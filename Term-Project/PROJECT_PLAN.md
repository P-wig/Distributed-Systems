# Term Project: Distributed Trigger Counting Algorithms

**Reference paper:** V. T. Chakaravarthy, A. R. Choudhury, V. K. Garg, Y. Sabharwal, *Efficient Decentralized Algorithms for the Distributed Trigger Counting Problem* (ACM TOCS, 2012). Local copy: [tocs2012.pdf](./tocs2012.pdf). Section numbers below refer to this paper.

## 1. Goals

The assignment is to **implement and compare** algorithms for distributed trigger counting (DTC). The starting algorithms are **LayeredRand**, **CoinRand** and **RingRand**. The open problem is: **can these algorithms be derandomized?**

1. Implement LayeredRand, CoinRand and RingRand, plus a deterministic baseline.
2. Compare them empirically on message complexity, MaxRcvLoad, MaxMsgLoad and correctness.
3. Investigate derandomization. Identify where each algorithm uses randomness, propose deterministic replacements, and test them experimentally and, where possible, argue about them analytically.
4. Write up the results, including negative results.

> **Naming note.** The paper does not use the name "RingRand". The ring-based algorithm is **ST-Rand** (Section 5). It is described on a ring (a Hamiltonian cycle) and generalizes to any constant-degree spanning tree. We assume RingRand = ST-Rand. *Confirm this with the instructor.*

## 2. Problem Definition (Section 1)

- `n` processors on a complete graph. Each receives triggers from an external source.
- The system must raise an alert once the total number of triggers across all processors reaches `w`. Assume `w >= n`, concretely `w >= n^2`.
- Which processor receives each trigger is chosen by an adversary and is not known in advance.

**Metrics**

| Metric | Meaning |
|---|---|
| Message complexity | Total messages exchanged by all processors |
| MaxRcvLoad | Maximum messages received by any one processor |
| MaxMsgLoad | Maximum messages sent plus received by any one processor |

**Algorithm types.** *Exact* algorithms always alert after `w` triggers. *Las Vegas* algorithms may fail with negligible probability. "With high probability" (w.h.p.) means probability at least `1 - 1/n^c`.

## 3. Algorithms to Implement

Bounds are from Figure 1 and the paper's analysis.

| Algorithm | Section | Message complexity | MaxRcvLoad | MaxMsgLoad | Exact? | Randomness used |
|---|---|---|---|---|---|---|
| Centralized (deterministic baseline) | 2 | `O(n (log n + log w))` | high | high | Exact | None |
| **LayeredRand** | 3 | `O(n log n log w)` | `O(log n log w)` w.h.p. | not bounded | Exact | Random parent in the layer above, on every coin |
| **CoinRand** | 4 | `O(n (log w + log n))` w.h.p. | `O(log w + log n)` w.h.p. | not bounded | Exact | Random node in the next layer up, on every coin |
| **RingRand (ST-Rand)** | 5 | `O(n log n log w)` | `O(log n log w)` w.h.p. | `O(log n log w)` w.h.p. | Approximate (negligible failure probability) | Random decision to start a Collection after each trigger |

The deterministic lower bound for message complexity is `Omega(n log(w/n))` (Garg et al.). This implies a deterministic MaxRcvLoad of at least `Omega(log(w/n))`.

### 3.1 Centralized baseline (Section 2)

- A fixed master. Each processor reports to it after every `B = w_hat / (2n)` local triggers.
- When the master's count reaches `w_hat/2`, it ends the round. Every processor reports its unreported triggers, the master recomputes `w_hat` and `B`, and `B = 1` once `w_hat < 2n`.
- The system never stalls: the unreported triggers total less than `w_hat/2`, and the master's count is also less than `w_hat/2`.
- Message complexity is `O(n log w)`, but the master receives almost all of the messages.

### 3.2 LayeredRand (Section 3)

