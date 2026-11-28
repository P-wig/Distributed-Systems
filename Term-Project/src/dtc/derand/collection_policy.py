"""When RingRand starts a Collection: the paper's random rule now; deterministic replacements later."""

import math
import random
from typing import Protocol


class CollectionPolicy(Protocol):
    def should_start(self, pid: int, w_hat: int, round: int) -> bool:
        """Called after processor `pid` receives a trigger."""
        ...


class RandomCollection:
    """The paper's rule: start a Collection with probability 8 log2(n) / w_hat."""

    def __init__(self, n: int, rng: random.Random) -> None:
        self.rng = rng
        self.numerator = 8 * math.log2(max(n, 2))

    def should_start(self, pid: int, w_hat: int, round: int) -> bool:
        return self.rng.random() < self.numerator / w_hat
