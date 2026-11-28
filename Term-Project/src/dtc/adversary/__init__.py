"""Adversaries decide which processor receives each trigger."""

import random

from dtc.adversary.base import Adversary
from dtc.adversary.oblivious import OBLIVIOUS


def make_adversary(name: str, n: int, w: int, rng: random.Random) -> Adversary:
    try:
        cls = OBLIVIOUS[name]
    except KeyError:
        raise KeyError(f"unknown adversary {name!r}; available: {sorted(OBLIVIOUS)}") from None
    return cls(n, w, rng)
