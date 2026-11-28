"""Experiment config loading and trial expansion tests."""

from pathlib import Path

import pytest

from dtc.experiments.config import compute_w, expand_trials, load_config

CONFIGS = Path(__file__).resolve().parents[2] / "configs"


def test_compute_w():
    assert compute_w(16, "n_squared") == 256
    assert compute_w(16, "n_squared_log_n") == 256 * 4
    assert compute_w(16, "n_cubed") == 4096
    with pytest.raises(ValueError):
        compute_w(16, "bogus")


def test_smoke_config_expands_to_all_trials():
    cfg = load_config(CONFIGS / "smoke.yaml")
    trials = expand_trials(cfg)
    assert len(trials) == 4 * 1 * 1 * 3  # algorithms x n x adversaries x seeds
    assert {t.w for t in trials} == {15**2}
    assert sorted({t.seed for t in trials}) == [0, 1, 2]
    assert all(t.variant == "" for t in trials)


def test_derandomization_config_includes_variants():
    cfg = load_config(CONFIGS / "derandomization.yaml")
    trials = expand_trials(cfg)
    assert len(trials) == 3 * 4 * 3 * 3 * 30
    assert {t.variant for t in trials} == set(cfg.variants)


@pytest.mark.parametrize("name", ["smoke", "comparison", "derandomization"])
def test_all_shipped_configs_load(name):
    assert expand_trials(load_config(CONFIGS / f"{name}.yaml"))
