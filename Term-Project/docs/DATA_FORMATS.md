# Data Formats

## Experiment results: `data/results/<config name>.csv`

One row per simulation run.

| Column | Type | Meaning |
|---|---|---|
| `algorithm` | string | `centralized`, `layered_rand`, `coin_rand`, `ring_rand` |
| `variant` | string | derandomized variant name, or empty for the original algorithm |
| `n` | int | number of processors |
| `w` | int | trigger threshold |
| `adversary` | string | trigger distribution name |
| `seed` | int | RNG seed for the run |
| `alert_fired` | bool | whether the alert was raised |
| `triggers_at_alert` | int | triggers received when the alert fired (equals `w` for exact algorithms) |
| `rounds` | int | number of rounds |
| `total_msgs` | int | message complexity |
| `max_rcv_load` | int | MaxRcvLoad |
| `max_msg_load` | int | MaxMsgLoad |

## Event traces: `data/traces/*.jsonl` (optional)

One JSON object per line, written by `dtc.core.trace` and used by the demo for replay. Every event has `t` (logical time, integer) and `type`.

| `type` | Extra fields | Meaning |
|---|---|---|
| `config` | `algorithm`, `n`, `w`, `seed`, `layout` | first line of a trace; `layout` describes node positions or layers |
| `trigger` | `node` | a trigger arrived at `node` |
| `msg` | `from`, `to`, `kind`, `round` | a message was sent |
| `round_end` | `round`, `w_hat` | a new round started with initial value `w_hat` |
| `alert` | `triggers` | the alert was raised |

## Experiment configs: `configs/*.yaml`

Keys: `name`, `algorithms`, `variants` (optional), `n` (list), `w_factor` (`n_squared`, `n_squared_log_n` or `n_cubed`), `adversaries`, `seeds` (count).
