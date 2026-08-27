# 2026-08-26 — Two defaults that could not run, and a sample that measured one seventh of the corpus

Second entry today. The first recorded four ways to report a search that never
happened; this one records the second engine getting its driver, and three more
defects, one of which was mine and was found by reading item identifiers rather
than by any check.

No prediction is registered here and no number below is a result.

## SkillOpt has a driver now

`de evolve --engine skillopt` runs. What was missing was never the environment —
that landed yesterday — but the flat config `ReflACTTrainer` reads, and the
reason for not guessing at it was that a run under settings nobody chose is not
a comparison.

It did not need guessing. `skillopt/config.py` carries an eighty-entry
`_FLATTEN_MAP` naming every structured key and its flat spelling, and the
trainer reads fourteen keys as `cfg["x"]` rather than `cfg.get("x", ...)`:
`out_root`, `optimizer_model`, `target_model`, `skill_init`, `batch_size`,
`num_epochs`, `accumulation`, `seed`, `merge_batch_size`, `edit_budget`,
`sel_env_num`, `analyst_workers`, `eval_test`, `test_env_num`. A missing one is
a `KeyError` partway into a search that has already spent its calls. All
fourteen are supplied and everything else is left to the engine's defaults.

The test that guards it reads the required set out of the installed trainer's
source and diffs it against what `train_config` produces, so a version bump
fails in the suite rather than mid-run. A pinned list of names would pass
forever and stop being true the first time SkillOpt requires a fifteenth.

**Its splits are ALFWorld's, because that is what it was written against.**
`valid_seen` is the acceptance gate and maps to the validation pool.
`valid_unseen` is its held-out test and is refused: the holdout for this study
is minted after the winners are frozen, and serving validation items under a
name meaning "test" would put a number in the engine's own `summary.json` that
reads like a held-out result. `eval_test` is `False` so a run never asks. The
refusal is the backstop, not the control.

One correction to yesterday's entry, which said the router knows three backends
and none is OpenAI-compatible. That is right, and there is more to it:
`qwen_backend.py` is a complete OpenAI-compatible backend that
`router.get_backend` will not dispatch to — `assert_valid` refuses anything
outside `{azure_openai, codex, claude}` — and it is reachable only through
`get_target_client`, which checks `get_target_backend() == "qwen_chat"` behind
the router's back. We do not use that path. `azure_openai` with
`auth_mode: openai_compatible` is simpler, applies to both roles, and is what
`venue_config` writes.

## The default validation seed could not be generated

`EvolveRequest.val_seeds` defaulted to `(1000, 1001)`. Seed 1001 cannot be
generated at all: `rel-008-contract-renew` fails to produce a robust,
discriminative `renew` in 500 attempts, and the generator raises rather than
returning a short corpus.

So the default request crashed on first contact with a real venue, and it had
never been noticed because every smoke run so far passed its own seeds — the
CLI's default `--val-seeds` is `1000` alone. A default nothing exercises is a
default nobody has run.

Roughly one seed in sixty does this and it is always that template: one failure
in the sixty seeds from 10000 to 10059, at 10034. That number is a Phase 3 input
rather than trivia, because the holdout is minted from that range and a seed
that cannot be generated has to be skipped. **Skipping is not free.** Dropping a
seed conditions the corpus on `rel-008` being generable there, which truncates
that template's variable distribution at the seeds that survive. It is small and
it is not nothing, and it should be decided deliberately when the holdout is
minted rather than by whatever the minting loop happens to do.

## The headroom probe measured one seventh of the corpus

This one was mine, it produced a clean run and a plausible number, and it is the
same shape as everything else in this repository's ledger.

The probe answers whether `qwen3:4b` has room to improve before a search spends
hours on a target that is already at its ceiling. It sampled 40 of the 280 items
at one seed with `items[::7]`.

A template contributes 28 items: four variants crossed with seven strata —
`d0-none`, `d1-early`, `d1-middle`, `d1-late`, `d4-early`, `d4-middle`,
`d4-late` — in that fixed order. The period is 7. So a stride of 7 starting at
index 0 draws `d0-none` **forty times out of forty**: zero distractors, the
easiest stratum, one seventh of the corpus.

It reported 0.868 for the unaided arm. That number is correct about the object
it measured, and the object was not the corpus. Read as a headroom check it says
there is almost no room to improve, which would have argued for abandoning
`qwen3:4b` as the target on the strength of a sample containing none of the hard
items.

Found by reading item identifiers in a debugging print, not by a check. Nothing
in the harness could have caught it: the sample was a list of valid items, every
call succeeded, and the aggregate was arithmetically right.

The probe now draws evenly across strata and prints the per-stratum breakdown
beside the aggregate, because an aggregate that hides a stratum is exactly how
this stayed invisible. Six per stratum, forty-two items, six of ten templates.

