"""RingRand, the paper's ST-Rand (paper Section 5)."""

from __future__ import annotations

import random
from typing import ClassVar

from dtc.algorithms.base import Algorithm
from dtc.algorithms.layout import ring_right
from dtc.algorithms.registry import register
from dtc.core.network import Message, Network
from dtc.core.processor import Processor
from dtc.derand.collection_policy import CollectionPolicy, RandomCollection


class RingProcessor(Processor):
    def __init__(self, pid: int, network: Network, algo: RingRand) -> None:
        super().__init__(pid, network)
        self.algo = algo
        self.policy = algo.collection_policy
        self.right = ring_right(pid, algo.n)
        self.round = 1
        self.w_hat = algo.w
        self.c = 0

    def on_trigger(self) -> None:
        self.c += 1
        if self.policy.should_start(self.pid, self.w_hat, self.round):
            self._collect()

    def on_message(self, msg: Message) -> None:
        if msg.kind == "collect":
            initiator, total = msg.data
            if initiator == self.pid:
                self._collected(total)
            else:
                self.send(self.right, "collect", self.round, (initiator, total + self.c))
        elif msg.kind == "new_round":
            initiator, w_hat = msg.data
            self._enter_round(w_hat, msg.round)
            if self.right != initiator:
                self.send(self.right, "new_round", self.round, msg.data)

    def _collect(self) -> None:
        """Sum-reduce C(x) around the ring; the total returns to this processor."""
        if self.algo.n == 1:
            self._collected(self.c)
        else:
            self.send(self.right, "collect", self.round, (self.pid, self.c))

    def _collected(self, total: int) -> None:
        if total < -(-self.w_hat // 2):
            return
        new_w_hat = self.w_hat - total
        if new_w_hat <= 0:
            self.algo.raise_alert()
            return
        self.algo.start_round()
        self._enter_round(new_w_hat, self.round + 1)
        if self.algo.n > 1:
            self.send(self.right, "new_round", self.round, (self.pid, new_w_hat))

    def _enter_round(self, w_hat: int, round: int) -> None:
        self.w_hat = w_hat
        self.round = round
        self.c = 0


@register
class RingRand(Algorithm):
    name = "ring_rand"
    exact: ClassVar[bool] = False

    def __init__(
        self, n: int, w: int, rng: random.Random, collection_policy: CollectionPolicy | None = None
    ) -> None:
        super().__init__(n, w, rng)
        self.collection_policy = collection_policy or RandomCollection(n, rng)

    def create_processors(self, network: Network) -> list[Processor]:
        self.start_round()
        return [RingProcessor(i, network, self) for i in range(self.n)]
