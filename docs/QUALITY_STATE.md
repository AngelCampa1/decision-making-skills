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
| W3 | `_run_loop` extraction from `runner.py`, `run_isolated` in `providers/claude_code.py`, new `elicit.py`, backpressure fault-injection test | in flight |
| 0G | This file | **done** |
| W2 | Quantity layer in `scripts/size_track_h_phase0.py` and the two two-branch gates. Re-derives `smallest_usable_n`. | blocked on W1 |
| W4 | Blind scalar extractor, `consensus_quantity`, and the `fal-z` and `fal-u` falsifier cases | blocked on W3 |

## The next three units

1. **W2, after W1 lands.** Add a quantity layer upstream of
   `draw_event_indicators` that draws log-normal elicitation noise and calls the
   real `derive_movement_threshold` and `classify_movement`. Wire the drift and
   coverage gates into `check_known_answers`.
   *Acceptance:* drift below 0.02 under the pooled rule **and above 0.10 under
   the maximum rule**; coverage 0.95 within Monte Carlo error recomputed **and
   inside 0.61 to 0.85 held fixed**. Both branches of both gates run. A
   single-branch pass is not a pass.

2. **W4, after W3 lands.** A blind quantity extractor under the scripts
   directory, three instances,
   importing `ADJUDICATORS` rather than redeclaring it. Add `fal-z` (a reply
   stating no number: the extractor returns null, never zero) and `fal-u` (a
   reply whose unit differs from the stated one: the extractor reports the number
   and converts nothing).
   *Acceptance:* the battery scores sensitivity 1.0 and specificity 1.0 on
   hand-written responses, before any generation call. Standing rule 2 is
   satisfied there or the track stops there.

3. **W5, the corpus schema and the six pilot triplets.** One triplet per
   construct, eighteen files, staged under a candidates directory beside the
   other run records rather than under `datasets/`, which is governed and shared.
   *Acceptance:* `load_quality_corpus` returns a two-tuple whose second element
   is the only place an answer key lives, and a static-import test shows the
   elicitation modules never import it.

## Open kills

| kill | reading | successor if it fires |
|---|---|---|
| Authoring yield below 3 of 5 on `ledger` at K = 10 | **2 of 5 cut, 3 pending.** L05 cut on triviality and disqualifier 14; L01 cut on a governing arm whose obstacle is remediable, firing disqualifiers 15 and 12 together. The kill fires if any one of L02, L03 or L04 also falls. | Family A drops to `timing` at reduced n; Families B and C carry the track |
| Unaided J at or above 0.70 on a stratum | not yet measured | that stratum closes; the others continue |
| Discriminator outside its permutation-derived band | not yet measured | discard the block, rebuild the design rule |
| Three constructs cannot express a scalar elicitation | open, and the largest design risk | `cascade`, `council` and `fit` move to Family B or C. W5's pilot is what surfaces this, deliberately before 45 triplets are authored rather than after. |

## Resume key

No run has started and no checkpoint exists. The run directory for this track
is created by the first unit that makes a call.

W0 and 0G are written and green against `de check --fast`, and are held
uncommitted while W1 and W3 finish, because the pre-commit hook reads the whole
tree. Commit them first when the tree is consistent: the registration is
evidence only if it predates the implementation in the history.
