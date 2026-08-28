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

Skew here is signed toward whichever option sorts first, which is the
convention the later table drops in favour of signing toward the act.

| template | accuracy | skew | toward |
| --- | --- | --- | --- |
| `rel-004-inventory-reorder` | 0.857 | −0.143 | `reorder_now` |
| `rel-002-deploy-window` | 0.917 | −0.083 | `hold_deploy` |
| the other seven | 1.000 | +0.000 | — |

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


## Correction, same day: prediction 3 is falsified, and it names the lever

Prediction 3 registered: *reversing which option is stated first in `hrd-002`
moves its accuracy by more than 0.10*, as the cheap test of whether the bias is
about the option or about the scenario.

`hrd-009-shipping-escalation-reversed` is `hrd-002` with the question clause and
the options list both stated the other way round and nothing else touched. Same
model, same arm, four distractors, two seeds, run against `hrd-002` at the same
time so the comparison is not against an older reading.

| | `hrd-002` | `hrd-009`, reversed |
| --- | --- | --- |
| accuracy | 14/24 = 0.583 | 15/24 = 0.625 |
| when the answer is `expedite` | 1.000 | 1.000 |
| when the answer is `leave_standard` | 0.167 | 0.250 |
| said `expedite` | 0.917 | 0.875 |
| skew | +0.417 | +0.375 |

The move is 0.042 and the registered threshold was 0.10, so the prediction is
falsified. Stating `leave_standard` first buys nothing.

**The bias is semantic.** It is now measured three times on this item type, at
0.629, 0.583 and 0.625, and every one of them answers `expedite` on about nine
items in ten while getting every `expedite` item right. An overdue shipment
reads as calling for action, and the model acts.

The obvious next sentence is that this names the difference between `hrd-002`
and the five that ceiling. `hrd-002` asks whether to **act or leave it alone**:
`expedite` is an act and `leave_standard` is a refusal to act. `hrd-003` through
`hrd-008` ask which of two acts applies, return or withhold, clear or hold,
grant or refuse, and a model that defaults to doing something has nowhere to put
that default.

The published corpus can check that sentence rather than accept it. Six of its
ten templates are act-or-wait pairs and three offer two acts, and the skews are
already computed. Signed toward the acting option, on `qwen3:1.7b`, arm `off`:

| shape | templates | mean signed skew | mean absolute skew |
| --- | --- | --- | --- |
| act or wait | 6 | +0.097 | 0.127 |
| two acts | 3 | +0.065 | 0.172 |

**It does not hold.** Act-or-wait templates lean toward acting by 0.097, which
is the right sign and is carried almost entirely by
`rel-004-inventory-reorder` at +0.464; drop that one and the remaining five
average +0.024. The two-act templates are not less skewed, they are more, and
`rel-006-refund-request` skews +0.321 with both options being decisions a person
makes.

So the `hrd-002` result stands and the explanation for it does not. Three
measurements agree that this scenario pulls a 30B toward `expedite` and that
option order is not why. Whether the pull is about acting, about shipping, or
about this template's wording is open, and the corpus that would separate them
is on a different model from the one the pull was measured on.

The instrument spec keeps its three measured lines. A fourth is a hypothesis and
gets written as one:

- accuracy below the ceiling,
- skew near zero,
- informedness below one,
- and possibly, untested, that both options should be acts.

`hrd-009` stays in the tree beside `hrd-002` as the measured control.

### Predictions

1. **A symmetric-option rewrite of the `hrd-002` scenario keeps skew above
   0.25.** The action account says the skew comes from the act-or-wait pairing
   and would fall; the published corpus says it does not work that way. This is
   the run that separates them, and it is about twenty-four calls.
2. **An arm that improves accuracy on `hrd-002` does it by moving skew and not
   informedness.** That is the whole worry this entry started from, it is about
   fifty calls across `off` and `placebo`, and a placebo that gains on a biased
   template is the cleanest demonstration this repository could publish of why
   accuracy alone is the wrong headline.


## Correction, same day: prediction 2 is falsified, and it had no case to test

Prediction 2 registered: *an arm that improves accuracy on `hrd-002` does it by
moving skew and not informedness*, on the reasoning that a template scoring 0.63
by preference offers about thirty points to a prompt that only shifts the
preference.

Three arms over the same 36 items, `nemotron-3-nano-30b-a3b`, four distractors,
three seeds. Counts differ because a few calls failed their three tries.

| arm | n | accuracy | skew | informedness |
| --- | --- | --- | --- | --- |
| `off` | 36 | 0.694 | +0.306 | 0.389 |
| `placebo` | 33 | 0.697 | +0.303 | 0.375 |
| `on` | 35 | 0.600 | +0.171 | 0.190 |

Paired against `off` on the items both answered, one-sided McNemar, and
bootstrap intervals over items at 20000 draws:

| | Δ accuracy | Δ informedness | Δ \|skew\| | p |
| --- | --- | --- | --- | --- |
| `placebo` | +0.003 [−0.091, +0.000] | −0.062 [−0.211, +0.000] | +0.030 | 1.0000 |
| `on` | −0.114 [−0.257, +0.029] | −0.222 [−0.533, +0.080] | −0.114 | 0.9648 |

**No arm improved accuracy, so the prediction's premise never occurred.** The
placebo moved nothing on any of the three numbers, which is the behaviour a
placebo should have and which the five-arm study did not get on the published
corpus.

The seed skill did the interesting thing and did it in the losing direction. It
cut skew from +0.306 to +0.171, so it genuinely made the model act less, and it
cut informedness from 0.389 to 0.190 at the same time. Trading discrimination
for a smaller lean is a net loss on a balanced key, and that is what the 0.094
accuracy drop is.

Every interval here crosses zero at these counts, so the ordering is what this
run supports and the sizes are not. Thirty-six items was chosen to answer a
question about a thirty-point gap and is far too few for a ten-point one.

The worry that started this entry is therefore unresolved rather than answered.
Nothing here shows an arm buying accuracy with bias, and nothing here had the
power to see it.
