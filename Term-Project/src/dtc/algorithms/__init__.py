"""The DTC algorithms from the paper, behind one common interface."""

# Importing the modules registers each algorithm by name.
from dtc.algorithms import centralized, coin_rand, layered_rand, ring_rand  # noqa: F401
