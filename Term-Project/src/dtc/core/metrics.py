"""Message complexity, MaxRcvLoad, MaxMsgLoad and rounds for one simulation run."""

from collections import Counter


class Metrics:
    """Per-processor send/receive counts plus the derived paper metrics."""

    def __init__(self, n: int) -> None:
        self.n = n
        self.sent = [0] * n
        self.received = [0] * n
        self.by_kind: Counter[str] = Counter()
        self.rounds = 0

    def record_message(self, src: int, dst: int, kind: str) -> None:
        self.sent[src] += 1
        self.received[dst] += 1
        self.by_kind[kind] += 1

    @property
    def total_msgs(self) -> int:
        """Message complexity: all messages sent by all processors."""
        return sum(self.sent)

    @property
    def max_rcv_load(self) -> int:
        """MaxRcvLoad: most messages received by any one processor."""
        return max(self.received)

    @property
    def max_msg_load(self) -> int:
        """MaxMsgLoad: most messages sent plus received by any one processor."""
        return max(s + r for s, r in zip(self.sent, self.received))
