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
thing this track has learned.** `ledger` was closed for 90 calls, and then all of
Family A for 9 more, by reading a gate's blind arms as a control arm *before* the
corpus was built. Every venue from here runs that probe first. Authoring a corpus
and then discovering the unaided model is at ceiling is what the last five venues
did.

**P2 fired and Family A is closed.** The v2 screen ran one triplet under both
repairs the L04 review named. All three arms unanimous, all three equal to key,
unaided J = 1.000 — and the item was harder by every measure anyone proposed,
with sibling width at 10 of 10 in every arm. `ledger`, `timing` and `fit` all
close together, because what failed is the thing they share: the scalar
elicitation form. Record:
[`../results/track-h/2026-08-25-28311e2-ledger-v2-screen/`](../results/track-h/2026-08-25-28311e2-ledger-v2-screen/README.md).
Families B and C never used that form. They carry the track, which is the
independence the three-family split was built for.

1. **P3a, land the three repairs.** All three are done and each scores its own
   two-branch falsifier battery on hand-written responses, before any generation
   call. `cascade`: 14 fixtures plus 3 one-rule-removed mutants; four control
   replies that walk past the item score J = 1.000 with the denominator gate
   removed and `undefined` with it. `council`: 35 checks, six mutants each caught
   by a different case, and a registered per-item dispersion statistic closing
   the objection that signed rates cancel. `hinge`: 29 checks, 22 hand-written
   responses over five populations, and a prompt-length delta of zero characters
   held through the repair.
   *Acceptance:* one commit per family carrying the battery, the revised items,
   the re-registered numbers and a [`DECISIONS.md`](DECISIONS.md) entry. A key
   that moved bumps `set_version` and no comparison crosses it.

2. **P3b, the Family B and C control screens.** The Family A lesson, applied
   before anything is authored at scale: read the unaided arm of each repaired
   instrument first. `hinge` and `cascade` are set-membership, so the ceiling
   argument that closed Family A does not transfer — a model at ceiling on
   arithmetic can still fail to name what it cannot do — but that is a
   hypothesis, and it is cheap to test.
   *Acceptance:* per family, an unaided J below 0.70 on a screen of at least
   three items. At or above 0.70 closes that family on the ceiling kill already
   on record, and `council` — which has no answer key and no base arm at all —
   is then the last instrument standing.

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
| Unaided J at or above 0.70 on `hinge` or `cascade` | not yet measured; P3b is the screen | that family closes and `council`, which has no answer key and no base arm, is the last instrument standing |

## Resume key

Landed: `7f175a7` (registration, tau v2, runner), `63ea7c3` (pre-registration
v3), `f578604` (site), `e7a1e22` (the ledger run and its 90 readings), `28311e2`
(the Family A closure in [`STATUS.md`](STATUS.md)), and this change (the v2 screen
and its 9). Worktrees `quality-track` and `quality-corpus`, the second
fast-forwarded onto the first so the registration is a genuine ancestor of the
run rather than a claim.

No checkpoint exists, because all 99 calls were dispatched as sub-agents rather
than through `scripts/run_triggers.py`. Nothing here belongs in
[`SCORECARD.md`](../SCORECARD.md) and none of these READMEs claims it does. The
first unit that runs through the real runner creates the checkpoint, and P3b is
the first candidate.

The three repaired Family B and C instruments sit in a scratchpad, batteries
green, waiting on P3a to land them. They are not in the repository and a session
resuming from a cold start does not have them — if the scratchpad is gone, the
briefs that produced them are the three bullets under P3a and each battery is
reproducible from its own item YAMLs.

**Two hazards found the hard way, both worth reading before starting.**
Pre-commit stashes the whole tree, so a concurrent session's hook run can carry
off your unstaged edits — stage early, the stash cannot reach the index. And a
pathspec commit builds a tree from HEAD plus its own paths, which reverts other
units' files while leaving their new files on disk; with three units in one tree
no ordering of three commits is green and the whole tree is, so they land
together.
