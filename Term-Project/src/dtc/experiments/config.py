"""Load and validate YAML experiment configs from configs/, and expand them into trials."""

import math
from dataclasses import dataclass
from pathlib import Path

import yaml

W_FACTORS = {
    "n_squared": lambda n: n**2,
    "n_squared_log_n": lambda n: n**2 * math.ceil(math.log2(n)),
    "n_cubed": lambda n: n**3,
}


def compute_w(n: int, w_factor: str) -> int:
    try:
        return W_FACTORS[w_factor](n)
    except KeyError:
        raise ValueError(f"unknown w_factor {w_factor!r}; options: {sorted(W_FACTORS)}") from None


@dataclass(frozen=True)
class TrialSpec:
    """Everything needed to reproduce one simulation run."""

    algorithm: str
    n: int
    w: int
    adversary: str
    seed: int
    variant: str = ""


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    algorithms: list[str]
    n: list[int]
    w_factor: str
    adversaries: list[str]
    seeds: int
    variants: list[str]


def load_config(path: str | Path) -> ExperimentConfig:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    missing = {"name", "algorithms", "n", "w_factor", "adversaries", "seeds"} - raw.keys()
    if missing:
        raise ValueError(f"{path}: missing keys {sorted(missing)}")
    compute_w(2, raw["w_factor"])  # validates the name
    return ExperimentConfig(
        name=raw["name"],
        algorithms=list(raw["algorithms"]),
        n=list(raw["n"]),
        w_factor=raw["w_factor"],
        adversaries=list(raw["adversaries"]),
        seeds=int(raw["seeds"]),
        variants=list(raw.get("variants") or [""]),
    )


def expand_trials(cfg: ExperimentConfig) -> list[TrialSpec]:
    """Cross product of algorithm x variant x n x adversary x seed (seeds are 0..seeds-1)."""
    return [
        TrialSpec(algorithm, n, compute_w(n, cfg.w_factor), adversary, seed, variant)
        for algorithm in cfg.algorithms
        for variant in cfg.variants
        for n in cfg.n
        for adversary in cfg.adversaries
        for seed in range(cfg.seeds)
    ]
