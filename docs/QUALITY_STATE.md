# Quality track: state

**Audience:** an agent picking up the decision-quality track.

**This file is the resumption point.** Read it first, do what the next unit says,
and rewrite it before you finish. It is hand-maintained and says so.

## North star

> A row in [`../SCORECARD.md`](../SCORECARD.md) stating what a decision procedure
> does to decision quality, from a confirmation run, with its guards passing.

`SHIP`, `PROVISIONAL`, `NULL` and `HARMFUL` all reach it. An empty table does
not.

Every measurement on record so far asks whether the skill fires. This track asks
the other question. The design, the three instrument families and the phase
order are registered in
[`../notebook/2026-08-25-prediction-the-quality-venue-and-the-tau-rule.md`](../notebook/2026-08-25-prediction-the-quality-venue-and-the-tau-rule.md).

## Rules for every session on this track

- **A unit ends when the next unit is written here.** Finishing the work and
  updating this file are one action.
- **Three stop conditions exist.** The north star is reached. The maintainer says
  stop. Or every remaining unit is blocked, with the evidence written below.
- **A pause is not a stop, and is never reported as a completion.** Quota
  exhaustion, wall clock, a green gate, a landed phase and a finished sub-agent
  are checkpoints. The runner is checkpointed and resumable so that running out
  of quota is a nap.
- **Work around blockers.** The table below carries a pre-decided move for each
  class. A question reaches the maintainer at a phase boundary, after every lane
  that does not depend on the answer is finished.

## Blocker protocol

| Blocker | Do this |
|---|---|
| Quota window closes | `Backoff.breaker_trips` aborts and the checkpoint holds. Record the resume key below and resume. |
| A gate fires | Its successor unit is already written. Execute it. |
| A pre-registered kill fires | A kill closes a stratum. Families A, B and C are independent. Execute the named successor. |
| The design rule fails the discriminator | Discard the block, rebuild the rule, re-author. Never patch items until green. |
| An answer key is disputed | Rewrite the ask and re-adjudicate blind. Precedent 2026-08-18: 11 of 12 resolved this way, movement 0.046 to 0.004, no label moved. |
| A parameter is missing | Derive it, or record the choice as a choice with its arithmetic. Standing rule 1. |
| Another session holds a file | `Edit` over `Write`, stage only your own paths, and keep candidates outside `GOVERNED` so `de check` stays green for everyone else. |
| Two concurrent units in one worktree | Give each its own worktree. The pre-commit hook gates the **whole working tree**, so one unit's half-written file fails the other's commit and neither can land. Found 2026-08-25 by doing it wrong. |
| A commit fails the hook on a file you do not own | Verify your own paths directly with `ruff check`, `mypy` and `pytest` scoped to them, then retry the commit. Never `--no-verify`, and never fix the other unit's file to get green. Retry on a timer: the other unit finishing turns the gate green without anyone touching your files. |
| Your work vanishes from the tree for a minute | Pre-commit stashes the whole tree, so a concurrent session's hook run can carry off your **unstaged** edits and put them back on its next pass. Stage your paths as soon as they are worth keeping; the stash cannot reach the index. Observed 2026-08-25 during W1. |
| `de check` red on a shared tree | Fix it, or move the work out of the shared path. `--no-verify` is not how a red gate gets resolved. |
| A sub-agent returns "looks good" | The review has not run. Re-brief and re-dispatch. |
| A sub-agent is slow or thin | Dispatch a replacement in parallel and take whichever lands first. |
| Ambiguous scope | Finish everything that does not depend on the answer, write the assumption here, keep going. |

## Where the work is

**Phase 0, unblock the pipeline.** Worktree `quality-track`, branched from
`54b1648`.

