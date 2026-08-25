# 2026-08-25 — N10: the opener costs false positives and buys no recall

The six description arms ran on answer key v6. 3,960 published calls, `haiku`,
parse rate 1.0000 on the published set. Published at
[`results/decision-making/2026-08-25-5ed5d38-n10-six-arms-v6/`](../results/decision-making/2026-08-25-5ed5d38-n10-six-arms-v6/README.md),
scored by [`scripts/score_n10.py`](../scripts/score_n10.py).

Registered in
[`2026-08-24-prediction-n10-the-six-description-arms-on-v6.md`](2026-08-24-prediction-n10-the-six-description-arms-on-v6.md)
and narrowed by
[`2026-08-24-n10-addendum-two-of-six-predictions-were-never-licensed.md`](2026-08-24-n10-addendum-two-of-six-predictions-were-never-licensed.md).
Four predictions were scoreable. One held, two failed, one split.

## The finding that outranks the predictions

`preregistration/decision-making-v2.yaml` registers that **on the private
holdout**, the shipped description fires on decision turns more often than the
same description with its trigger-phrase opener removed, **by at least 0.086**.

On the public corpus the recall difference is 0.0046 in the other direction,
and paired on all 220 positive rows it is one discordant call: `no-opener` fires
where `full` misses once, `full` fires where `no-opener` misses never. Exact
McNemar p = 1.0000. On the registered metric the two arms separate by nothing.

The false-positive rate does separate them. `full` 0.1432 against `no-opener`
0.0818, a 42.9% reduction, 57 discordant negatives split 42 to 15, p = 0.0005.

So the opener costs false positives and buys no detectable recall. That is not a
falsification. The hypothesis is registered against a private holdout that does
not exist yet, this run is the screen tier, and its recall comparison has a
single discordant call in it. What a v3 pre-registration would have to start
from is the false-positive result, because the recall result is the one with
nothing in it.

This is the first time a screen result has changed what the confirm arena should
be registered against, and it arrived before that arena was built. That ordering
is the arena split working. It saved no money: the confirm run is registered at
1,320 calls and this screen run made 3,960.

## Predictions 2 and 6 failed together

Both expected the 24 `council` and `hinge` positives to fire below the 86
carried ones. All six arms fire on them at 1.0000.

The prediction document anticipated one failure mode, that the new items might
fire low because they are harder turns rather than because the two procedures
are unfamiliar, and registered prediction 3 as the check. Prediction 3 turned
out unlicensed, and the failure that arrived was a third thing neither covered.
Firing did not drop at all.

Routing across those two procedures is uneven. Of the turns labelled for
`hinge`, 0.3542 reached `hinge`, second lowest of six, while `council` sits at
0.9167, the highest of six. So the premise held and the measurement did not
follow from it. Whether a turn is a decision and which procedure it needs are
separate capabilities, and both predictions reasoned about the second while
scoring the first.

Worth carrying forward: a prediction about an unfamiliar procedure belongs on a
routing metric. Firing saturates.

## Prediction 5 held, and the margin does not survive being looked at

`no-exclusions` 0.3000 and `opener-only` 0.2977 top the FPR table, separated
from `stakes-named` at 0.1886 by 0.1091 against a registered 0.10. A paired
cluster bootstrap on the 110 triples, seed 1, 20,000 resamples: 95% CI
[0.0659, 0.1523], 64.5% of resamples above 0.10.

The bootstrap is exploratory and unregistered. The prediction is scored held on
the rule as written, because a threshold rewritten after seeing the data is not
a threshold. Recording both is the whole point of registering the rule first.

For the next run: a threshold on a difference wants an interval registered with
it, or it is close to a coin flip dressed as a result.

## `ledger` is picked rarely and picked well

Prediction 4 registered `ledger` as weakest of the four carried routes and
predicted its misroutes would keep landing on `cascade`. Weakest held under both
routing rules. `cascade` failed: of the 177 misroutes, `council` takes 44.1%,
`cascade` 27.1%, `timing` 15.8%.

The metric behind "weakest" is `over_answered`, which is route recall. On turns
that should fire, `ledger` is chosen 47 times at a precision of 0.9574, the
highest of six, while `timing` is chosen 324 times at 0.4475. Across every row
in the run the picture is dimmer for all of them, `ledger` 0.4167 and `timing`
0.2984, because many picks land on turns that should not have fired at all. The
ordering survives that wider denominator and the 0.9574 does not.

So a fix aimed at making `ledger` pick better is aimed at a column that is
already high. What is low is how often the turns labelled for `ledger` reach it,
and this run does not say whether that is `ledger`'s row, the rows around it, or
both. Nothing here varies a router row, so nothing here reaches a mechanism.

S9 retargeted `ledger`'s row against the `ledger`/`cascade` confusion. On v6 the
misroutes concentrate on `council`. `council` was not a routing target when S9
was written, so no measurement from then could have located this, and none is
compared against.

## How these calls were collected, which is not uniform across the arms

Recorded because the run record needs it and because it is the part of this run
I got wrong first.

**Two arms were collected alone and four under sixteen-way concurrency.** `full`
and `no-opener` ran as whole-corpus single processes. The other four ran as
sixteen concurrent `(arm, band)` processes across four worktrees pinned to the
same commit, because `--band` shares the full run's checkpoint and no flag
redirects it, so band parallelism inside one worktree would have meant four
processes appending multi-kilobyte rows to one file.

Arm is therefore confounded with collection load, and the four concurrent arms
sit higher on FPR at every band. Two things cut against reading that as a load
effect: `stakes-shown` was collected concurrently and sits below single-process
`full`, and load fell over the window while the gap is widest at `xl`, the
lowest-load cell. It cannot be resolved from this record. Prediction 5 names two
arms that are both in the concurrent group.

`run_triggers.py` collects serially and knows nothing about any of this. The
concurrency was introduced at the OS-process level, outside what the code can
see or refuse, and `runner.py`'s `CONCURRENCY_UNSAFE` register says this backend
is unmeasured for concurrency rather than safe.

**The published zero-null figure is a post-repair number.** `no-opener` first
completed carrying 43 contiguous nulls, all `the CLI stream ended without a
result on turn 1`. Contiguity is what identified one infrastructure window
rather than model behaviour. Those rows were dropped and refilled, so at least
4,003 calls were made and 3,960 are published. All 43 refills fired `True`, as
did the same 43 cases at repeat 0 which were never touched, and no surviving
verdict changed.

That zero is not evidence that sixteen-way concurrency is harmless, and it was
offered as such in the first draft of this entry. The nulls occurred in a
single-process arm, and the 2026-08-20 falsifier that cleared concurrency at
eight workers had a serial control arm and a paired test. This run has neither.

Two things for the runner, both already filed: a `--checkpoint` override would
make sharding a first-class operation instead of four worktrees and a merge
script, and the retry-and-backoff it still lacks would have refilled that window
without a human deciding which rows were infrastructure.

A row carries no collection provenance at all: no timestamp, no duration, no
worktree, no commit. Nothing in the published files distinguishes a row
collected alone from one collected sixteen-way, or a repaired row from an
original. Establishing everything above needed untracked run logs and a
scratch-directory backup. That is the gap worth closing before the next
sharded run.
