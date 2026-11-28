"""CoinRand, including the phase 2 boundary case (paper Section 4)."""

from __future__ import annotations

import random

from dtc.algorithms.base import Algorithm
from dtc.algorithms.layout import (
    coin_internal_layers,
    heap_layer,
    layer_size,
    layer_start,
)
from dtc.algorithms.registry import register
from dtc.algorithms.tree_round import TreeRoundProcessor
from dtc.core.network import Message, Network
from dtc.core.processor import Processor
from dtc.derand.parent_selection import ParentSelector, RandomParent


def coin_round_params(w_hat: int, n: int) -> tuple[int, int]:
    """Return (threshold tau, number of internal layers) for a round with initial value w_hat.

    Phase 1 (w_hat >= n): tau = ceil(w_hat / 4n) and all L internal layers.
    Phase 2 (w_hat < n): tau = 1 and floor(log2 w_hat) internal layers (at least 1), so the
    coins the internal layers can hold, 2^I - 2, stay below w_hat and the round cannot stall.
    """
    if w_hat >= n:
        return -(-w_hat // (4 * n)), coin_internal_layers(n)
    return 1, max(1, w_hat.bit_length() - 1)


class CoinProcessor(TreeRoundProcessor):
    def __init__(self, pid: int, network: Network, algo: CoinRand) -> None:
        super().__init__(pid, network, algo)
        self.selector = algo.parent_selector
        internal = pid < layer_start(coin_internal_layers(algo.n))
        self.internal_layer = heap_layer(pid) if internal else None
        self.c = 0
        self.has_coin = False
        self.tau = 1
        self.layers = 1
        self.reset_round()

    def local_count(self) -> int:
        return self.c + self.tau * self.has_coin

    def reset_round(self) -> None:
        self.c = 0
        self.has_coin = False
        self.tau, self.layers = coin_round_params(self.w_hat, self.algo.n)

    def on_trigger(self) -> None:
        self.c += 1
        if self.c >= self.tau:
            self.c = 0
            self._send_coin(self.layers - 1)

    def on_message(self, msg: Message) -> None:
        if msg.kind != "coin":
            self.handle_end_of_round(msg)
            return
        if msg.round != self.round or self.ending:
            return
        layer = self.internal_layer
        if layer == 0:
            self.has_coin = True
            self.begin_end_of_round()
        elif not self.has_coin:
            self.has_coin = True
        else:
            self._send_coin(layer - 1)

    def _send_coin(self, target_layer: int) -> None:
        index = self.selector.select(self.pid, target_layer, layer_size(target_layer), self.round)
        self.send(layer_start(target_layer) + index, "coin", self.round)


@register
class CoinRand(Algorithm):
    name = "coin_rand"

    def __init__(
        self, n: int, w: int, rng: random.Random, parent_selector: ParentSelector | None = None
    ) -> None:
        if n < 2:
            raise ValueError("CoinRand needs n >= 2")
        super().__init__(n, w, rng)
        self.parent_selector = parent_selector or RandomParent(rng)

    def create_processors(self, network: Network) -> list[Processor]:
        self.start_round()
        return [CoinProcessor(i, network, self) for i in range(self.n)]
