# 2026-08-26 — The search that never searched, and three more ways to report a clean run

Phase 1 of the evolution study: the substrate edits, the `evolution/` package,
and `de evolve`. No prediction is registered here and no number below is a
result. What is worth recording is that four separate defects in this loop all
had the same signature — **a completed run, exit code zero, a plausible
winner** — and none of them would have shown up in a checkpoint.

## What landed

`candidate` is a sixth arm, rendered through the `on` arm's code path so that
what differs between a written body and a generated one is the author and not
the delivery. `RunRecord` grew `seed` and `candidate_sha`; `run_arm` grew a
`resume_fields` parameter that defaults to the `("item_id", "arm")` every
published run resumed on, because widening it by default would have made
`completed_keys` skip every existing checkpoint line and silently re-run whole
published runs.

`BudgetLedger` grew a call cap, a wall-clock cap and backoff accounting, and it
now **refuses at construction** when a venue reports no cost and carries neither.
That refusal is the whole point of the class on a free tier: dollars read zero on
Ollama and on NVIDIA Build, so the guard that stopped every previous run here
cannot fire on either. `NestedBudget` is three of those at once — run, generation,
child — because one pathological candidate eating the entire budget before the
search has been anywhere is a different failure from the run as a whole going
long, and a single ledger only sees the second.

`_run_loop` charges all three currencies now. Calls come free from
`record`'s default; seconds come from each record's `duration_ms` plus the time
`Backpressure` spent holding the run at a rate limit, charged after each batch
rather than at the end, because a cap read once the run is over is a report.

The corpus lock moved out of `scripts/calibrate.py` into `generators/audit.py`.
An evolution loop resumes a checkpoint per candidate, so it is library code now,
and a second copy of a hash function is a second answer.

## The four defects, in the order they were found

**One.** `propose_new_texts` is documented optional and read without a `getattr`
default, so an adapter that omits it raises on every proposal. GEPA catches the
error, retries, gives up, and exits zero reporting the seed as the winner.
Recorded in yesterday's entry; the fix is a class attribute set to `None`, and
`lineage.assert_searched` is the check that catches the next engine that does
this differently.

**Two.** The adapter reported `num_metric_calls=len(records)` — the calls the
harness actually made, which is smaller than the batch whenever a candidate is
re-evaluated on items already scored. GEPA's `max_metric_calls` therefore never
fell. The run did not terminate. It wrote **4,665 lineage lines for a search of
two distinct candidates** before it was stopped by hand. Two fixes: report the
evaluations to the engine and charge the calls to the ledger, which are different
questions; and record each candidate once rather than on every evaluation.

**Three.** The budget authorised `len(batch)` calls per evaluation, including the
ones about to resume off the checkpoint for nothing. A search stopped at its
per-child cap after two candidates, refusing to spend what it was not going to
spend. The ledger is now asked to authorise the same work the runner is about to
do, computed from the same resume key.

**Four, and the most instructive.** The mock reflector appended the first ladder
rung not already present in the instruction it was shown. It could never get past
rung one: GEPA accepts on strict improvement, rung one is worth nothing, the
rejected candidate is discarded, and the next proposal starts from the same base
and produces the same rung again. The search converged after two candidates
having never reached the rung that was worth something, and reported a winner and
a score, and exited zero. **A search that stalls at its first proposal and a
search that converges look identical from outside.** The fix counts proposals
rather than reading the text.

Read defects two through four together and the pattern is not about GEPA. Three
of them are the harness reporting a number for a search that did not happen, and
in every case the visible output was a lineage, a winner and a score.

## The smoke, once all four were fixed

Mock venue, in-process, no server and no key. `--limit 8 --max-calls 400`:

| generation | candidate | parent | score |
| --- | --- | --- | --- |
| 0 | `edc3ee70` | — | 0.375 |
| 1 | `fba6c522` | `edc3ee70` | 0.667 |
| 2 | `2c831224` | `fba6c522` | 0.667 |
| 3 | `39e3b22c` | `2c831224` | 1.000 |

Sixteen kilobytes of `lineage.jsonl`, and the table above is read from it and
nothing else. **None of these numbers mean anything about a skill.** The mock
venue answers correctly when a fixed phrase appears in the system prompt and
guesses otherwise; it is an oracle, not a capability, and it is built that way so
that a smoke run exercises proposal, scoring, acceptance, budget and lineage
without producing a figure anyone could mistake for a measurement.

`parent_sha` is proposal order rather than observed descent, because GEPA does
not report which candidate a proposal was mutated from. It is right whenever the
search moves forward and wrong whenever it branches back to an earlier point on
the frontier. SkillOpt reports parentage and will not need the approximation.

## Two things this does not have

**SkillOpt has no driver yet.** `de evolve --engine skillopt` refuses rather than
guessing. Its environment package is the next commit.

**The seed pools are asserted, not yet used against a real holdout.** `POOLS` puts
training at 0–999, validation at 1000–1499 and the holdout at 10000 and up, and
`assert_evolvable` refuses a batch carrying a holdout seed or a seed in no pool
at all. Nothing has been minted at those seeds. The firewall exists before the
data it guards, which is the right order and is also why it is untested against
the thing it is for.

## Next

Phase 2, and it starts with a prediction entry rather than a run: projected call
counts, the target and reflector models, and the headroom check on whether
`qwen3:4b` has room to improve on this corpus at all. The candidate-count floor
from defect one goes in that prediction as a validity condition, not a nicety.
