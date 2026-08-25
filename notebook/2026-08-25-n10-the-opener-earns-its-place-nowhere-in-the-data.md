# 2026-08-25 — N10: the opener earns its place nowhere in the data

The six description arms ran on answer key v6. 3,960 calls, `haiku`, parse rate
1.0000 on every arm. Published at
[`results/decision-making/2026-08-25-5ed5d38-n10-six-arms-v6/`](../results/decision-making/2026-08-25-5ed5d38-n10-six-arms-v6/README.md).

Registered in
[`2026-08-24-prediction-n10-the-six-description-arms-on-v6.md`](2026-08-24-prediction-n10-the-six-description-arms-on-v6.md)
and narrowed by
[`2026-08-24-n10-addendum-two-of-six-predictions-were-never-licensed.md`](2026-08-24-n10-addendum-two-of-six-predictions-were-never-licensed.md).
Four predictions were scoreable. One held, two failed, one split.

## The finding that outranks the predictions

`preregistration/decision-making-v2.yaml` registers that the shipped description
fires on decision turns more often than the same description with its
trigger-phrase opener removed. The screen run says the opposite: `full` recalls
0.9909 and `no-opener` recalls 0.9955, and `no-opener` gets there at an FPR of
0.0818 against `full`'s 0.1432.

The opener costs 0.0614 of false-positive rate and returns nothing measurable in
recall. The confirm run is registered against a private holdout that this does
not describe, so nothing is settled. What is settled is that the direction the
hypothesis predicts is absent on the public corpus, and the confirm pathway
should not be built against a v2 hypothesis without someone deciding that on
purpose.

This is the first time the screen arena has changed what a later arena should
do. It is the argument for the arena split, arriving before the expensive run
rather than after it.

## Predictions 2 and 6 failed together

Both expected the 24 `council` and `hinge` positives to fire below the 86
carried ones. All six arms fire on them at 1.0000.

The prediction document anticipated one failure mode — that the new items might
fire low because they are harder turns rather than because the two procedures
are unfamiliar — and registered prediction 3 as the check. Prediction 3 turned
out unlicensed, and the failure that arrived was a third thing neither covered.
Firing did not drop at all.

Routing to those procedures is bad: `hinge` routes correct on 0.3542 of its
fires, second worst of six. So the premise held and the measurement did not
follow from it. Whether a turn is a decision and which procedure it needs are
separate capabilities, and both predictions reasoned about the second while
scoring the first.

Worth carrying forward: a prediction about an unfamiliar procedure belongs on a
routing metric. Firing saturates.

## Prediction 5 held, and the margin does not survive being looked at

`no-exclusions` 0.3000 and `opener-only` 0.2977 top the FPR table, separated
from `stakes-named` at 0.1886 by 0.1091 against a registered 0.10. A cluster
bootstrap on triples: 95% CI [0.0659, 0.1523], 63% of resamples above 0.10.

The bootstrap is exploratory and unregistered. The prediction is scored held on
the rule as written, because a threshold rewritten after seeing the data is not
a threshold. Recording both is the whole point of registering the rule first.

For the next run: a threshold on a difference wants an interval registered with
it, or it is a coin-flip dressed as a result.

## `ledger` is conservative rather than weak

Prediction 4 registered `ledger` as weakest of the four carried routes and
predicted its misroutes would keep landing on `cascade`. Weakest held under both
routing rules. `cascade` failed — the misroutes concentrate on `council` at
44.1%, `cascade` second at 27.1%.

The metric behind "weakest" is `over_answered`, which is route recall. Precision
tells a different story: `ledger` is chosen 47 times at a precision of 0.9574,
the highest of six. `timing` is chosen 324 times at 0.4475 and `council` 239
times at 0.5523.

So the routing failure is competition between procedures rather than a bad
router row on `ledger`. S9 retargeted `ledger`'s row against the `ledger`/
`cascade` confusion; the confusion has since moved onto `council`, which was not
a routing target when S9 was written. A fix aimed at `ledger` in isolation is
aimed at the wrong object.

The precision column is not part of any registered prediction and is one run at
one tier. It says where the fires went. It does not show that narrowing `timing`
or `council` would move them, and finding out means editing the measured
artefact, which is its own registered arm.

## What the run cost to make fast, and what that surfaced

The six arms were run as sixteen concurrent `(arm, band)` processes across four
worktrees, each writing its own checkpoint, merged afterwards as a disjoint
union checked on `(case, repeat)`. 85.6 calls/min against 3.82 serial. Zero
nulls in 3,960 calls at that concurrency, which is the first evidence on this
backend above the eight workers the 2026-08-20 falsifier measured.

Two things only visible because the arms ran in parallel and were audited
per-arm rather than at the end:

- `no-opener` first came back "complete" carrying 43 contiguous nulls, all
  `the CLI stream ended without a result on turn 1`. Contiguity is what
  identified it as one infrastructure window rather than model behaviour. The
  rows were dropped and refilled to 660 at parse rate 1.0000. Voids leave every
  rate's denominator (`run_triggers.py:411`), so the arm was scoreable
  throughout; the hole was in the denominator.
- `--band` shares the full run's checkpoint and no flag redirects it, so band
  parallelism inside one worktree would have meant four processes appending
  multi-kilobyte rows to one file. Four worktrees avoided that. A `--checkpoint`
  override would make sharding a first-class operation, and it belongs in the
  same change as the retry and backoff the runner still does not have.
