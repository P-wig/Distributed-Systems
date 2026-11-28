"""Layering and threshold tests for n = 2^L - 1 and n = 2^L."""

import pytest

from dtc.algorithms.coin_rand import coin_round_params
from dtc.algorithms.layered_rand import layered_threshold
from dtc.algorithms.layout import (
    coin_internal_layers,
    heap_children,
    heap_layer,
    heap_parent,
    layer_size,
    layer_start,
    num_layers,
    ring_right,
)


@pytest.mark.parametrize("n", range(1, 70))
def test_heap_tree_is_consistent(n):
    assert heap_layer(0) == 0
    for i in range(n):
        for c in heap_children(i, n):
            assert heap_parent(c) == i
            assert heap_layer(c) == heap_layer(i) + 1
        assert layer_start(heap_layer(i)) <= i < layer_start(heap_layer(i) + 1)
    assert heap_layer(n - 1) + 1 == num_layers(n)


@pytest.mark.parametrize("L", range(1, 8))
def test_paper_layering_for_full_trees(L):
    n = 2**L - 1  # LayeredRand: layers 0..L-1, layer l has 2^l processors
    assert num_layers(n) == L
    assert n == sum(layer_size(layer) for layer in range(L))
    m = 2**L  # CoinRand: L internal layers hold n-1 processors, everyone is a leaf
    assert coin_internal_layers(m) == L
    assert sum(layer_size(layer) for layer in range(L)) == m - 1


@pytest.mark.parametrize("n", range(2, 70))
def test_coin_internal_nodes_fit_in_n_minus_one(n):
    assert layer_start(coin_internal_layers(n)) <= n - 1


def test_ring_wraps():
    assert [ring_right(i, 4) for i in range(4)] == [1, 2, 3, 0]


def test_layered_threshold_matches_paper_formula():
    n, w_hat = 15, 10_000  # log2(n+1) = 4
    assert layered_threshold(w_hat, 1, n) == -(-w_hat // (4 * 2 * 4))
    assert layered_threshold(w_hat, 3, n) == -(-w_hat // (4 * 8 * 4))
    assert layered_threshold(1, 3, n) == 1


@pytest.mark.parametrize("n", [3, 7, 15, 16, 31, 100])
@pytest.mark.parametrize("w_hat", [1, 2, 5, 40, 1000, 10**6])
def test_layered_counters_cannot_stall_the_root(n, w_hat):
    # Paper Section 3.2: counters below the root hold less than w_hat / 4 triggers in total.
    held = sum(
        min(layer_size(layer), n - layer_start(layer)) * (layered_threshold(w_hat, layer, n) - 1)
        for layer in range(1, num_layers(n))
    )
    assert held < w_hat / 4 or held == 0


@pytest.mark.parametrize("n", [2, 3, 8, 15, 16, 17, 100, 1024])
@pytest.mark.parametrize("w_hat", [1, 2, 3, 7, 50, 1000, 10**6])
def test_coin_round_cannot_stall(n, w_hat):
    # Paper Sections 4.2 and 4.6: the most triggers the system can hold without the root
    # receiving a coin must be below w_hat.
    tau, layers = coin_round_params(w_hat, n)
    assert 1 <= layers <= coin_internal_layers(n)
    coins = 2**layers - 2  # every non-root internal node holds one
    assert coins * tau + n * (tau - 1) < w_hat


def test_coin_phase_boundary():
    n = 16
    assert coin_round_params(16, n) == (1, 4)  # phase 1, w_hat >= n
    assert coin_round_params(15, n) == (1, 3)  # phase 2, floor(log2 15) = 3
    assert coin_round_params(1, n) == (1, 1)
    assert coin_round_params(4 * n + 1, n) == (2, 4)
