"""Adversary interface: decides which processor receives each trigger."""

import random
from abc import ABC, abstractmethod


class Adversary(ABC):
    def __init__(self, n: int, w: int, rng: random.Random) -> None:
        self.n = n
        self.w = w
        self.rng = rng

    @abstractmethod
    def next_node(self) -> int:
        """Return the processor that receives the next trigger."""
