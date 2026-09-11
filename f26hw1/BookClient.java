// run java BookClient command-file clientId ex. java BookClient command_file1.txt 1
import java.util.Scanner;
import java.io.*;
import java.net.*;

public class BookClient {
    public static void main(String[] args) {
        String hostAddress;
        int tcpPort;
        int udpPort;
        int clientId;

        if (args.length != 2) {
            System.out.println("ERROR: Provide 2 arguments: command-file, clientId");
            System.out.println("\t(1) command-file: file with commands to the server");
            System.out.println("\t(2) clientId: an integer between 1..9");
            System.exit(-1);
        }

        String commandFile = args[0];
        clientId = Integer.parseInt(args[1]);
        hostAddress = "localhost";
        tcpPort = 7000;// hardcoded -- must match the server's tcp port
        udpPort = 8000;// hardcoded -- must match the server's udp port

        try (Connection conn = new Connection(hostAddress, tcpPort, udpPort);
                Scanner sc = new Scanner(new FileReader(commandFile));
                PrintWriter out = new PrintWriter("out_" + clientId + ".txt")) {

            while (sc.hasNextLine()) {
                String cmd = sc.nextLine();
                String[] tokens = cmd.split(" ");

                if (tokens[0].equals("set-mode")) {
                    // DONE: set the mode of communication for sending commands to the server
                    if (tokens.length != 2 || !(tokens[1].equals("t") || tokens[1].equals("u"))) {
                        System.out.println("ERROR: No such command");
                    } else {
                        conn.setMode(tokens[1]);
                        writeResponse(out, conn.send(cmd));
                    }
                } else if (tokens[0].equals("begin-loan")) {
                    // DONE: send appropriate command to the server and display the
                    // appropriate responses form the server
                    writeResponse(out, conn.send(cmd));
                } else if (tokens[0].equals("end-loan")) {
                    // DONE: send appropriate command to the server and display the
                    // appropriate responses from the server
                    writeResponse(out, conn.send(cmd));
                } else if (tokens[0].equals("get-loans")) {
                    // DONE: send appropriate command to the server and display the
                    // appropriate responses from the server
                    writeResponse(out, conn.send(cmd));
                } else if (tokens[0].equals("get-inventory")) {
                    // DONE: send appropriate command to the server and display the
                    // appropriate responses from the server
                    writeResponse(out, conn.send(cmd));
                } else if (tokens[0].equals("exit")) {
                    // DONE: send appropriate command to the server
                    conn.sendNoReply(cmd);
                    break;
                } else {
                    System.out.println("ERROR: No such command");
                }
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    /** Writes each line separately so a multi-line reply uses one line separator throughout. */
    private static void writeResponse(PrintWriter out, String response) {
        for (String line : response.split("\n")) {
            out.println(line);
        }
    }

    /** Holds the client's socket state so it survives across commands in the loop. */
    private static class Connection implements Closeable {
        private String mode = "u"; // default mode of communication is UDP
        private final InetAddress serverAddress;
        private final int tcpPort;
        private final int udpPort;
        private final DatagramSocket udpSocket;
        private Socket tcpSocket = null;
        private PrintWriter tcpOut = null;
        private BufferedReader tcpIn = null;

        Connection(String hostAddress, int tcpPort, int udpPort) throws IOException {
            this.serverAddress = InetAddress.getByName(hostAddress);
            this.tcpPort = tcpPort;
            this.udpPort = udpPort;
            this.udpSocket = new DatagramSocket();
        }

        void setMode(String newMode) throws IOException {
            mode = newMode;
            if (mode.equals("t")) {
                if (tcpSocket == null || tcpSocket.isClosed()) {
                    tcpSocket = new Socket(serverAddress, tcpPort);
                    tcpOut = new PrintWriter(tcpSocket.getOutputStream(), true);
                    tcpIn = new BufferedReader(new InputStreamReader(tcpSocket.getInputStream()));
                }
            } else if (tcpSocket != null && !tcpSocket.isClosed()) {
                tcpSocket.close();
                tcpSocket = null;
                tcpOut = null;
                tcpIn = null;
            }
        }

        /** Sends a command over the active protocol; a TCP reply ends at the server's blank-line sentinel. */
        String send(String cmd) throws IOException {
            if (mode.equals("t")) {
                tcpOut.println(cmd);
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = tcpIn.readLine()) != null && !line.isEmpty()) {
                    if (response.length() > 0) {
                        response.append("\n");
                    }
                    response.append(line);
                }
                return response.toString();
            }

            byte[] outBuf = cmd.getBytes();
            udpSocket.send(new DatagramPacket(outBuf, outBuf.length, serverAddress, udpPort));
            byte[] inBuf = new byte[65507];
            DatagramPacket reply = new DatagramPacket(inBuf, inBuf.length);
            udpSocket.receive(reply);
            return new String(reply.getData(), 0, reply.getLength());
        }

        /** Sends a command the server does not answer; waiting for a reply would block forever on UDP. */
        void sendNoReply(String cmd) throws IOException {
            if (mode.equals("t")) {
                tcpOut.println(cmd);
            } else {
                byte[] outBuf = cmd.getBytes();
                udpSocket.send(new DatagramPacket(outBuf, outBuf.length, serverAddress, udpPort));
            }
        }

        public void close() throws IOException {
            if (tcpSocket != null && !tcpSocket.isClosed()) {
                tcpSocket.close();
            }
            udpSocket.close();
        }
    }
}