## What the arithmetic says about the study

Measured on this machine: 26 s median per call, 33 s mean, 84 s at the tail,
against `ollama/qwen3:4b` serial. Serial is not a choice — `CONCURRENCY_UNSAFE`
registers the `ollama` prefix on the 2026-08-19 falsifier, which found a
batching server changing every one of 40 answers.

`de power`, one-sided, alpha 0.05, power 0.8, McNemar pairs:

| pairs | MDE at p_d=0.20 |
| --- | --- |
| 100 | 11.0 points |
| 233 | 7.3 points |
| 527 | 4.8 points |

Five arms over 100 items is 500 calls, about 4.6 hours, and buys a minimum
detectable effect of eleven points. Over 500 items it is 2,500 calls, roughly a
day of wall clock, for under five points.

That is the real budget of this study and it is wall clock rather than money.
Both venues bill nothing, which is why `BudgetLedger` refuses a ledger that
carries only a dollar cap.

## And `--limit` drew twenty items from one template

Found by reading the probe's own lesson back into the harness, which is the only
reason it was found at all.

`items_for` sliced the flattened corpus. A seed's corpus is template-major: ten
templates of 28. So `--limit 20` returned twenty items from
`rel-001-vendor-outage` and nothing else, while `run.json` recorded a corpus of
ten scenarios and a search run against it would have optimised for vendor
outages. Every smoke run on record went through that path, including the
four-candidate lineage in this morning's entry.

The obvious fix — one item from each template — is wrong for the same reason the
probe was. A template's 28 items are variant-major and stratum-minor, so the
first item of each template is `d0-none` every time: ten templates, one stratum,
the easiest one. Striding instead gives a stride of `28 // per`, usually a
multiple of seven, which draws the same stratum just as reliably. Three ways to
build this corpus and two of them are the same defect.

What it does now is rotate: template `t` starts at stratum `t`. Seven items span
seven strata, ten span ten templates and seven strata, and asking for all 280
through the limited path returns all 280 exactly once — which is the property
that makes it a permutation rather than a resample, and a resample would weight
an item twice in a paired test.

**Three instances in one day, all the same shape.** A full checkpoint, a clean
exit, an aggregate that is arithmetically correct about an object nobody meant
to measure. None of the three was caught by a check; the first was caught by
reading item identifiers, and the second and third by asking where else the same
mistake could be hiding.

## The target selection rule, written before the numbers exist

The balanced probe is returning a high unaided accuracy, which inverts what the
plan assumed. It said that if `qwen3:4b` ceilings on this corpus the target
should move **up**, to `qwen3:8b` or a hosted model. The direction is wrong: a
target at its ceiling leaves nothing for a skill to add, and the fix is a weaker
model, not a stronger one.

`qwen3:1.7b` and `qwen3:0.6b` are pulling now. The same 42-item balanced probe
will run the `off` arm against each.

**The rule, registered here before those numbers exist:** the study's target is
whichever measured model's unaided accuracy on this probe falls closest to 0.50.
Not the lowest — a floored model has room in principle and reaches it by
learning to emit an answer line, which is a formatting result wearing a decision
result's clothes. Not the highest either, for the ceiling reason. McNemar's
minimum detectable effect is best near a half, and a target there has room to
move in both directions, which matters because a skill that makes things worse
is a finding this study should be able to see.

If no measured model lands between 0.35 and 0.65, that is reported as the
outcome and the study does not proceed on the least-bad option. A corpus and a
model range that cannot be made to disagree is worth knowing about and is not
worth spending a day of wall clock to dress up.

## The rule above is wrong, and here is the correction

It stays as written because that is what this notebook is for.

**Every item in this corpus is a two-option choice.** 280 of 280, at every
stratum: `n_distractors` adds *facts* — three, four, seven — and never adds an
option. So chance is 0.500 and the usable range is 0.500 to 1.000.

The rule said to pick the model closest to 0.50. It was written thinking 0.50
was the middle of the range. It is the floor. Applied as written, the rule
selects the model that is **exactly at chance** — one that has learned nothing
about the task, where every apparent improvement is noise and no skill could
demonstrate anything.

That is not a subtle error. It is the same error as the rest of today: a number
that is right about an object nobody checked, in this case the option count.

**The corrected rule:** the target sits near the midpoint of the *usable* range,
0.75, and has to be significantly above chance. Below chance-plus-noise there is
no behaviour to improve; near 1.0 there is no room to improve it.

## The measured table, and the target

Unaided, on the balanced 42-item probe at seed 0. `z` is against a chance
baseline of 0.500.

| model | unaided | z vs chance | format violations | s/call | arena |
| --- | --- | --- | --- | --- | --- |
| `ollama/qwen3:4b` | 0.881 | 4.94 | 0.119 | 42.7 | dev |
| `ollama/qwen3:1.7b` | **0.762** | **3.40** | 0.024 | 12.1 | dev |
| `ollama/qwen3:0.6b` | 0.524 | 0.31 | 0.024 | 2.0 | dev |
| `nvbuild/google/gemma-3-4b-it` | — | — | — | — | screen |

