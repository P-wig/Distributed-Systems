"""Tree-based end-of-round procedure shared by LayeredRand and CoinRand (paper Sections 3.1 and 4.1).

The root broadcasts "begin" down the heap-ordered tree over all n processors, every processor
reduces its local count back up to the root, and the root broadcasts the new initial value
`w_hat` down. That is 3(n-1) messages per round, a constant number per processor.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from dtc.algorithms.layout import heap_children, heap_parent
from dtc.core.network import Message, Network
from dtc.core.processor import Processor

if TYPE_CHECKING:
    from dtc.algorithms.base import Algorithm


class TreeRoundProcessor(Processor):
    def __init__(self, pid: int, network: Network, algo: Algorithm) -> None:
        super().__init__(pid, network)
        self.algo = algo
        self.round = 1
        self.w_hat = algo.w
        self.ending = False
        self.children = heap_children(pid, algo.n)
        self.parent = heap_parent(pid) if pid > 0 else None
        self._pending = 0
        self._acc = 0

    @abstractmethod
    def local_count(self) -> int:
        """Triggers this processor accounts for in the current round (counter plus held coins)."""

    @abstractmethod
    def reset_round(self) -> None:
        """Reset counters and recompute thresholds for the new `self.w_hat` and `self.round`."""

    def begin_end_of_round(self) -> None:
        """Called by the root when it decides the round is over."""
        self._start_reduce()

    def handle_end_of_round(self, msg: Message) -> bool:
        """Process an end-of-round message; return False if `msg` is not one."""
        if msg.kind == "eor_begin":
            self._start_reduce()
        elif msg.kind == "eor_reduce":
            self._acc += msg.data
            self._pending -= 1
            if self._pending == 0:
                self._reduce_done()
        elif msg.kind == "eor_inform":
            self._enter_round(msg.data)
            for child in self.children:
                self.send(child, "eor_inform", self.round, msg.data)
        else:
            return False
        return True

    def _start_reduce(self) -> None:
        self.ending = True
        self._acc = self.local_count()
        self._pending = len(self.children)
        for child in self.children:
            self.send(child, "eor_begin", self.round)
        if self._pending == 0:
            self._reduce_done()

    def _reduce_done(self) -> None:
        if self.parent is not None:
            self.send(self.parent, "eor_reduce", self.round, self._acc)
            return
        new_w_hat = self.w_hat - self._acc
        if new_w_hat <= 0:
            self.algo.raise_alert()
            return
        self.algo.start_round()
        self._enter_round(new_w_hat)
        for child in self.children:
            self.send(child, "eor_inform", self.round, new_w_hat)

    def _enter_round(self, w_hat: int) -> None:
        self.round += 1
        self.w_hat = w_hat
        self.ending = False
        self.reset_round()
