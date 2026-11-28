"""Per-algorithm behaviour: round accounting, message structure and API constraints."""

import pytest

from dtc.adversary import make_adversary
from dtc.algorithms.registry import ALGORITHMS, get_algorithm
from dtc.core.metrics import Metrics
from dtc.core.network import Network
from dtc.core.rng import make_rng


def build(name, n, w, seed=0):
    network = Network(n, Metrics(n))
    algo = get_algorithm(name)(n, w, make_rng(seed, "algorithm"))
    algo.setup(network)
    return algo, network


def test_all_algorithms_registered():
    assert set(ALGORITHMS) >= {"centralized", "layered_rand", "coin_rand", "ring_rand"}
    assert not ALGORITHMS["ring_rand"].exact
    assert all(ALGORITHMS[a].exact for a in ("centralized", "layered_rand", "coin_rand"))


@pytest.mark.parametrize("name", ["layered_rand", "coin_rand"])
@pytest.mark.parametrize("n", [15, 16, 33])
@pytest.mark.parametrize("adversary", ["uniform", "few_nodes"])
def test_round_accounting_invariant(name, n, adversary):
    # Every trigger of the current round is held in exactly one counter or coin, so
    # w' = Csum + tau * Ncoins equals the triggers received since the round began.
    w = n * n
    algo, network = build(name, n, w)
    adv = make_adversary(adversary, n, w, make_rng(0, "adversary"))
    root = network.processors[0]
    for delivered in range(1, w + 1):
        network.processors[adv.next_node()].on_trigger()
        network.deliver_all()
        if algo.alert_fired:
            assert delivered == w
            return
        in_system = sum(p.local_count() for p in network.processors)
        assert in_system == delivered - (w - root.w_hat)
        assert 0 <= in_system < root.w_hat
    pytest.fail("alert never fired")


@pytest.mark.parametrize("name", ["layered_rand", "coin_rand"])
def test_end_of_round_costs_three_messages_per_non_root_processor(name):
    n = 15
    algo, network = build(name, n, 10_000)
    adv = make_adversary("uniform", n, 10_000, make_rng(0, "adversary"))
    while algo.network.metrics.rounds < 2:
        network.processors[adv.next_node()].on_trigger()
        network.deliver_all()
    by_kind = network.metrics.by_kind
    assert by_kind["eor_begin"] == by_kind["eor_reduce"] == by_kind["eor_inform"] == n - 1


def test_centralized_master_receives_most_messages():
    algo, network = build("centralized", 16, 256)
    adv = make_adversary("uniform", 16, 256, make_rng(0, "adversary"))
    while not algo.alert_fired:
        network.processors[adv.next_node()].on_trigger()
        network.deliver_all()
    m = network.metrics
    assert m.received[0] == m.max_rcv_load
    assert m.received[0] > m.total_msgs / 3


def test_ring_collection_uses_one_message_per_processor():
    from dtc.algorithms.ring_rand import RingRand

    class Always:
        def should_start(self, pid, w_hat, round):
            return True

    n, w = 8, 64
    network = Network(n, Metrics(n))
    algo = RingRand(n, w, make_rng(0), collection_policy=Always())
    algo.setup(network)
    network.processors[3].on_trigger()  # w_hat = 64, total = 1 < 32: collection only
    network.deliver_all()
    assert network.metrics.by_kind == {"collect": n}
    assert not algo.alert_fired


def test_coin_rand_requires_two_processors():
    with pytest.raises(ValueError):
        get_algorithm("coin_rand")(1, 10, make_rng(0))


@pytest.mark.parametrize("name", ["centralized", "layered_rand", "ring_rand"])
def test_single_processor_system(name):
    algo, network = build(name, 1, 20)
    for i in range(20):
        network.processors[0].on_trigger()
        network.deliver_all()
        assert algo.alert_fired == (i == 19)
    assert network.metrics.total_msgs == 0
