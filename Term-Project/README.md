# Distributed Trigger Counting

Implementation and comparison of LayeredRand, CoinRand and RingRand (the paper's ST-Rand), plus derandomization experiments, all in Python. See [PROJECT_PLAN.md](PROJECT_PLAN.md) for goals and plan, and [tocs2012.pdf](tocs2012.pdf) for the reference paper.

## Layout

| Path | Contents |
|---|---|
| `src/dtc/core/` | Simulation core: processor, network, event engine, metrics, seeded RNG, trace recorder |
| `src/dtc/algorithms/` | Centralized baseline, LayeredRand, CoinRand, RingRand, layouts, registry |
| `src/dtc/derand/` | Derandomized parent-selection and Collection policies |
| `src/dtc/adversary/` | Oblivious trigger distributions and the adaptive adversary |
| `src/dtc/experiments/` | Config loading and the parallel experiment runner |
| `src/dtc/analysis/` | Result loading, plots and growth-rate fits |
| `configs/` | YAML experiment definitions (`smoke`, `comparison`, `derandomization`) |
| `tests/unit/`, `tests/integration/` | Unit tests and end-to-end correctness tests |
| `demo/` | The demo (imports `dtc` directly) |
| `data/results/`, `data/traces/` | Generated CSV results and JSONL traces (git-ignored) |
| `figures/` | Generated plots (git-ignored) |
| `docs/` | Data format reference |
| `report/` | Final report |

## Setup and usage

```
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,demo]"

pytest
dtc-experiment configs/smoke.yaml
streamlit run demo/app.py
```

`dtc-experiment` and the demo are placeholders until implemented.
