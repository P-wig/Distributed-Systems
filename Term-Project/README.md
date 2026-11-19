# Distributed Trigger Counting

Implementation and comparison of LayeredRand, CoinRand and RingRand (the paper's ST-Rand), plus derandomization experiments. See [PROJECT_PLAN.md](PROJECT_PLAN.md) for goals and plan, and [tocs2012.pdf](tocs2012.pdf) for the reference paper.

## Layout

| Path | Contents |
|---|---|
| `sim/` | Go: shared interfaces (processor, message, network) and metrics |
| `algo/centralized/` | Go: deterministic baseline |
| `algo/layeredrand/`, `algo/coinrand/`, `algo/ringrand/` | Go: the three randomized algorithms |
| `algo/derand/` | Go: derandomized variants |
| `adversary/` | Go: trigger distributions and the adaptive adversary |
| `cmd/experiment/` | Go: experiment runner, writes CSV to `data/results/` |
| `cmd/demoserver/` | Go: optional live backend for the demo |
| `analysis/` | Python: plots and analysis of the CSV results |
| `demo/` | Python: the demo |
| `data/results/`, `data/traces/` | Generated CSV results and JSONL event traces (git-ignored) |
| `docs/` | Data format contract between Go and Python |
| `report/` | Final report |

## Usage

```
go build ./...
go test ./...
go run ./cmd/experiment

pip install -r analysis/requirements.txt
pip install -r demo/requirements.txt
```
