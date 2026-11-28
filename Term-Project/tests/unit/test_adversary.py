"""Adversary and RNG tests."""

from collections import Counter

import pytest

from dtc.adversary import make_adversary
from dtc.adversary.oblivious import OBLIVIOUS
from dtc.core.rng import make_rng


def draw(name, n, w, seed=0, count=None):
    adv = make_adversary(name, n, w, make_rng(seed, "adversary"))
    return [adv.next_node() for _ in range(count if count is not None else w)]


@pytest.mark.parametrize("name", sorted(OBLIVIOUS))
def test_nodes_in_range_and_reproducible(name):
    a = draw(name, 16, 500)
    assert all(0 <= x < 16 for x in a)
    assert a == draw(name, 16, 500)


def test_different_seeds_differ():
    assert draw("uniform", 16, 200, seed=1) != draw("uniform", 16, 200, seed=2)


def test_streams_are_independent():
    assert make_rng(0, "algorithm").random() != make_rng(0, "adversary").random()


def test_single_node_hits_one_processor():
    assert len(set(draw("single_node", 16, 300))) == 1


def test_few_nodes_hits_at_most_four():
    assert 1 < len(set(draw("few_nodes", 16, 400))) <= 4


def test_bursty_runs_have_burst_length():
    n, w = 8, 640  # burst length 80
    nodes = draw("bursty", n, w)
    assert all(len(set(nodes[i : i + 80])) == 1 for i in range(0, w, 80))


def test_permutation_is_balanced_per_pass():
    n = 16
    nodes = draw("permutation", n, 5 * n)
    for i in range(0, 5 * n, n):
        assert Counter(nodes[i : i + n]) == Counter(range(n))


def test_unknown_adversary_raises():
    with pytest.raises(KeyError):
        make_adversary("nope", 4, 16, make_rng(0))
