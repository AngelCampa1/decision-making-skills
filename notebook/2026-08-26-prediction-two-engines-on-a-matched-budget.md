# 2026-08-26 — Prediction: two engines, one matched budget, on qwen3:1.7b

Registered before the first call of Phase 2. Committed before the runs start, so
the ancestry check can see it.

## What will be run

Two searches over the same corpus, the same splits, the same scorer and the same
venue. The only thing that differs is the engine.

| | |
| --- | --- |
| target | `ollama/qwen3:1.7b`, temperature 0, serial |
| reflector / optimizer | `nvbuild/openai/gpt-oss-120b` |
| train pool | seed 0, `--limit 70` — 70 items, ten templates, seven strata |
| validation pool | seed 1000, `--limit 21` — 21 items |
| holdout | untouched. `assert_evolvable` refuses any batch carrying a seed ≥ 10000 |
| engines | `gepa` 0.1.4, `skillopt` 0.2.0 |

Why this target is 1.7B rather than the 4B the plan named, and why the selection
rule that chose it had to be corrected first, is in
[the entry before this one](2026-08-26-two-defaults-that-could-not-run-and-a-sample-that-measured-one-seventh-of-the-corpus.md).

## The budgets are matched, and that is the point

SkillOpt's call count falls out of its own loop: one epoch over 70 training
items at `batch_size` 8 is 9 steps, and each step is 8 training rollouts plus a
21-item acceptance gate. **261 target calls.**

GEPA's is set by `max_metric_calls`, so it is set **to match**: 300.

Unmatched budgets would make this a comparison of how much each engine was
allowed to spend. The two numbers are not identical because neither engine
takes an exact call count as input, and 261 against 300 is as close as their
respective knobs reach.

At 12.1 s/call this is roughly 53 minutes for SkillOpt and up to an hour for
GEPA, plus reflector calls that are hosted, free and not on the clock that
binds. Reflector calls are not counted in the matched budget because they are
not target calls and the two engines call their reflectors differently by
design; the run records both.

## What will be computed, from which records, over which denominator

**The primary quantity is mean item score on the validation pool**, computed by
`DecisionAdapter.score` — which is `run_arm` into `score_item`, the same
function every published run in this repository uses — over a denominator of the
21 validation items, read from `records.jsonl` joined on
`(candidate_sha, seed, item_id)`.

For each engine: the seed body's score, the declared winner's score, and the
difference. The winner is whichever body the engine itself hands back, read from
`result.best_candidate` for GEPA and `best_skill.md` for SkillOpt, because the
acceptance rule is part of what an engine is.

**No verdict comes out of this.** `ollama` is the `dev` arena and emits none.
Phase 2 exists to produce two frozen bodies; whether they beat a placebo on
fresh items is Phase 3's question and needs the holdout that does not exist yet.

## Validity conditions, checked before the numbers are read

1. **Both searches explored at least two distinct candidates.**
   `lineage.assert_searched` enforces it. A search whose every proposal failed
   reports the seed as its winner and exits zero, which is how four separate
   defects presented earlier today.
2. **Some possible response scores above zero.** Established: the same items and
   scorer returned 0.762 unaided on this target.
3. **No holdout seed appears in any batch.** `assert_evolvable` refuses one.
4. **Zero-cause audit before any comparison.** A `0.000` that is an HTTP 404
   already happened once today. Any candidate whose score moves by more than a
   few points gets its `zero_cause` column read before the move is believed.

If condition 1 fails for an engine, that engine has no result and the failure is
the finding, not a smaller number.

## The predictions

Falsifiable, and they stay whatever happens.

1. **Both engines explore at least three distinct candidates.** Confidence:
   moderate for GEPA, lower for SkillOpt, whose acceptance gate is stricter and
   which has never run against this environment with a live model.
2. **At least one winner beats the seed body on validation by ≥ 3 points**
   (0.6 of 21 items, so in practice ≥ 1 item). Confidence: moderate. This is a
   low bar and it is deliberately low, because 21 validation items cannot
   support a claim about anything larger.
3. **Format violations fall.** Unaided, this target violates the format on 2.4%
   of items. Both engines see `format_violation` in the reflective feedback, and
   "emit an ANSWER line" is a far easier edit than "decide better". Confidence:
   moderate, with the caveat that 2.4% of 21 items is half an item and there may
   be no room to show it.