- `n = 2^L - 1` processors in `L` layers. Layer `l` has `2^l` processors, and only adjacent layers communicate.
- Round threshold for layer `l`: `tau(l) = ceil(w_hat / (4 * 2^l * log(n+1)))`.
- Each processor keeps a counter `C(x)`. A trigger adds 1. A coin from layer `l+1` adds `tau(l+1)`.
- When `C(x) >= tau(l)`, subtract `tau(l)` and send a coin to a **uniformly random** processor in layer `l-1`.
- When the root's counter reaches `ceil(w_hat / 2)`, it starts the end-of-round procedure. This is a broadcast and reduce over the tree to compute the exact count `w'`, then `w_hat = w_hat - w'`.

### 3.3 CoinRand (Section 4)

- `n = 2^L`, with layers 0 to `L`. Layer `l` has `2^l` nodes. Every processor is a leaf, and `n-1` of them also fill the internal layers.
- Single global threshold `tau = ceil(w_hat / (4n))`.
- When a processor's `C(x)` hits `tau`, it resets `C(x)` and sends a coin to a **random** node in layer `L-1`.
- A node that receives a coin keeps it if it holds none. If it already holds one, it forwards the new coin to a **random** node one layer up.
- When the root receives a coin, the round ends. Exact count: `w' = Csum + tau * Ncoins`.
- Phase 2 (Section 4.6): once `w_hat < n`, the internal layers shrink each round and `tau = 1`.

### 3.4 RingRand / ST-Rand (Section 5)

- Processors sit on a ring. Each keeps `C(x)`.
- After each trigger, with probability `8 log n / w_hat`, the processor runs a **Collection**: a sum-reduce around the ring to get `w'`.
- If `w' >= ceil(w_hat/2)`, it runs end-of-round. This updates `w_hat = w_hat - w'`, which is announced around the ring.
- Failure: with small probability, no Collection fires before `w` triggers arrive. The paper assumes `w <= 2^poly(n)`.

### 3.5 Concurrency (Section 6)

All three algorithms assume triggers arrive one at a time. Section 6 removes this assumption. The implementation must follow it, because real asynchronous execution is where bugs appear:

- Two FIFO queues per processor: a default queue for triggers and coins, and a priority queue for end-of-round messages.
- A never-reset counter `D(x)` of processed triggers, and a `RoundNum` stamped on every coin.
- End-of-round (LayeredRand) has four phases: `RoundReset` broadcast (processors stop processing their default queue), `Reduce` of the `D(x)` counts to the root, `Inform` broadcast of the new `w_hat`, and `InformAck` back up the tree, after which processors enter the new round and resume the default queue. Coins from earlier rounds are discarded.
- In RingRand, simultaneous Collections are resolved by smallest initiator id.

## 4. Implementation Plan

### 4.1 Approach

Write a **discrete-event simulator** with one message-passing actor per processor. Do not use real distributed deployment. A simulator makes message counts exact and runs reproducible, and it can run `n` up to thousands.

- **Language:** Python 3.12 only, for the simulator, experiments, analysis and demo. One language means the demo imports the real algorithm code directly.
- **Package:** `src/dtc/` (installed with `pip install -e .`). See [README.md](README.md) for the full layout.
  - `dtc.core`: `Processor` with `on_trigger()` and `on_message(msg)`, a `Network` that delivers messages and counts every send and receive, the event engine, metrics and seeded RNG.
  - `dtc.algorithms`: `Centralized`, `LayeredRand`, `CoinRand`, `RingRand`, each behind a common `Algorithm` interface and a registry keyed by name.
  - `dtc.derand`: derandomized variants of the same interface, so they plug into the same experiments.
  - `dtc.adversary`: trigger distributions and the adaptive adversary.
  - `dtc.experiments`: experiment runner driven by YAML files in `configs/`, writing CSV to `data/results/`.
  - `dtc.analysis`: plots and fits from the CSV files, writing to `figures/`.
