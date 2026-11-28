"""Fixed trigger distributions: uniform, single node, few nodes, bursty, permutation."""

import random

from dtc.adversary.base import Adversary

FEW_NODES = 4


class Uniform(Adversary):
    def next_node(self) -> int:
        return self.rng.randrange(self.n)


class SingleNode(Adversary):
    """Every trigger goes to one processor, chosen at random up front."""

    def __init__(self, n: int, w: int, rng: random.Random) -> None:
        super().__init__(n, w, rng)
        self.target = rng.randrange(n)

    def next_node(self) -> int:
        return self.target


class FewNodes(Adversary):
    """Triggers are spread uniformly over a small random set of processors."""

    def __init__(self, n: int, w: int, rng: random.Random) -> None:
        super().__init__(n, w, rng)
        self.targets = rng.sample(range(n), min(FEW_NODES, n))

    def next_node(self) -> int:
        return self.rng.choice(self.targets)


class Bursty(Adversary):
    """Runs of w/n consecutive triggers to a random processor."""

    def __init__(self, n: int, w: int, rng: random.Random) -> None:
        super().__init__(n, w, rng)
        self.burst_len = max(1, w // n)
        self._remaining = 0
        self._current = 0

    def next_node(self) -> int:
        if self._remaining == 0:
            self._current = self.rng.randrange(self.n)
            self._remaining = self.burst_len
        self._remaining -= 1
        return self._current


class Permutation(Adversary):
    """Cycles through all processors in a fresh random order on every pass."""

    def __init__(self, n: int, w: int, rng: random.Random) -> None:
        super().__init__(n, w, rng)
        self._order: list[int] = []
        self._pos = 0

    def next_node(self) -> int:
        if self._pos == len(self._order):
            self._order = list(range(self.n))
            self.rng.shuffle(self._order)
            self._pos = 0
        node = self._order[self._pos]
        self._pos += 1
        return node


OBLIVIOUS: dict[str, type[Adversary]] = {
    "uniform": Uniform,
    "single_node": SingleNode,
    "few_nodes": FewNodes,
    "bursty": Bursty,
    "permutation": Permutation,
}
