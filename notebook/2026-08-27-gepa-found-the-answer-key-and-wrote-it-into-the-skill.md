# 2026-08-27 — GEPA found the answer key and wrote it into the skill

Outcome of [the prediction registered yesterday](2026-08-26-prediction-two-engines-on-a-matched-budget.md).
GEPA's half. SkillOpt is still running.

## The registered numbers

Target `ollama/qwen3:1.7b`, reflector `nvbuild/openai/gpt-oss-120b`, 70 training
items, 21 validation items, 300 target calls, 8,192-token cap.

Fourteen distinct candidates. Seven were scored on the whole validation pool, and
those seven are the only ones that can be compared with each other:

| generation | candidate | validation, 21 items |
| --- | --- | --- |
| 3 | `d74de503` | **0.857** |
| 2 | `0c34719c` | 0.810 |
| 4 | `6e6ac9ce` | 0.810 |
| 9 | `60375720` | 0.810 |
| 6 | `fb46ff7d` | 0.762 |
| 11 | `85a6816c` | 0.762 |
| 0 | seed skill | 0.714 |

**Prediction 1 holds**: fourteen candidates against a floor of three.
**Prediction 2 holds**: +14.3 points against a bar of 3.

Eighteen of 21 against fifteen of 21 is a three-item difference on 21 items. It
is not significant and was never going to be; the prediction set the bar low on
purpose because 21 validation items cannot support a claim about anything.

## What the winning body actually says

It is 1,656 words against the seed's 612. Section 5 is titled *"Domain‑specific
facts you must always respect"* and contains this:

> **Organisation standing policy threshold** … This is the **primary rule**
> unless the organisation explicitly states it follows the vendor guidance.
>
> **Vendor guidance threshold** … Consider *only if* the organisation has
> *adopted* that guidance.
>
> **Conflict resolution rule:** … The decisive fact is therefore the applicable
> out‑of‑band threshold (policy vs vendor) compared to the vulnerability's
> severity.

Here is `datasets/templates/rel-005-security-patch.yaml`:

```yaml
solution:
  expr: "'patch_immediately' if severity >= emergency_at else 'schedule_patch'"
  load_bearing: [r1, r2]

distractor_facts:
  - id: d2
    strength: high
    collides_with: emergency_at
    text: "The vendor's own guidance recommends out-of-band patching at
           {vendor_at} or above, which this organisation has not adopted."
```

The evolved skill is a transcription of the solution expression and the
distractor designed to defeat it. Not a paraphrase of the reasoning — the rule
itself, and the specific trap, named.

It also asserts that security vulnerabilities are *"the most common use‑case of
this tool"*. That is true of one template in the training sample and of nothing
else.

**The gain is real and it is not decision quality.** The skill scores better
because it carries the answer key for a template it saw, and it will keep
scoring better for exactly as long as that template is in the test set.

Section 1 is the same phenomenon a level up: the body opens by reciting the
harness's prompt format — *"Each user request will always follow the exact
template below"*, *"must output exactly one of these strings, unchanged"*. That
part is arguably fair, since format compliance is scored in every arm. Section 5
is not.

## This breaks Phase 3 as designed, and that is the finding

The plan's test set is *"a freshly minted frozen holdout (seeds ≥ 10000),
generated after winners are frozen, never touched by either engine"*.

A holdout at seeds ≥ 10000 draws **the same ten templates** with different
variable values. `severity` and `emergency_at` are redrawn; the rule relating
them is not, because the rule *is* the template. So a skill that memorised
`severity >= emergency_at` transfers to the holdout at full strength.

**The planned holdout would have scored memorisation as generalisation**, and
the study would have reported that evolved skills survive controls on fresh
items. The items would have been fresh. The answer key would not have been.

A seed-held-out split tests robustness to new variable draws. It cannot test
what this study was built to ask. What is needed is a **template**-held-out
split: some templates reserved entirely, never generated at any seed for either
engine, so that a winner meets decision problems whose rules it has never been
shown.

Ten templates is not many to split. Seven train and three test is a small test
set; the alternative is a bigger corpus, and that is a real cost this repository
has not paid yet. Either way the seed split alone is not the control the plan
believed it was.

Prediction 4 said neither winner would generalise. It is now clear that the
planned experiment could not have detected the failure it predicted.

## Three defects in the harness, found by the run

**A budget that stopped a search destroyed it.** The 300-call cap fired
mid-proposal, `BudgetError` left `de evolve`, and fourteen candidates and 287
records sat on disk with nothing pointing at them. The cap still stops the run.
The search now survives it, and `winner.json` records `winner_source`, because
when the engine did not declare a winner the choice was ours and a study citing
the body has to be able to tell.

**The lineage score is the wrong number to rank on.** It records the *first*
score a candidate got, and for GEPA that is a three-item minibatch. Ranking on
it compares 1.000-of-3 against 0.714-of-21 and selects noise. Only candidates
scored on every validation item are ranked now, and a partial pass is not ranked
lower — it is an answer to a different question.

**`train_size` is required in practice.** SkillOpt reads it with `.get` and a
zero fallback, then infers from a dataloader; this adapter has none by design,
so the fallback raises. The required-key test scanned bracket-reads only. It
checks all fifteen now.

## Two things I did wrong

**A waiter that could only see success.** `until [ -f winner.md ]` polled for a
file that the crash guaranteed would never appear, for seven and a half hours,
while the run had finished. A watcher whose filter matches only the happy path
cannot distinguish a crash from work in progress.

**Two runs on one checkpoint.** A foreground run outlived the tool timeout that
appeared to end it, and a second was launched on top. Two processes made
concurrent calls to a venue this repository has *measured* as unsafe under
concurrency, into one checkpoint. It survived — 287 lines, all parseable, one
duplicate key that the resume key deduplicates — and surviving is not the same
as being safe. The liveness check that missed it used `pgrep`, which does not
see Windows processes from this shell.

## The instrument settings this ran under

The 8,192-token cap, [registered as an amendment](2026-08-26-prediction-two-engines-on-a-matched-budget.md)
before any scored comparison, held: no record exceeded it, and 8 of 287 reached
it. Those eight are runaways that would each have cost around five minutes
uncapped.

Runaway rate is worth its own line. Unaided, this target violated the format on 2.4%
of items. Under a skill it is far higher — the first fourteen calls of the seed
candidate produced three capped generations. **A skill in the prompt makes this
model ramble**, and that is a cost of skills on small models that none of the
literature surveyed reports.
