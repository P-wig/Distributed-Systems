"""End-to-end trial pipeline test using a toy algorithm (every trigger is reported to node 0)."""

import pytest

from dtc.algorithms import registry
from dtc.algorithms.base import Algorithm
from dtc.core.processor import Processor
from dtc.experiments.config import TrialSpec
from dtc.experiments.run import run_trial


class ToyProcessor(Processor):
    def __init__(self, pid, network, algo):
        super().__init__(pid, network)
        self.algo = algo
        self.count = 0

    def on_trigger(self):
        self.send(0, "report")

    def on_message(self, msg):
        self.count += 1
        if self.count == self.algo.w:
            self.algo.raise_alert()


class ToyAlgorithm(Algorithm):
    name = "toy"

    def create_processors(self, network):
        self.start_round()
        return [ToyProcessor(i, network, self) for i in range(self.n)]


@pytest.fixture(autouse=True)
def toy_registered():
    registry.register(ToyAlgorithm)
    yield
    registry.ALGORITHMS.pop("toy")


@pytest.mark.parametrize("adversary", ["uniform", "single_node", "few_nodes", "bursty", "permutation"])
@pytest.mark.parametrize("seed", range(3))
def test_alert_fires_at_exactly_w(adversary, seed):
    r = run_trial(TrialSpec("toy", 8, 64, adversary, seed))
    assert r.alert_fired
    assert r.triggers_at_alert == 64
    assert r.rounds == 1
    assert r.max_rcv_load == r.total_msgs  # node 0 receives every counted message


def test_trial_is_reproducible():
    spec = TrialSpec("toy", 8, 64, "uniform", 5)
    assert run_trial(spec) == run_trial(spec)


def test_no_alert_reported_when_algorithm_never_fires():
    class Silent(ToyAlgorithm):
        name = "silent"

        def raise_alert(self):
            pass

    registry.register(Silent)
    try:
        r = run_trial(TrialSpec("silent", 4, 16, "uniform", 0))
    finally:
        registry.ALGORITHMS.pop("silent")
    assert not r.alert_fired
    assert r.triggers_at_alert == 16


def test_unknown_algorithm_and_variant():
    with pytest.raises(KeyError):
        run_trial(TrialSpec("nope", 4, 16, "uniform", 0))
    with pytest.raises(NotImplementedError):
        run_trial(TrialSpec("toy", 4, 16, "uniform", 0, variant="hashed"))