| unit | what | state |
|---|---|---|
| W0 | Register the tau rule, the consensus rule, the multiplicity family and W2's acceptance tests | **done** — the notebook entry above |
| W1 | Tau v2 in `stats/track_h.py`, plus `cluster_bootstrap_statistic` in `stats/cluster.py`. v1 stays callable. | **done** — 140 tests, `stats` at 100% line and branch |
| W3 | `_run_loop` extraction from `runner.py`, `run_isolated` in `providers/claude_code.py`, new `elicit.py`, backpressure fault-injection test | **done** — 95 tests; landed in `7f175a7` |
| W3b | `elicit.py` generalised off scalars: `ScalarAsk`/`MembershipAsk`/`CallAsk` behind a closed union, `condition_label` split from `arm`, `common_item_set`, `exclusion_counts` by arm | **done** — branch `elicit-generic` at `d5d02b7`, full gate green, 82 tests. Not merged; lands at the phase boundary. |
| 0G | This file | **done** |
| W2 | Quantity layer in `scripts/size_track_h_phase0.py` and the two two-branch gates. Re-derives `smallest_usable_n`. | unblocked, not started |
| W4 | Blind scalar extractor, `consensus_quantity`, and the `fal-z` and `fal-u` falsifier cases | unblocked, not started |
| P1 | The `ledger` yield probe and its control arm, 90 calls | **done** — both kills fired; `results/track-h/2026-08-25-f578604-ledger-yield-and-ceiling/` |
| P3b-`hinge` | The `hinge` H01 control screen, 40 unaided blind readings | **done** — ceiling kill fired at crossed +0.850 machine, +0.950 hand-adjudicated; `results/track-h/2026-08-25-c9f649a-hinge-control-screen/` |

## The next three units

**Read this first: the order of operations changed, and it is the most useful
thing this track has learned.** `ledger` was closed for 90 calls, and then all of
Family A for 9 more, by reading a gate's blind arms as a control arm *before* the
corpus was built. Every venue from here runs that probe first. Authoring a corpus
and then discovering the unaided model is at ceiling is what the last five venues
did.

**P2 fired and Family A is closed.** The v2 screen ran one triplet under both
repairs the L04 review named. All three arms unanimous, all three equal to key,
unaided J = 1.000, on an item that was harder by every measure anyone proposed,
with sibling width at 10 of 10 in every arm. `ledger`, `timing` and `fit` all
close together, because what failed is the thing they share: the scalar
elicitation form. Record:
[`../results/track-h/2026-08-25-28311e2-ledger-v2-screen/`](../results/track-h/2026-08-25-28311e2-ledger-v2-screen/README.md).

**P3b fired on `hinge`, and that closes it too.** 40 unaided blind readings of
H01, 20 per arm, crossed primary **+0.850** [+0.725, +0.975] against a registered
kill of 0.70. A blind adjudicator agreeing 36 of 40 puts it at **+0.950**
[+0.850, +1.000], and all four disagreements are the scorer losing a hit rather
than manufacturing a swap. Record:
[`../results/track-h/2026-08-25-c9f649a-hinge-control-screen/`](../results/track-h/2026-08-25-c9f649a-hinge-control-screen/README.md),
write-up
[`../notebook/2026-08-25-the-hinge-screen-ceilings-and-two-validity-checks-fail.md`](../notebook/2026-08-25-the-hinge-screen-ceilings-and-two-validity-checks-fail.md).

**P3b fired on `cascade` too, at J = +1.000**, [+0.772, +1.000], over 40 blind
readings, format-violation gap 0.000, adjudication coverage 1.000 with zero
movement. That run lands from another lane and its record is not in the
repository yet, so this file names the number and links nothing.

**All three families are now at ceiling on single-call scale.** Family A at
unaided J = 1.000 over 99 readings, `hinge` at +0.950 hand-adjudicated,
`cascade` at +1.000. Three independent constructs, six domains, three answer-key
shapes. What that licences is a claim about the venue: a scenario compact enough
to fit one prompt is not, for a current model, hard, whatever shape the answer
takes. What it does not licence is anything about volume, long context,
delegation, or work carried across a conversation, which is where the failures
the six procedures describe mostly live. **`council` is the last instrument
standing, and it has no answer key and no base arm.**

**One thing the `cascade` run found that bears on every adjudicated number
here.** Its three blind judges had mean pairwise rationale similarity of 0.806
and wrote identical opening text on 17 of 40 cases, which is what three samples
of one model at default sampling look like. A separate lane is measuring whether
`scripts/adjudicate.py` behaves the same way. It does not reach `hinge`'s 36 of
40, which was **one blind pass** compared against the machine scorer rather than
judges compared against each other, and stating that difference is cheaper than
having to reconstruct it later.

Three things the `hinge` run leaves behind for whoever runs the next screen.

- **The `d/N` dropout bound is vacuous rather than passed.** `d` came in at 0, so
  the rule measured nothing on this run. It is not a validated guard and must not
  be recorded as one.
- **Two registered validity checks failed, and neither touches the primary.**
  `decoys_are_live` (F_B and F_D named zero times in 40 readings) and
  `fork_is_real` (pivotal 20 of 20 `SIGN`, minority share 0.000 against a floor
  of 0.15). H01 can no longer say anything about decoy resistance, and its
  pivotal arm is not sitting near its recommendation threshold.
