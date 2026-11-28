"""Seeded random number generation so every run is reproducible."""

import random


def make_rng(seed: int, stream: str = "") -> random.Random:
    """Return an independent generator for (seed, stream).

    Separate streams (for example "algorithm" and "adversary") keep the
    adversary's trigger sequence identical when only the algorithm changes.
    String seeding is hash-randomization safe, so results repeat across processes.
    """
    return random.Random(f"{seed}:{stream}")