4. **Neither winner generalises.** I expect any validation gain to be mostly
   overfitting to 21 items, and Phase 3's fresh holdout to shrink it toward
   zero. Confidence: this is the prediction I would most like to be wrong about,
   and it is the one the whole study exists to test.

## Where I expect to be wrong

**Prediction 3 is the one most likely to invert.** A reflector told that the
model failed to emit an answer line may respond by adding formatting
instructions that lengthen the skill, and a longer skill on a 1.7B model can
crowd out the reasoning that was producing the correct answers. A gain in format
compliance bought with a loss in accuracy would satisfy the letter of the
prediction and miss the point, so both are reported.

**The matched budget may not be matched in the way that matters.** 261 target
calls buys SkillOpt 9 gradient steps and buys GEPA some number of proposals that
depends on how often its minibatches look promising. Equal calls is not equal
search, and if the candidate counts come out far apart, the comparison is about
call efficiency rather than about search quality — which is worth reporting and
is not what this was designed to measure.

**The reflector is a 120B model reading the output of a 1.7B one.** Its
proposals may be well beyond what the target can follow. That is a real
configuration people use and it is the planned one, but a winner that helps a
larger model and not this one would be invisible here.

---

## Amendment, before any scored comparison: an output cap

Registered above without one, and the first GEPA run showed why there has to be
one. Appended rather than edited into the text above, which stands as written.

**What happened.** Eight items into the seed candidate's validation pass, one
call generated **40,960 output tokens over 317 seconds** and never emitted an
answer line. 40,960 is a server ceiling, not a stopping point: the model entered
a reasoning loop and ran until something else stopped it. That one call was 89%
of the elapsed time of the run to that point.

**Why it breaks the design rather than merely slowing it.** The budgets are
matched at 261 target calls against 300 so that the comparison is between two
engines. A runaway costs roughly 50 ordinary calls' worth of wall clock, the
run's guard is `max_seconds`, and the guard would have bound long before either
call cap. Whichever engine happened to draw more runaways would have searched
less, and the result would have been a measurement of luck.

**The evidence for where to put the cap.** Across 168 records on three models:

| model | longest completed answer | longest call | runaways |
| --- | --- | --- | --- |
| `qwen3:4b` | 4,479 | 6,595 | 0 of 76 |
| `qwen3:1.7b` | 1,611 | 40,960 | 1 of 42 |
| `qwen3:0.6b` | 847 | 847 | 0 of 42 |

No answer that finished has ever exceeded 4,479 output tokens. **The cap is
8,192**, which is above every completed answer on record by a factor of 1.8 and
below every runaway by a factor of 5.

**Why this does not bias the comparison.** It is set on the venue, so it applies
identically to every arm and every candidate. A runaway scores `no_answer_line`
capped or uncapped — the item is wrong either way, and only the clock changes.
The one thing it could distort is a skill that legitimately needs more than
8,192 tokens to answer, and nothing in 168 records has come within half of it.

`max_tokens` defaults to zero everywhere else, which sends no cap, so every
published run's behaviour is untouched. The number reaches `run.json`, because a
search's instrument settings are part of what the search was.

**Prediction 3 gains a companion.** It said format violations would fall. It is
now also worth recording that this target's format violations have two distinct
causes — an answer that finished in the wrong shape, and a generation that never
finished at all — and they call for different edits. The run reports them apart:
a capped runaway is a record with `output_tokens` at the cap.

---

## Amendment, before SkillOpt's first scored run: the guard sits above the projection

Registered above at 261 target calls for SkillOpt against 300 for GEPA. The 261
is wrong by one pass, and using it as a cap would do something the registration
did not intend.

**The arithmetic.** Nine steps of eight training rollouts plus a 21-item
acceptance gate is 9 x 29 = 261. The trainer also scores the seed body on all 21
validation items **before** the first step, to have something for its gate to
compare against. That baseline is 21 target calls and was left out. The loop
needs **282**.

