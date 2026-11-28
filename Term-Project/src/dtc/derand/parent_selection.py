"""Pluggable parent-selection strategies: random now; round-robin, hashed, staggered, load-feedback later."""

import random
from typing import Protocol


class ParentSelector(Protocol):
    def select(self, sender: int, layer: int, size: int, round: int) -> int:
        """Pick which of the `size` processors in `layer` receives a coin; return an index in [0, size)."""
        ...


class RandomParent:
    """The paper's choice: uniformly at random."""

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def select(self, sender: int, layer: int, size: int, round: int) -> int:
        return self.rng.randrange(size)
