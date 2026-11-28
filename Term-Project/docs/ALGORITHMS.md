# The Algorithms in Plain English

This is a plain-language guide to the algorithms in this project. For the formal details, thresholds and bounds, see [PROJECT_PLAN.md](../PROJECT_PLAN.md) and the paper ([tocs2012.pdf](../tocs2012.pdf)).

## 1. The problem

Imagine `n` computers (**processors**). Events called **triggers** arrive at them from the outside. Think of votes, sensor readings or clicks. We don't control which computer gets which trigger. An adversary decides.

We want to raise an **alert** as soon as the total number of triggers across *all* computers reaches a number `w`. No single computer sees the whole picture, so they have to talk to each other.

We care about three costs:

| Cost | Plain meaning |
|---|---|
| **Message complexity** | How many messages are sent in total |
| **MaxRcvLoad** | How many messages the busiest computer *receives* |
| **MaxMsgLoad** | How many messages the busiest computer *sends plus receives* |

Total messages matter, but so does fairness. An algorithm that is cheap overall but makes one computer handle almost every message is not useful.

## 2. The idea all of them share: rounds

Counting every trigger exactly would take a message per trigger, which is far too expensive. Instead the algorithms work in **rounds**:

1. Keep a guess `w_hat` of how many triggers are still missing. At the start it is `w`.
2. Let computers count triggers locally and send only *occasional, rough* updates.
3. Detect when about **half** of `w_hat` has arrived.
4. End the round. Do one exact count of all triggers so far, and subtract it from `w_hat`.
5. Repeat. Each round halves what is left, so there are only about `log w` rounds.
6. When fewer than about `n` triggers remain, switch to reporting every trigger, so the alert is exact.

The algorithms differ in step 2 and step 3: how computers send rough updates, and how they notice that half the work is done.

## 3. The baseline: Centralized

One computer is the **master**. Every other computer counts its own triggers and reports to the master after every `B = w_hat / (2n)` local triggers. When the master has heard about `w_hat / 2` triggers, the round ends. Everyone sends in their leftover count, and the master works out the new `w_hat`.

- **Good:** very few messages in total, and always exact.
- **Bad:** the master receives nearly every message, so MaxRcvLoad is huge.

The three algorithms below try to keep this low message cost while spreading the load around.

## 4. LayeredRand

**Picture:** a pyramid. Computers are arranged in a binary tree with layers. The top layer is a single **root**, the next has 2 computers, then 4, 8 and so on. `n = 2^L - 1`.

**How it works:**

- Each computer keeps a counter. A trigger adds 1 to it.
- Each layer has its own **threshold**. Lower layers (more computers, each seeing few triggers) have small thresholds. Upper layers (few computers, receiving lots of traffic) have large ones.
- When a computer's counter reaches its layer's threshold, it takes that amount out of its counter, wraps it up as a **coin**, and sends the coin to a **randomly chosen computer one layer up**.
- A computer that receives a coin adds the coin's value to its own counter. If that pushes it over *its* threshold, it sends a coin one layer further up, again to a random computer.
- When the root's counter reaches half of `w_hat`, the round is over. The root starts an exact count by asking everybody (broadcast down the tree, add up on the way back up). Then `w_hat` is updated and the next round begins.

**Why the randomness matters:** by choosing a random parent, no computer in a layer gets flooded with coins, even if the adversary sends all triggers to one place.

**Result:** exact, with fairly low receive load, but no bound on how many messages a single computer *sends*.

## 5. CoinRand

**Picture:** the same pyramid idea, but simpler and faster. Every computer is a leaf at the bottom, and some of them also play the role of the upper layers. `n = 2^L`.

**How it works:**

- There is just **one threshold for everyone**: `tau = w_hat / (4n)`.
- When a computer has seen `tau` triggers, it makes a coin and sends it to a **random computer in the layer just above the leaves**.
- A computer that receives a coin and has none of its own simply **holds on to it**.
- If it already holds a coin, it passes the *new* coin on to a **random computer one layer higher**.
- When a coin reaches the root, the round ends. The exact total is the triggers still sitting in local counters plus `tau` for every coin stored in the tree.
- When `w_hat` drops below `n`, there are very few triggers left, so `tau = 1` and the tree shrinks round by round (the paper's "phase 2").

You can think of it as a tournament: coins only travel up when they collide with a coin that is already there, so the upper layers see very little traffic.

**Result:** exact, and the best bounds of the three on total messages and receive load. Like LayeredRand, it puts no bound on how many messages one computer sends.

## 6. RingRand (called ST-Rand in the paper)

**Picture:** computers sit in a circle. There are no layers and no coins.

**How it works:**

- Each computer just counts its own triggers.
- After **every** trigger, a computer rolls a very biased die. With probability about `8 log n / w_hat` it starts a **Collection**.
- A Collection is a message that goes once around the ring. Each computer adds in its own count, so the initiator learns the exact total `w'` of triggers so far.
- If `w'` is at least half of `w_hat`, the round ends. The new `w_hat` is announced around the ring.
- If two computers start a Collection at the same time, the one with the smaller id wins.

**The catch:** everything hinges on the dice. It is possible, with very low probability, that nobody ever starts a Collection in time, and the alert is missed. So RingRand is **approximate**: correct with very high probability but not guaranteed (the paper calls this Las Vegas style).

**What you get for that risk:** no single computer sends or receives too many messages, so it is the only one with a bound on MaxMsgLoad.

## 7. Side-by-side summary

| | Centralized | LayeredRand | CoinRand | RingRand |
|---|---|---|---|---|
| Shape | One master | Binary tree, per-layer thresholds | Tree, one global threshold | Ring |
| How rough progress is reported | Periodic reports to the master | Coins sent up to a random parent | Coins sent up, forwarded only on collision | Random Collections around the ring |
| Exact? | Yes | Yes | Yes | Almost always |
| Load spread | Terrible | Good (receive) | Best (receive) | Good (send and receive) |
| Where randomness is used | None | Choice of parent | Choice of parent | Whether to start a Collection |

## 8. Why we care about randomness

The randomized algorithms rely on random choices to spread load, even against an adversary. The project's open question is whether those random choices can be replaced by **deterministic rules** (round-robin, hashing and so on) without losing the guarantees. The risk is that an adversary who knows the rule can aim triggers to overload one computer. See section 5 of [PROJECT_PLAN.md](../PROJECT_PLAN.md).

## 9. Handling the real world (concurrency)

The descriptions above pretend triggers arrive one at a time. In reality, triggers and messages overlap, so the paper adds some rules:

- Each computer has two queues: a normal one for triggers and coins, and a priority one for end-of-round messages.
- Every coin is stamped with its round number, so coins left over from an old round are thrown away.
- Each computer keeps a never-reset count of triggers it has processed, so the exact count at the end of a round is always right.

The plan is to build the one-at-a-time version first, then add these rules.