- **Reproducibility:** a seeded RNG, with the seed logged in every run.
- **Performance:** pure Python is slow for large runs. Keep the hot paths simple, run seeds in parallel with `multiprocessing`, and avoid `w = n^3` for large `n` (see 4.3).
- **Start with the sequential model** (one trigger fully processed before the next). Add the Section 6 concurrency layer after the sequential versions pass tests.

### 4.2 Correctness checks (run on every algorithm)

- **Exactness:** the alert fires after exactly `w` triggers for exact algorithms, never before and never after. Check over many seeds.
- **No stalling:** after `w` triggers, the alert must have fired. For RingRand, count failures across many seeds and compare to the predicted failure probability.
- **Round invariant:** the triggers in flight in a round never exceed `w_hat` (the paper's no-dead-state argument).
- **Unit tests:** threshold computation, layering and indexing for `n = 2^L` and `n = 2^L - 1`, end-of-round accounting (`w' = Csum + tau * Ncoins`), and phase-2 boundary handling in CoinRand.

### 4.3 Experiment design

**Parameters**

- `n` in {16, 64, 256, 1024, 4096}
- `w` in {`n^2`, `n^2 log n`}, plus `n^3` only for `n <= 256` (larger runs are infeasible, since `w` would be around 7×10^10 at `n = 4096`)
- Trigger distributions (adversary):
  - uniform over processors
  - all triggers to one processor
  - all triggers to a few processors (the paper's `w/4` triggers to four processors example)
  - bursty, and a random permutation
  - adaptive: in the derandomization experiments, targets the processors that tend to receive coins
- 30 or more seeds per configuration.

**Measurements**

- Total messages, MaxRcvLoad and MaxMsgLoad, and the number of rounds.
- Rounds versus the predicted `O(log w)` count.
- Per-layer message load, to show where the load concentrates.
- Failure rate for RingRand.

**Comparison questions**

1. Do measured totals follow the predicted growth? Fit against `n log n log w` and `n (log n + log w)`.
2. How large are the constant factors? Asymptotically better CoinRand may lose at small `n`.
3. Does CoinRand's MaxRcvLoad beat LayeredRand's in practice, as the paper predicts?
4. What does RingRand gain (bounded MaxMsgLoad) and cost (approximate answer)?
5. How far is each from the centralized baseline, which has the lowest message complexity but unbalanced load?

### 4.4 Deliverables

- Source code (`src/dtc/`) with tests and a README on how to run it.
- Raw result data (CSV in `data/results/`) and the plotting code (`dtc.analysis`).
- Demo in `demo/`, with complete creative freedom on its concept.
- Final report with figures and the derandomization analysis.
- Short presentation, if required.

## 5. Open Problem: Derandomization

**Question:** can LayeredRand, CoinRand and RingRand be replaced by deterministic algorithms with the same (or nearly the same) guarantees?

### 5.1 Why it is not trivial

- A deterministic **centralized** algorithm already achieves `O(n log w)` messages, but its MaxRcvLoad equals its message complexity, because one master receives everything.
- The randomized algorithms spread load evenly. With random parents, no node is likely to be hit too often. A deterministic rule has to give the same balancing against an adversary who knows the rule.
- The adversary controls which processors get triggers. If the parent choice is a fixed function, the adversary can aim triggers so that coins pile on one node.
- The research question is whether a deterministic scheme can have both low total messages and low MaxRcvLoad. The paper only shows the lower bound `Omega(log(w/n))` for MaxRcvLoad. It does not give a matching deterministic algorithm.

### 5.2 Where each algorithm uses randomness

| Algorithm | Random choice | Role of the randomness |
|---|---|---|
| LayeredRand | Parent in layer `l-1` for each coin | Spreads coins evenly across a layer. The root round ends only after a proportional number of triggers (Section 3.3 and 3.4 analysis). |
| CoinRand | Target in layer `L-1`, and in each upper layer for forwarded coins | Same load spreading. Also ensures the root does not receive a coin too early (round-length bound, Section 4.3) |
| RingRand | Whether to start a Collection after each trigger | Ensures some Collection fires in time without coordination. Keeps Collection count low. |

### 5.3 Candidate derandomization strategies

For each, implement it as a drop-in replacement and run the same experiments plus adversarial ones.

1. **Round-robin parent selection.** Each processor keeps a pointer and sends successive coins to successive parents in the layer above. This gives perfect balance from the sender's side. Risk: many senders can have aligned pointers and hit the same parent.
2. **Hash-based parent selection.** Parent = `h(sender id, coin index, round)` for a fixed hash. This is pseudo-random and not truly derandomized. It is useful as a baseline for how much true randomness the algorithm needs.
3. **Id-staggered round-robin.** Start each sender's pointer at an offset based on its own id, to avoid alignment of pointers.
4. **Deterministic Collection in RingRand.** Replace "with probability `8 log n / w_hat`" with a rule such as "initiate a Collection every `k`-th local trigger", with different offsets per processor. The aim is that some processor must reach its count in time, whatever the distribution of triggers.
5. **Local load feedback.** A coin is sent to the least-loaded of a small fixed set of candidate parents, based on locally observed counts. Related to "power of two choices", but deterministic.
6. **Small random seed.** Reduce the amount of randomness needed (limited-independence hash families), which is a middle ground between full randomness and full determinism.
7. **Hybrid with the deterministic algorithm.** Use a deterministic hierarchical scheme in which each layer acts like a mini centralized counter with threshold splitting. Analyze the resulting load.

### 5.4 Evaluation of derandomized variants

- **Oblivious adversary:** trigger sequence fixed in advance. Compare each variant with its randomized original.
- **Adaptive adversary:** knows the deterministic rule and aims triggers to maximize MaxRcvLoad. This is the real test of derandomization. A deterministic rule that only works against an oblivious adversary has not solved the problem.
- Report for each variant: whether it stays **exact**, total messages, and MaxRcvLoad under the worst adversary found.
- If a variant has a provable bad case, construct it explicitly and report it as a negative result.

### 5.5 Expected outcomes

Each of these is an acceptable result:

- A deterministic variant matching the randomized bounds experimentally, with an argument or partial proof.
- Evidence that a natural deterministic rule fails, with a concrete adversarial sequence showing it.
- A characterization of the trade-off, for example lower MaxRcvLoad only at the cost of more total messages.

## 6. Timeline

| Phase | Work | Output |
|---|---|---|
| 1 | Read the paper. Install the package and fix the simulator design (language: Python). Confirm RingRand = ST-Rand. | Design notes |
| 2 | Simulator core, metrics, centralized baseline | Working baseline with tests |
| 3 | LayeredRand and CoinRand (sequential model) | Passing correctness tests |
| 4 | RingRand (sequential model) | Passing correctness tests, failure-rate measurement |
| 5 | Concurrency layer (Section 6) | All algorithms correct under asynchronous delivery |
| 6 | Comparison experiments and plots | Data and figures for the comparison |
| 7 | Derandomized variants, adaptive adversary experiments | Data on each variant |
| 8 | Report (and presentation) | Final submission |

Adjust the dates to the course deadlines.

## 7. Risks and Open Questions

- **Name mismatch:** RingRand vs. ST-Rand (see the naming note above).
- **Constants:** the paper's analysis is asymptotic, with unspecified constants. Expect to tune them. The Section 6 proofs apply only to the stated constants.
- **Number of layers:** LayeredRand requires `n = 2^L - 1` and CoinRand `n = 2^L`. Test non-power-of-two `n`, since the paper says only that it "can be extended".
- **Randomized rounds and `w_hat < n`:** boundary cases (CoinRand phase 2, `tau = 1`) need careful tests.
- **Interpretation of "derandomize":** whether the goal is a full deterministic algorithm with the same bounds, or a best-effort investigation. *Confirm the expectation with the instructor.*
