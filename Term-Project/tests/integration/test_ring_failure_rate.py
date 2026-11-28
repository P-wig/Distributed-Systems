"""RingRand failure rate is negligible across many seeds."""

import pytest

from dtc.experiments.config import TrialSpec
from dtc.experiments.run import run_trial


@pytest.mark.parametrize("n", [8, 16])
@pytest.mark.parametrize("adversary", ["uniform", "single_node", "few_nodes"])
def test_ring_failure_rate_is_negligible(n, adversary):
    w = n * n
    results = [run_trial(TrialSpec("ring_rand", n, w, adversary, seed)) for seed in range(200)]
    # Collections sum exact counters, so an alert can never fire early; failure means no alert.
    assert all(r.triggers_at_alert == w for r in results if r.alert_fired)
    assert sum(not r.alert_fired for r in results) <= 2


def test_ring_fails_without_collections():
    from dtc.algorithms.ring_rand import RingRand
    from dtc.core.engine import run_simulation
    from dtc.core.metrics import Metrics
    from dtc.core.network import Network
    from dtc.adversary import make_adversary
    from dtc.core.rng import make_rng

    class Never:
        def should_start(self, pid, w_hat, round):
            return False

    n, w = 8, 64
    network = Network(n, Metrics(n))
    algo = RingRand(n, w, make_rng(0), collection_policy=Never())
    algo.setup(network)
    adv = make_adversary("uniform", n, w, make_rng(0, "adversary"))
    result = run_simulation(algo, network, adv, w)
    assert not result.alert_fired
    assert network.metrics.total_msgs == 0
