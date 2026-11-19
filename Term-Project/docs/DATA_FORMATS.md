# Data Formats (Go <-> Python contract)

The Go simulator and the Python analysis/demo code communicate only through
these files. Keep this document in sync with the code on both sides.

## Experiment results: `data/results/*.csv`

One row per simulation run.

| Column | Type | Meaning |
|---|---|---|
| `algorithm` | string | `centralized`, `layeredrand`, `coinrand`, `ringrand`, or a derandomized variant name |
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

## Event traces: `data/traces/*.jsonl`

One JSON object per line, used by the demo for replay and live streaming.
Every event has `t` (logical time, integer) and `type`.

| `type` | Extra fields | Meaning |
|---|---|---|
| `config` | `algorithm`, `n`, `w`, `seed`, `layout` | first line of a trace; `layout` describes node positions or layers |
| `trigger` | `node` | a trigger arrived at `node` |
| `msg` | `from`, `to`, `kind`, `round` | a message was sent |
| `round_end` | `round`, `w_hat` | a new round started with initial value `w_hat` |
| `alert` | `triggers` | the alert was raised |
