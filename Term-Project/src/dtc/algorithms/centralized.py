"""Deterministic master-based baseline (paper Section 2)."""

from __future__ import annotations

from dtc.algorithms.base import Algorithm
from dtc.algorithms.registry import register
from dtc.core.network import Message, Network
from dtc.core.processor import Processor

MASTER = 0


def batch_size(w_hat: int, n: int) -> int:
    """B = w_hat / (2n), and 1 once w_hat < 2n."""
    return max(1, w_hat // (2 * n))


class CentralizedProcessor(Processor):
    def __init__(self, pid: int, network: Network, algo: Centralized) -> None:
        super().__init__(pid, network)
        self.algo = algo
        self.round = 1
        self.w_hat = algo.w
        self.batch = batch_size(self.w_hat, algo.n)
        self.local = 0  # triggers not yet reported to the master
        self.count = 0  # master only: triggers reported (or received) this round
        self.ending = False
        self._pending = 0
        self._acc = 0

    def on_trigger(self) -> None:
        if self.pid == MASTER:
            self.count += 1
            self._check_round_end()
            return
        self.local += 1
        if self.local >= self.batch:
            self.local -= self.batch
            self.send(MASTER, "report", self.round, self.batch)

    def on_message(self, msg: Message) -> None:
        if msg.kind == "report":
            self.count += msg.data
            self._check_round_end()
        elif msg.kind == "eor_begin":
            self.send(MASTER, "eor_reply", self.round, self.local)
            self.local = 0
        elif msg.kind == "eor_reply":
            self._acc += msg.data
            self._pending -= 1
            if self._pending == 0:
                self._finish_round()
        elif msg.kind == "new_round":
            self._enter_round(msg.data)

    def _check_round_end(self) -> None:
        if self.ending or self.count < -(-self.w_hat // 2):
            return
        self.ending = True
        self._acc = self.count
        self._pending = self.algo.n - 1
        for pid in range(self.algo.n):
            if pid != MASTER:
                self.send(pid, "eor_begin", self.round)
        if self._pending == 0:
            self._finish_round()

    def _finish_round(self) -> None:
        new_w_hat = self.w_hat - self._acc
        if new_w_hat <= 0:
            self.algo.raise_alert()
            return
        self.algo.start_round()
        self._enter_round(new_w_hat)
        for pid in range(self.algo.n):
            if pid != MASTER:
                self.send(pid, "new_round", self.round, new_w_hat)

    def _enter_round(self, w_hat: int) -> None:
        self.round += 1
        self.w_hat = w_hat
        self.batch = batch_size(w_hat, self.algo.n)
        self.local = 0
        self.count = 0
        self.ending = False


@register
class Centralized(Algorithm):
    name = "centralized"

    def create_processors(self, network: Network) -> list[Processor]:
        self.start_round()
        return [CentralizedProcessor(i, network, self) for i in range(self.n)]
