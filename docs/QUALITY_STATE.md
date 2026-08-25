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
| 0G | This file | **done** |
| W2 | Quantity layer in `scripts/size_track_h_phase0.py` and the two two-branch gates. Re-derives `smallest_usable_n`. | unblocked, not started |
| W4 | Blind scalar extractor, `consensus_quantity`, and the `fal-z` and `fal-u` falsifier cases | unblocked, not started |
| P1 | The `ledger` yield probe and its control arm, 90 calls | **done** — both kills fired; `results/track-h/2026-08-25-f578604-ledger-yield-and-ceiling/` |

## The next three units

**Read this first: the order of operations changed, and it is the most useful
thing this track has learned.** `ledger` was closed for 90 calls by reading a
gate's blind arms as a control arm, *before* its corpus was built. Every venue
from here runs that probe first. Authoring a corpus and then discovering the
unaided model is at ceiling is what the last five venues did.

1. **P2, the `ledger` v2 screen.** One triplet under both repairs the L04 review
   named — indirect binding, so the governed entity is identified by a property
   resolved through the sibling set rather than named in the core block, and a
   multi-input rule sentence, so more than one quantity routes. Both preserve
   skeleton identity. Then the bare arm first: three arms, three blind instances,
   nine calls. Registered in
   [`../notebook/2026-08-25-prediction-can-a-ledger-item-be-repaired-off-the-ceiling.md`](../notebook/2026-08-25-prediction-can-a-ledger-item-be-repaired-off-the-ceiling.md).
   *Acceptance:* the unaided arm is not 3 of 3 unanimous and equal to key. If it
   is, **Family A closes entirely** rather than dropping to `timing`, and the
   finding is about scalar elicitation rather than about one construct.

2. **P3, the Family B and C repairs, then their screens.** All three pilots
   killed part of their own registered primary and named the replacement, which
   is what pilots are for and why they ran before any corpus:
   - `cascade`: the effect/foreclosure partition is unreadable by a membership
     scorer, because doing without something is itself an ability, so any effect
     touching the actor supports a *keep* or *avoid* phrasing. Replacement: one
     target read across both arms.
   - `council`: flip rate cannot be the primary, because a true tie item
     coin-flips within a single ordering and leaves no floor. Replacement:
     second-position rate, null exactly 0.5 under balanced orderings.
   - `hinge`: the `NONE`-keyed matched arm does not terminate — every silence a
     reader closes opens another, and a required single-slot block always finds
     one. Replacement: give the matched arm its own on-list pivotal candidate so
     naming lands in-set.
   *Acceptance:* each repaired primary scores its own two-branch falsifier on
   hand-written responses before a single generation call. Standing rule 2.

3. **W2 and W4**, unblocked and unchanged, below.

### W2 and W4, as originally written

**W2.** Add a quantity layer upstream of `draw_event_indicators` that draws
log-normal elicitation noise and calls the real `derive_movement_threshold` and
`classify_movement`. Wire the drift and coverage gates into
`check_known_answers`.
*Acceptance:* drift below 0.02 under the pooled rule **and above 0.10 under the
maximum rule**; coverage 0.95 within Monte Carlo error recomputed **and inside
0.61 to 0.85 held fixed**. Both branches of both gates run. A single-branch pass
is not a pass.

**W4.** A blind quantity extractor under the scripts directory, three instances,
importing `ADJUDICATORS` rather than redeclaring it. Add `fal-z` (a reply stating
no number: the extractor returns null, never zero) and `fal-u` (a reply whose
unit differs from the stated one: the extractor reports the number and converts
nothing).
*Acceptance:* the battery scores sensitivity 1.0 and specificity 1.0 on
hand-written responses, before any generation call.

## Open kills

| kill | reading | successor if it fires |
|---|---|---|
| Authoring yield below 3 of 5 on `ledger` at K = 10 | **FIRED, 2 of 5.** L01 cut on a governing arm whose obstacle is remediable, firing disqualifiers 15 and 12 together. L04 cut on the same-alarm dimension, label-sound and construct-void. L05 cut on triviality and disqualifier 14. L02 and L03 survived reviews raising eight and six objections. | executed: Families B and C carry the track |
| Unaided J at or above 0.70 on a stratum | **FIRED on `ledger`, J = 1.000** over 45 unaided readings, 15 of 15 arms unanimous and equal to key. The 45 readings under G1's brief agree exactly, so the gate was measuring the cheap thing. | `ledger` closed; P2 tests whether the repairs escape it, and Family A closes entirely if they do not |
| Discriminator outside its permutation-derived band | not yet measured | discard the block, rebuild the design rule |
| Three constructs cannot express a scalar elicitation | open, and the largest design risk | `cascade`, `council` and `fit` move to Family B or C. W5's pilot is what surfaces this, deliberately before 45 triplets are authored rather than after. |

## Resume key

Landed: `7f175a7` (registration, tau v2, runner), `63ea7c3` (pre-registration
v3), `f578604` (site), `e7a1e22` (the ledger run and its 90 readings). Worktrees
`quality-track` and `quality-corpus`, the second fast-forwarded onto the first so
the registration is a genuine ancestor of the run rather than a claim.

No checkpoint exists, because the 90 calls were dispatched as sub-agents rather
than through `scripts/run_triggers.py`. P2 is nine calls and does not need one.
The first unit that runs through the real runner creates the checkpoint.

**Two hazards found the hard way, both worth reading before starting.**
Pre-commit stashes the whole tree, so a concurrent session's hook run can carry
off your unstaged edits — stage early, the stash cannot reach the index. And a
pathspec commit builds a tree from HEAD plus its own paths, which reverts other
units' files while leaving their new files on disk; with three units in one tree
no ordering of three commits is green and the whole tree is, so they land
together.
