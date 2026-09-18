// after compiling run java BookServer input_file.txt, remember to ctrl+c to stop the server
import java.io.*;
import java.net.*;
import java.util.*;

public class BookServer {
    public static void main(String[] args) {
        int tcpPort;
        int udpPort;
        if (args.length != 1) {
            System.out.println("ERROR: Provide 1 argument: input file containing initial inventory");
            System.exit(-1);
        }
        String fileName = args[0];
        tcpPort = 7000;
        udpPort = 8000;

        // parse the inventory file
        try (DatagramSocket udpSocket = new DatagramSocket(udpPort);
                ServerSocket tcpSocket = new ServerSocket(tcpPort)) {
            final Library library = new Library(fileName);

            // DONE: handle request from clients
            Thread udpThread = new Thread(new Runnable() {
                public void run() {
                    udpLoop(library, udpSocket);
                }
            });
            Thread tcpThread = new Thread(new Runnable() {
                public void run() {
                    tcpLoop(library, tcpSocket);
                }
            });
            udpThread.start();
            tcpThread.start();

            // Both loops run forever; joining keeps the sockets open for the server's lifetime.
            tcpThread.join();
            udpThread.join();
        } catch (IOException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    // TCP server loop: accepts incoming connections and spawns a new thread for each client.
    private static void tcpLoop(final Library library, ServerSocket socket) {
        while (true) {
            try {
                final Socket client = socket.accept();
                new Thread(new Runnable() {
                    public void run() {
                        handleTcpClient(library, client);
                    }
                }).start();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    /** One thread per connected TCP client. */
    private static void handleTcpClient(Library library, Socket socket) {
        try (Socket client = socket;
                BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
                PrintWriter out = new PrintWriter(client.getOutputStream(), true)) {
            String cmd;
            while ((cmd = in.readLine()) != null) {
                if (cmd.trim().equals("exit")) {
                    library.writeInventoryFile();
                    break;
                }
                out.println(library.process(cmd));
                out.println(); // blank line marks the end of the response
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // UDP server loop: receives incoming datagrams and spawns a new thread for each request.
    private static void udpLoop(final Library library, final DatagramSocket socket) {
        while (true) {
            try {
                // A fresh buffer per packet: a reused one would be overwritten while a worker reads it.
                byte[] buf = new byte[65507];
                DatagramPacket request = new DatagramPacket(buf, buf.length);
                socket.receive(request);

                final String cmd = new String(request.getData(), 0, request.getLength());
                final InetAddress clientAddress = request.getAddress();
                final int clientPort = request.getPort();

                new Thread(new Runnable() {
                    public void run() {
                        handleUdpRequest(library, socket, cmd, clientAddress, clientPort);
                    }
                }).start();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    /** One thread per datagram; UDP has no connection, so each request stands alone. */
    private static void handleUdpRequest(Library library, DatagramSocket socket, String cmd,
            InetAddress clientAddress, int clientPort) {
        try {
            if (cmd.trim().equals("exit")) {
                library.writeInventoryFile();
                return;
            }
            byte[] reply = library.process(cmd).getBytes();
            socket.send(new DatagramPacket(reply, reply.length, clientAddress, clientPort));
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static class Loan {
        private final String user;
        private final String book;

        Loan(String user, String book) {
            this.user = user;
            this.book = book;
        }
    }

    /** Shared state for every client; all mutating methods are synchronized on this instance. */
    private static class Library {
        // Book names are kept with their surrounding quotes so they match commands and output verbatim.
        private final Map<String, Integer> inventory = new LinkedHashMap<String, Integer>();
        private final Map<Integer, Loan> loans = new LinkedHashMap<Integer, Loan>();
        private int nextLoanId = 1;

        Library(String fileName) throws IOException {
            Scanner sc = new Scanner(new FileReader(fileName));
            while (sc.hasNextLine()) {
                String line = sc.nextLine().trim();
                if (line.isEmpty()) {
                    continue;
                }
                int split = line.lastIndexOf(' ');
                inventory.put(line.substring(0, split).trim(),
                        Integer.parseInt(line.substring(split + 1).trim()));
            }
            sc.close();
        }

        synchronized String process(String cmd) {
            String[] tokens = cmd.trim().split(" ");
            if (tokens[0].equals("set-mode")) {
                return "The communication mode is set to" + (tokens.length > 1 && tokens[1].equals("t") ? " TCP" : " UDP");
            } else if (tokens[0].equals("begin-loan")) {
                return beginLoan(cmd.trim());
            } else if (tokens[0].equals("end-loan")) {
                return endLoan(tokens.length > 1 ? tokens[1] : "");
            } else if (tokens[0].equals("get-loans")) {
                return getLoans(tokens.length > 1 ? tokens[1] : "");
            } else if (tokens[0].equals("get-inventory")) {
                return inventoryText();
            }
            return "ERROR: No such command";
        }

        private String beginLoan(String cmd) {
            String rest = cmd.substring("begin-loan".length()).trim();
            int space = rest.indexOf(' ');
            if (space < 0) {
                return "ERROR: No such command";
            }
            String user = rest.substring(0, space);
            String book = rest.substring(space + 1).trim();

            Integer available = inventory.get(book);
            if (available == null) {
                return "Request Failed - We do not have this book";
            }
            if (available.intValue() == 0) {
                return "Request Failed - Book not available";
            }
            inventory.put(book, available - 1);
            int loanId = nextLoanId++;
            loans.put(loanId, new Loan(user, book));
            return "Your request has been approved, " + loanId + " " + user + " " + book;
        }

        private String endLoan(String loanId) {
            Loan loan = null;
            try {
                loan = loans.remove(Integer.parseInt(loanId));
            } catch (NumberFormatException e) {
                loan = null;
            }
            if (loan == null) {
                return loanId + " not found, no such borrow record";
            }
            inventory.put(loan.book, inventory.get(loan.book) + 1);
            return loanId + " is returned";
        }

        private String getLoans(String user) {
            StringBuilder sb = new StringBuilder();
            for (Map.Entry<Integer, Loan> entry : loans.entrySet()) {
                if (entry.getValue().user.equals(user)) {
                    if (sb.length() > 0) {
                        sb.append("\n");
                    }
                    sb.append(entry.getKey()).append(" ").append(entry.getValue().book);
                }
            }
            return sb.length() == 0 ? "No record found for " + user : sb.toString();
        }

        private String inventoryText() {
            StringBuilder sb = new StringBuilder();
            for (Map.Entry<String, Integer> entry : inventory.entrySet()) {
                if (sb.length() > 0) {
                    sb.append("\n");
                }
                sb.append(entry.getKey()).append(" ").append(entry.getValue());
            }
            return sb.toString();
        }

        synchronized void writeInventoryFile() throws IOException {
            PrintWriter out = new PrintWriter("inventory.txt");
            for (Map.Entry<String, Integer> entry : inventory.entrySet()) {
                out.println(entry.getKey() + " " + entry.getValue());
            }
            out.close();
        }
    }
}
