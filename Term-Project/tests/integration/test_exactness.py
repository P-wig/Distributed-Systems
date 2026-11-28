"""The alert fires after exactly w triggers for every exact algorithm, over many seeds."""

import pytest

from dtc.experiments.config import TrialSpec
from dtc.experiments.run import run_trial

ADVERSARIES = ["uniform", "single_node", "few_nodes", "bursty", "permutation"]


def sizes(n):
    return sorted({1, 2, 5, n - 1, n, n + 1, 4 * n, n * n} - {0})


@pytest.mark.parametrize("algorithm", ["centralized", "layered_rand", "coin_rand"])
@pytest.mark.parametrize("n", [2, 3, 7, 15, 16, 17, 31, 64])
@pytest.mark.parametrize("adversary", ADVERSARIES)
def test_exact_algorithms_alert_at_exactly_w(algorithm, n, adversary):
    for w in sizes(n):
        for seed in range(2):
            r = run_trial(TrialSpec(algorithm, n, w, adversary, seed))
            assert r.alert_fired, (algorithm, n, w, adversary, seed)
            assert r.triggers_at_alert == w, (algorithm, n, w, adversary, seed)


@pytest.mark.parametrize("algorithm", ["centralized", "layered_rand"])
def test_n_equals_one(algorithm):
    r = run_trial(TrialSpec(algorithm, 1, 30, "uniform", 0))
    assert r.alert_fired and r.triggers_at_alert == 30


@pytest.mark.parametrize("algorithm", ["centralized", "layered_rand", "coin_rand", "ring_rand"])
def test_rounds_are_logarithmic_in_w(algorithm):
    n = 16
    r = run_trial(TrialSpec(algorithm, n, n * n, "uniform", 0))
    assert r.alert_fired
    assert r.rounds <= 3 * (n * n).bit_length()