**The target is `ollama/qwen3:1.7b`**, at 0.762 against a corrected optimum of
0.75. It is above chance by z=3.40, leaves 23.8 points of room, and runs 3.5
times faster than the 4B.

`qwen3:0.6b` is at chance and would have been chosen by the uncorrected rule.
`qwen3:4b` leaves 11.9 points, of which 11.9 are format violations — it is at
its ceiling on decisions and its remaining errors are the model reasoning past
the point where it emits an answer line.

Worth noting against the 4B: the two smaller models violate the format on 2.4%
of items and the 4B on 11.9%. More reasoning is not more compliance here.

## The gemma row is empty because the venue said 404

It reported 0.000 with 100% format violations and 0.0 s/call, and 0.0 s/call is
not a model being bad at anything.

```
integrate.api.nvidia.com/v1/chat/completions returned 404:
"Function '...': Not found for account '...'"
```

`/v1/models` lists 84 models. That is the **catalogue**, not what a key is
entitled to call, and the two are not the same list. `openai/gpt-oss-120b`
answers for this key and `google/gemma-3-4b-it` does not.

The harness caught this one: `zero_cause` is `infrastructure`, which is exactly
the field the 2026-08-19 entry added after a CUDA OOM was counted as a healthy
zero. A summary that reported the 0.000 without reading `zero_cause` would have
published "gemma-3-4b scores zero on decision tasks", which is a sentence about
an HTTP status.

Any `nvbuild/` model gets one smoke call before a run is built on it.

## Phase 3 needs a placebo it does not have

`skills/decision-making/placebo.md` is 628 words against the seed body's 612 and
passes `check_placebo_match` at a 15% tolerance. It is a fair control for the
seed skill arm and for nothing else.

An evolved winner will be whatever length the search made it. If GEPA returns
900 words, the 628-word placebo is 30% short of it, and an evolved arm beating
that placebo cannot be told apart from a length effect — which is the exact
confound the placebo arm exists to remove.

Three ways out, none free. Match a placebo to each winner, which means prose
written to not matter and `scripts/separability.py` says register separability is
the threat most likely to fire. Constrain the search to bodies within tolerance
of the seed, which distorts what the engines do. Or report arm lengths and scope
the claim, which is honest and weaker. This is a decision for Phase 3 and it is
recorded here so it is made deliberately rather than by whichever placebo
happens to be on disk.

## The holdout's provenance file is a way to leak the holdout

Found while sketching the minting path and worth writing down before anyone
writes that code.

A minted split needs a provenance record: which seeds were drawn, which were
skipped and why, how many items resulted. The obvious place is a sidecar beside
the split, and `.gitignore` line 29 covers `datasets/holdout/*.jsonl` and
nothing else. So `<name>.provenance.json` would be **committed** — and it would
carry the seeds, and the seeds regenerate the corpus exactly.

That is the entire split, reconstructible by anyone with the repository, in a
file added for the sake of rigour. `datasets/holdout/README.md` is explicit that
the split is the only uncontaminated data here and that contamination cannot be
undone within a seed.

So the seed list belongs in an ignored file, and what may be committed is the
part that identifies nothing: counts, the corpus fingerprint, a hash of the
passphrase to prove which one was used, and the skip *count* without the skipped
seeds. Whoever writes the minting code should widen the ignore rule in the same
change rather than after.

## What is still missing

**A reflector — now supplied.** `NVIDIA_API_KEY` was absent for most of today,
which would have forced a local 4B model to propose rewrites for itself. The
maintainer supplied a key, and `nvbuild/openai/gpt-oss-120b` answers and returns
a fenced block that GEPA's extractor reads. The planned configuration — local
target, hosted reflector — is available, so no run has to be reported under a
weaker one. `nvbuild/openai/` was already a registered prefix from Phase 0, so
this needs no `DECISIONS.md` entry.

The timing figures above are from the 4B, measured before the target moved. They
are kept because they are what the wall-clock arithmetic in this entry was
computed from; the target's own rate is 12.1 s/call and is in the table.

**The reasoning chain does not reach the record.** `CliResult` has carried a
`reasoning` field since the 2026-08-19 fix, and `runner.py` never reads it, so
`RunRecord` has no such column. On this model that is 3,600 tokens of chain
dropped per call: the records show `output_tokens=4205` against 581 characters
of stored response. The token count is honest and the chain is gone. Reflection
therefore sees what the model answered and not why, which handicaps both engines
identically and so does not confound the comparison — but it is a limit on the
evidence, and it is filed rather than fixed here because adding the column
touches the published record schema.
