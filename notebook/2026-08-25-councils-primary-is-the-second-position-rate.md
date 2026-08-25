# 2026-08-25 — `council`'s primary is the second-position rate, not the flip rate

A ruling, dated and recorded before the instrument has a commit. It belongs here
rather than in [`docs/DECISIONS.md`](../docs/DECISIONS.md) because that register
is checked against governed commits and refuses an entry naming none — correctly,
since an entry that names no commit cannot be checked against anything. `council`
touches none of the four governed paths yet. When its corpus lands under
`datasets/`, that commit is governed and carries the register entry, and this is
what it will point at.

## The discrepancy

**The plan and the pilot name different estimators, and nothing recorded the
change.** The programme's Family C row says "recommendation flip rate under AB and
BA ordering". The `council` pilot killed the flip rate and replaced it with the
second-position rate. That replacement was never written down anywhere a reader of
the numbers could reach: the phrase "second-position rate" appears nowhere in this
repository, while three agents have been building against it.

Found by the agent generalising `decision_evals.elicit`, which noticed that the
record type it was designing had to serve one statistic or the other and could not
tell which was registered. It declined to adopt either silently, which is the
reason this entry exists rather than a silent convergence on whichever one got
written first.

## They are different statistics

A model that always names the same course whatever the ordering has a **flip rate
of 0.0** and a **second-position rate of 0.5**.

## The ruling, and the pilot's kill was sound

**The second-position rate is primary. The flip rate is superseded.**

The flip rate has no floor. On an item where the two courses are genuinely even, a
model with no position dependence at all coin-flips *within* a single ordering, so
it produces a flip rate near 0.5 — and 0.5 is also what a badly inconsistent model
produces. The statistic cannot separate "correctly indifferent" from "unstable",
which is the whole question `council` asks. The second-position rate has an exact
null at 0.5 under balanced orderings, so the same behaviour reads as the null
rather than as half a defect.

Both are computable from the same records, and the runner's record type carries
what each needs — `cluster_id` with `ordering` for the flip rate, the printed first
and second course for the position marginal — with a test asserting the two diverge
on an order-blind model. So this governs which is **primary** and forecloses
nothing.

## What it costs

The `council` pilot's own four K02 records were collected under the older framing
*and* under a format contract carrying the positional word "above" — in an
instrument whose entire primary is a position effect. They are not evidence for
either statistic.

## Why this is written down at all

Nothing forced it. The gate does not reach `council`, no published number moves,
and the change had already been made in practice by three agents who agreed with
each other. That is the condition under which a decision goes unrecorded and later
becomes indistinguishable from a result — which is the argument the decision
register opens with, and it applies whether or not the register's own scope
happens to cover the file.