- **The dismissal-parsing block is scoped correctly.** The control arm's
  adjudicated fraction is 1 of 40 = 0.025 against a 0.25 kill, where the v6 note
  measured 15 of 21 on procedure-following phrasings. The skill-arm block stays
  where that note put it.

**The denominator rule from P3a binds every instrument from here.** For every
rule that removes a record from a denominator, say what makes a record leave,
whether that is correlated with doing the task well, and which direction it
pushes. **A rule that cannot answer all three does not ship**, and every
exclusion class is printed by arm. All three instruments failed that before
review, which is why the attrition would have been invisible in the published
output. Full account:
[`../notebook/2026-08-25-three-exclusion-rules-and-all-three-read-high-on-the-treatment.md`](../notebook/2026-08-25-three-exclusion-rules-and-all-three-read-high-on-the-treatment.md).

1. **`council`, screen in flight, and the last instrument standing.** Four draws
   per item under one pre-registered ordering, AB only. Unanimity admits, the run
   stops early on the first disagreement, and `BALANCED` counts as a call.
   Unaided, `sonnet`, blind, every reply recorded verbatim, the isolation receipt
   read off a smoke call before any screen draw was issued. Screen draws are
   discarded from the primary and may never be reused as data.

   `council` has no answer key and no base arm, so its ceiling analogue is the
   opposite failure: a second-position rate indistinguishable from 0.5 means no
   order effect exists and there is nothing for a procedure to fix. The
   registered point predictions are a true second-position rate of 0.60 and a
   commit rate of 0.70, at which the reporting gate refuses the run.

   **One defect outranks the screen and is not closed by it. There is no `arm`
   dimension anywhere in `council`'s scorer**, while its kill condition requires
   an arm comparison. Every number it can currently produce is a one-arm
   description, and `on` against `off` is the question this project exists to
   answer. Field names come from `solvers/arms.py`, shared with the
   `elicit-generic` work.
   *Acceptance:* the screen reports its second-position rate with the reporting
   gate's verdict stated either way, and the scorer carries `arm` before a
   measurement call is spent on the primary.

2. **The successor venue, and it is not a fourth instrument.** Three constructs,
   six domains and three answer-key shapes have now ceilinged, and the
   registration named this outcome before any of them ran: if the remaining
   families also ceiling, "the reading available is not that three constructs
   failed but that **single-call scale is the wrong scale**, and the successor is
   the volume and delegation venue rather than a fourth instrument". Authoring a
   fourth construct at this scale spends calls on a question three screens have
   answered.

   What the venue has to carry is the thing none of the three touched: work at
   volume, over long context, under delegation, or across a conversation. That is
   where the failures the six procedures describe live, and no measurement in
   this repository has reached it.
   *Acceptance:* a registered design, a pre-registered kill, and a control-arm
   probe read **before** anything is authored at scale. That order is what closed
   `ledger` for 90 calls and Family A for 9, and it is the rule this track has
   paid for twice.

**What W3b bought, and one thing it found.** Families B and C could not reach
[`SCORECARD.md`](../SCORECARD.md) at all before this: every call on the quality
track has gone through sub-agents, so nothing carries a checkpoint, a cost ledger
or an isolation receipt. `elicit.py` was blind by construction and hard-coded to
scalars, which Family A no longer needs and Families B and C cannot use. It now
serves all three, and `unit` lives only on `ScalarAsk`, so a `council` item has no
field to leave null rather than an optional one to fill in wrongly.

Two of its findings matter beyond the module. `common_item_set` exists because a
long item can overflow the window in `on`, `in_situ` and `placebo` while fitting
in `off`, which scores the arms on **different item sets** and, if length tracks
difficulty, pushes the document-carrying arms up — the same direction as all three
Family B and C defects. The union of items that overflow in any arm is dropped
from every arm, and it is reported whether or not it is empty.

And an `infrastructure` row occupies its own resume key in `elicit.py`, so a
resumed run never re-issues it, while the docstring said retrying was the right
answer. **Audited: no published number is affected.** No record under `results/`
carries `call_status` at all, and the shared `_run_loop` writes no row on failure —
it continues and re-raises — so a resumed `run_arm` re-issues the call and its key
stays free. The defect is specific to `elicit.py`, which has produced no records.

3. **W2 and W4**, unblocked and unchanged, below. They serve Family A's scalar
   pipeline, which is now closed, so they drop to the bottom of the order: what
   they still buy is a verified movement rule for any later venue that elicits a
   quantity, and the near-threshold falsifier tier that §7 says nothing currently
   tests.

## Open kills

