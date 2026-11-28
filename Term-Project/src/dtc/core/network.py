"""Complete-graph network: any processor may message any other, and every message is counted."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from dtc.core.metrics import Metrics

if TYPE_CHECKING:
    from dtc.core.processor import Processor


@dataclass(slots=True)
class Message:
    src: int
    dst: int
    kind: str
    round: int = 0
    data: Any = None


class Network:
    """Fully connected network of `n` processors with ids 0..n-1.

    There is no adjacency structure: trees and rings used by the algorithms are
    overlays defined in `dtc.algorithms.layout`. All message accounting happens
    in `send`. A processor messaging itself is delivered but not counted, since
    no real message crosses the network (a processor can hold both a leaf and
    an internal role in CoinRand).
    """

    def __init__(self, n: int, metrics: Metrics | None = None) -> None:
        if n < 1:
            raise ValueError("n must be at least 1")
        self.n = n
        self.metrics = metrics if metrics is not None else Metrics(n)
        self.processors: list[Processor] = []
        self._queue: deque[Message] = deque()

    def attach(self, processors: list[Processor]) -> None:
        if len(processors) != self.n:
            raise ValueError(f"expected {self.n} processors, got {len(processors)}")
        for i, p in enumerate(processors):
            if p.pid != i:
                raise ValueError(f"processor at index {i} has pid {p.pid}")
        self.processors = processors

    def send(self, src: int, dst: int, kind: str, round: int = 0, data: Any = None) -> None:
        if not (0 <= src < self.n and 0 <= dst < self.n):
            raise ValueError(f"invalid endpoints {src} -> {dst} for n={self.n}")
        if src != dst:
            self.metrics.record_message(src, dst, kind)
        self._queue.append(Message(src, dst, kind, round, data))

    def deliver_all(self) -> int:
        """Deliver queued messages (FIFO) until none remain; return how many were delivered.

        This is the sequential model: one trigger is fully processed, including every
        message it causes, before the next trigger arrives.
        """
        delivered = 0
        while self._queue:
            msg = self._queue.popleft()
            self.processors[msg.dst].on_message(msg)
            delivered += 1
        return delivered