**Why the difference matters.** GEPA's 300 is a cap: `max_metric_calls` is the
knob, and the engine searches until it binds. SkillOpt has no such knob — its
call count falls out of epochs and batch size — so 261 was a *projection* of
what its loop would spend, not a budget chosen for it. Setting `--max-calls` to
a projection that is 21 short converts a guard into a truncation, and it would
truncate inside the ninth step's acceptance gate: the last proposal would be
scored on part of the validation pool and then stopped. Whatever came out of
that would be an artefact of my arithmetic.

**The correction.** SkillOpt's guard is set to **300**, the same number GEPA
had, and its loop is left to terminate on its own at 282. Neither engine is
stopped by the other's shape. This is a smaller deviation than the alternative,
because the registered claim was that the budgets are matched and 300 against
300 is more matched than 261 against 300.

The comparison this run reports is still per-engine spend against a common
ceiling, and both spends are recorded: what an engine *chose* to use is part of
what it is, and that is the number worth reading rather than the ceiling.

**No prediction changes.** The four above stand as written. This changes what
stops a run, and no engine reaches either number by being better at deciding.

---

## Amendment, before SkillOpt's first scored run: the reflector changes, and GEPA runs again

Registered above with `nvbuild/openai/gpt-oss-120b` as the reflector for both
engines. It stopped answering on 2026-08-27, partway through SkillOpt's first
working run, and the study cannot wait for it.

**What was observed.** Every chat completion to that model hangs: a sixteen-token
request times out at 45 seconds, repeatedly, over eighteen minutes. The API
itself is healthy — `/v1/models` returns 200 in 1.2 seconds and still lists the
model with no end-of-life marker. `openai/gpt-oss-20b` on the same endpoint,
with the same key, answers in 2.1 seconds.

It is not an entitlement problem in the shape already on record from
2026-08-26, when `gemma-3-4b-it` returned an HTTP 404 for an account that could
see it in the catalogue. A 404 is an answer. This is no answer at all, which is
worse, because SkillOpt's model layer wraps every call in
`except Exception: time.sleep(...)` and prints nothing, so a dead reflector
looks exactly like a slow one for as long as the retries last.

**The catalogue is moving under the study.** Two models queried in the same
minute returned HTTP 410 Gone: `meta/llama-3.3-70b-instruct`, retired
2026-08-26 — the day before this — and `qwen/qwen3-next-80b-a3b-instruct`,
retired 2026-07-27. A free tier retires models on its own schedule, and a run
that takes hours can start on a model that exists and finish on one that does
not.

**The change.** The reflector for both engines becomes
**`nvbuild/openai/gpt-oss-20b`**: same vendor, same endpoint, same key, same
model family, and it is still far larger than the 1.7B target. `arenas.py`
registers `nvbuild/openai/` by prefix, so this needs no model-registry change
and no entry in `DECISIONS.md`.

**GEPA runs again.** Its matched run of 2026-08-26 used the 120B reflector and
completed. Keeping it and running SkillOpt against the 20B would make the
comparison between an engine *and* a reflector, which is the one thing the
matched budget exists to prevent. So both engines re-run from scratch on the
same reflector, and the earlier GEPA run stays on record as what it is: a
finished search whose result cannot be set beside SkillOpt's.

**What survives from it.** The memorisation finding
([its own entry](2026-08-27-gepa-found-the-answer-key-and-wrote-it-into-the-skill.md))
is an observation about what an evolved body *contained* — a transcription of
`rel-005-security-patch.yaml`'s solution expression and its high-strength
distractor. That a search found the answer key does not become untrue because
the reflector changed. Whether the new run's winner does it again is now a thing
to watch rather than a thing established, and it is worth watching: if a second
reflector produces the same memorisation, that is a much stronger claim than one
run could support.

**Prediction 4 gains a companion, registered before the run.** The winners of
these two searches will be compared against each other for *shared* memorised
content. I expect some, because the pressure comes from the corpus rather than
from the reflector. Confidence: moderate.

**One thing this exposes about the instrument, recorded rather than fixed.** The
wall-clock guard is charged in `DecisionAdapter.score`, which only runs when the
*target* is called. A reflector that hangs spends no target calls, so
`max_seconds` cannot fire and the run waits indefinitely. Every published guard
in this repository has the same shape. It did not bite here because a monitor
caught it, and a guard that depends on somebody watching is not a guard.
