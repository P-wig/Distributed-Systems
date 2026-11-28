"""Abstract Algorithm interface shared by all algorithms and derandomized variants."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import ClassVar

from dtc.core.network import Network
from dtc.core.processor import Processor


class Algorithm(ABC):
    """One DTC algorithm instance for a single trial.

    Subclasses build one `Processor` per node in `create_processors` and call
    `raise_alert()` when they determine that `w` triggers have been received.
    """

    name: ClassVar[str]
    exact: ClassVar[bool] = True

    def __init__(self, n: int, w: int, rng: random.Random) -> None:
        self.n = n
        self.w = w
        self.rng = rng
        self.alert_fired = False
        self.network: Network | None = None

    def setup(self, network: Network) -> None:
        self.network = network
        network.attach(self.create_processors(network))

    @abstractmethod
    def create_processors(self, network: Network) -> list[Processor]:
        """Return `n` processors with pids 0..n-1."""

    def raise_alert(self) -> None:
        self.alert_fired = True

    def start_round(self) -> None:
        """Record that a new round began (call once per round, including the first)."""
        assert self.network is not None
        self.network.metrics.rounds += 1
