"""LayeredRand (paper Section 3)."""

from __future__ import annotations

import random

from dtc.algorithms.base import Algorithm
from dtc.algorithms.layout import heap_layer, layer_size, layer_start, num_layers
from dtc.algorithms.registry import register
from dtc.algorithms.tree_round import TreeRoundProcessor
from dtc.core.network import Message, Network
from dtc.core.processor import Processor
from dtc.derand.parent_selection import ParentSelector, RandomParent


def layered_threshold(w_hat: int, layer: int, n: int) -> int:
    """tau(l) = ceil(w_hat / (4 * 2^l * log2(n+1))), with log2(n+1) replaced by the layer count."""
    return -(-w_hat // (4 * (1 << layer) * num_layers(n)))


class LayeredProcessor(TreeRoundProcessor):
    def __init__(self, pid: int, network: Network, algo: LayeredRand) -> None:
        super().__init__(pid, network, algo)
        self.selector = algo.parent_selector
        self.layer = heap_layer(pid)
        self.c = 0
        self.tau = 0
        self.root_limit = 0
        self.reset_round()

    def local_count(self) -> int:
        return self.c

    def reset_round(self) -> None:
        self.c = 0
        if self.layer == 0:
            self.root_limit = -(-self.w_hat // 2)
        else:
            self.tau = layered_threshold(self.w_hat, self.layer, self.algo.n)

    def on_trigger(self) -> None:
        self.c += 1
        self._settle()

    def on_message(self, msg: Message) -> None:
        if msg.kind == "coin":
            if msg.round != self.round or self.ending:
                return
            self.c += msg.data
            self._settle()
        else:
            self.handle_end_of_round(msg)

    def _settle(self) -> None:
        if self.layer == 0:
            if self.c >= self.root_limit and not self.ending:
                self.begin_end_of_round()
        elif self.c >= self.tau:
            up = self.layer - 1
            index = self.selector.select(self.pid, up, layer_size(up), self.round)
            self.c -= self.tau
            self.send(layer_start(up) + index, "coin", self.round, self.tau)


@register
class LayeredRand(Algorithm):
    name = "layered_rand"

    def __init__(
        self, n: int, w: int, rng: random.Random, parent_selector: ParentSelector | None = None
    ) -> None:
        super().__init__(n, w, rng)
        self.parent_selector = parent_selector or RandomParent(rng)

    def create_processors(self, network: Network) -> list[Processor]:
        self.start_round()
        return [LayeredProcessor(i, network, self) for i in range(self.n)]