| kill | reading | successor if it fires |
|---|---|---|
| Authoring yield below 3 of 5 on `ledger` at K = 10 | **FIRED, 2 of 5.** L01 cut on a governing arm whose obstacle is remediable, firing disqualifiers 15 and 12 together. L04 cut on the same-alarm dimension, label-sound and construct-void. L05 cut on triviality and disqualifier 14. L02 and L03 survived reviews raising eight and six objections. | executed: Families B and C carry the track |
| Unaided J at or above 0.70 on a stratum | **FIRED on all of Family A, J = 1.000.** 90 unaided readings on `ledger` v1, then 9 more on a v2 item built under both named repairs: 18 arms, 99 readings, every arm unanimous and every arm equal to key, over six domains and three difficulty dials. | executed: `ledger`, `timing` and `fit` all closed. Families B and C, which never used the scalar triplet, carry the track. |
| Discriminator outside its permutation-derived band | not yet measured | discard the block, rebuild the design rule |
| Three constructs cannot express a scalar elicitation | **answered, and the other way round.** All three express it fine; the form is what ceilings. | moot — Family A is closed on the ceiling, not on expressibility |
| Unaided J at or above 0.70 on `hinge` | **FIRED, crossed +0.850.** 40 unaided blind readings of H01, 20 per arm, at `c9f649a`. Machine +0.850 [+0.725, +0.975]; a blind adjudicator agreeing 36 of 40 puts it at +0.950 [+0.850, +1.000]. Two registered validity checks failed alongside it, `decoys_are_live` and `fork_is_real`, and neither touches the primary. | executed: `hinge` closes on set-membership elicitation at single-call scale. `cascade` and `council` carry the track. |
| Unaided J at or above 0.70 on `cascade` | **FIRED, J = +1.000**, [+0.772, +1.000], over 40 blind readings, format-violation gap 0.000, adjudication coverage 1.000 with zero movement. Landing from another lane; the record is not in the repository yet. | executed: `cascade` closes, and `council` is the last instrument standing |

## Resume key

Landed: `7f175a7` (registration, tau v2, runner), `63ea7c3` (pre-registration
v3), `f578604` (site), `e7a1e22` (the ledger run and its 90 readings), `28311e2`
(the Family A closure in [`STATUS.md`](STATUS.md)), `cf7a3f8` (the prediction
covering all three P3b screens), and this change (the `hinge` screen and its 40
readings). Worktrees `quality-track` and `quality-corpus`, the second
fast-forwarded onto the first so the registration is a genuine ancestor of the
run rather than a claim.

No checkpoint exists, because all 139 calls were dispatched as sub-agents rather
than through `scripts/run_triggers.py`. Nothing here belongs in
[`SCORECARD.md`](../SCORECARD.md) and none of these READMEs claims it does. The
first unit that runs through the real runner creates the checkpoint, and the
successor venue is now the first candidate. `cascade`'s 40 readings are not in
that 139: they land with their own record from another lane, and its call ledger
entry is that lane's to add.

**The `hinge` instrument is in the repository now.** Its three arms, its answer
key as data, its version 6 note and all 40 readings are under
[`../results/track-h/2026-08-25-c9f649a-hinge-control-screen/`](../results/track-h/2026-08-25-c9f649a-hinge-control-screen/README.md),
so a cold start has it. The scoring code is not: it fails `ruff check` and
`ruff format`, and reformatting it to land it would leave a scorer here that is
not the scorer that ran. `key-h01-v3.json` carries the vocabulary those modules
hold, which is what a reader needs to check a label by hand.

`council` still sits in a scratchpad and a cold start does not have it, and
`cascade` lands with its own record from another lane. If the scratchpad is gone,
what survives is the review findings above: the batteries were green and the
batteries were not the test, so a rebuild briefed on the three denominator
questions is worth more than the artefacts were.

**The lesson is one step further along than Family A's.** There, reading the blind
arms as a control arm before authoring the corpus saved ninety calls. Here, a
green two-branch falsifier battery passed on all three instruments that a review
then found unfit to fail anything — because a battery written by the author tests
the implementation against the author's own expectations, and the defect was in
the expectations. **An author's battery is not a review, and a green one buys
nothing on its own.**

**Two hazards found the hard way, both worth reading before starting.**
Pre-commit stashes the whole tree, so a concurrent session's hook run can carry
off your unstaged edits — stage early, the stash cannot reach the index. And a
pathspec commit builds a tree from HEAD plus its own paths, which reverts other
units' files while leaving their new files on disk; with three units in one tree
no ordering of three commits is green and the whole tree is, so they land
together.
