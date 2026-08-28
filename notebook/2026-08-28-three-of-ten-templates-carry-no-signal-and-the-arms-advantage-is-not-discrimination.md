# Three of ten templates carry no signal, and no arm's advantage is discrimination

**2026-08-28.** Follows the `hrd-002` diagnosis in
[the policy-selection entry](2026-08-28-policy-selection-is-the-lever-and-it-costs-the-small-model.md),
which found that the one template keeping a 30B off the ceiling does it by
answering one option most of the time. That raised a question about the
published five-arm study rather than about the hard corpus, and the records to
answer it were already on disk.

No model calls. Everything here is recomputed from
`results/evolution-study/2026-08-27-53b4965-five-arm/records-*.jsonl`, which
carry `expected` and `parsed` on every row, so the model's own answer rate can
be compared with the rate the items called for. The same files `analysis.json`
was computed from, read a second way.

## The measure

Accuracy on a balanced two-option key adds together two different things: how
well a model tells the cases apart, and how often it picks one option whatever
the case. Signal detection separates them. Informedness, sensitivity plus
specificity minus one, is zero for any constant-answer policy at any base rate
and is unmoved by a pure shift in preference. Skew, the model's rate for an
option minus the rate the items wanted it, names the other half directly.

Computed per template, because which option counts as positive is a
per-template fact, then averaged over templates so no template's item count
decides the answer. Over parsed rows only, which is a caveat below.

## The arms

| arm | parse rate | accuracy | mean J | ΔJ vs `off` | 95% cluster CI |
| --- | --- | --- | --- | --- | --- |
| `off` | 0.946 | 0.702 | 0.514 | — | — |
| `on` | 0.951 | 0.712 | 0.495 | −0.019 | [−0.095, +0.065] |
| `placebo` | 0.934 | 0.731 | 0.545 | +0.031 | [−0.019, +0.086] |
| `gepa` | 0.918 | 0.706 | 0.522 | +0.007 | [−0.144, +0.135] |
| `skillopt` | 0.962 | 0.761 | 0.594 | +0.080 | [−0.069, +0.260] |

Intervals from resampling templates, which are the cluster the study's own
analysis uses, 20000 draws. Ten clusters is few, so the intervals are wide and
they are the width this design supports.

**The study's conclusion survives the correction, and gets a little stronger.**
Every arm's discrimination advantage over an empty prompt has an interval
containing zero, exactly as every accuracy comparison did after Holm. SkillOpt
keeps first place on both measures and its ΔJ of +0.080 is the largest, so its
accuracy lead survives the correction. Its interval still contains zero.

Two things this does not say. Mean skew is 0.125 to 0.193 in *every* arm
including the empty prompt, so response bias is a property of the model on this
corpus rather than something an arm introduced. And J is computed over parsed
rows, so `gepa`, which parses least at 0.918, is measured on the subset it
managed to answer; its interval is the widest here and that is part of why.

## Three templates are not measuring anything

| template | `off` | `on` | `placebo` | `gepa` | `skillopt` |
| --- | --- | --- | --- | --- | --- |
| `rel-004-inventory-reorder` | +0.071 | +0.168 | +0.089 | +0.071 | +0.005 |
| `rel-006-refund-request` | +0.271 | +0.192 | +0.198 | +0.212 | +0.125 |
| `rel-009-flight-rebook` | +0.028 | −0.072 | +0.042 | +0.044 | −0.024 |

Three of ten templates sit below J = 0.3 in all five arms, and two of them are
indistinguishable from zero. On those items `qwen3:1.7b` is not deciding. Their
contribution to a 0.70 headline is the base rate and the direction the model
happens to lean, and `rel-009-flight-rebook` is the template an earlier entry
called the hardest in the corpus. It is not hard. It is unanswered.

Templates here mint either 56 or 112 items, and the three low-signal ones carry
224 between them, so a 728-item run carries the discriminative signal of the
other **504**. The power calculation behind the study assumed 728. That does not change a result
that failed to reject, since less power only makes rejection harder, but it
would matter to any run designed off those numbers.

`rel-006-refund-request` is worth naming twice: it is one of the two templates
whose 30B accuracy an earlier correction re-measured from 0.667 up to 0.853. It
is low-signal on the small model and ceilinged on the large one.

## The same split on the 30B, which arrived before it could be predicted

Ran it on `nemotron-3-nano-30b-a3b`, no skill, four distractors, seed 1000, 120
calls. It is on the record here rather than as a prediction because the numbers
came back while this entry was being written, and a prediction registered
against data already in hand is not one.

| template | accuracy | skew |
| --- | --- | --- |
| `rel-004-inventory-reorder` | 0.857 | −0.143 |
| `rel-002-deploy-window` | 0.917 | −0.083 |
| the other seven | 1.000 | +0.000 |

`rel-004` is the one template that is both low-signal on the small model and off
the ceiling on the large one, and it leans the same way on both: 0.667 on the
items wanting the first option against 1.000 on the rest. `rel-009`, near zero
informedness on the 1.7B, is a flat 1.000 here and so says nothing either way.

Weak evidence, and the weakness is worth stating. One seed gives about twelve
items per template, `rel-006` produced no four-distractor items at that seed and
is missing from the table, and `rel-005` and `rel-010` drew a single answer
class so their skew is undefined rather than zero. It is enough to say `rel-004`
leans on both models and not enough to say more.

## What this changes about building a harder corpus

The target was "accuracy below the ceiling", which `hrd-002` met while measuring
a preference. Three numbers replace it, all computable from records already
kept:

- accuracy below the ceiling,
- skew near zero, so the model is answering from the item,
- informedness below one, so discrimination is left to gain.

Every published template fails one of these on one of the two models. Seven of
ten are at J near 1 for the 30B and have no room; three are near J = 0 for the
1.7B and have no signal. `hrd-002` has room and no signal. `hrd-003` through
`hrd-008` have signal and no room.

That is a narrower gap than "make it harder" and it explains why three designed
templates in a row missed. Difficulty was the target and difficulty is the
confounded quantity.

## Predictions

1. **A template built to hold skew under 0.10 while keeping 30B accuracy under
   0.90 will take more than one attempt.** Three attempts have produced two
   ceilings and one bias, and nothing yet shows the region is non-empty for
   these item types.
2. **`rel-004`'s lean holds at three seeds and stays under 0.90 on the 30B.**
   The reading above rests on seven items of one class and is the only published
   template with room on both models, so it is either the corpus's one usable
   item type or a single-seed accident.
3. **Reversing which option is stated first in `hrd-002` moves its accuracy by
   more than 0.10**, which is the cheap test of whether the bias is about the
   option or about the scenario, and which no design should have been built
   before running.
