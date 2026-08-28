# 2026-08-28 — What makes an item hard survives a capability jump, and arithmetic does not

The five-arm study is scoped to `ollama/qwen3:1.7b` and emits no verdict,
because `arenas.py` registers `ollama` as `dev`. The screen that followed found
every NVIDIA Build model measured solving the corpus with an empty prompt, the
weakest at 0.933. So a verdict needs a harder corpus.

Before building one, the question worth answering: what actually makes an item
hard, and does it stay hard when the model gets better? Two guesses were
available and one of them was mine.

## Margin does nothing

The obvious guess: these are threshold comparisons, so items whose two sides sit
close together should be harder. Computed the relative margin for all 728 items
the study scored and crossed it with the `off` arm.

| margin | items | `off` accuracy |
| --- | --- | --- |
| 0.00 to 0.02 | 35 | 0.857 |
| 0.02 to 0.05 | 56 | 0.696 |
| 0.05 to 0.10 | 84 | 0.750 |
| 0.10 to 0.25 | 217 | 0.673 |
| over 0.25 | 336 | 0.693 |

Flat, and the tightest band is nominally the easiest. **Margin is not a lever.**
It would not have worked on a larger model either: tight margins defeat
estimation, and these models compute.

## Distractors do, mildly

Same records, the existing strata:

| distractors | items | `off` accuracy |
| --- | --- | --- |
| 0 | 104 | 0.798 |
| 1 | 312 | 0.708 |
| 4 | 312 | 0.663 |

Monotone, 13 points across the range. Real, and too small on its own to move a
model from 0.93 to 0.70.

## The template is the whole story

The same 728 records, split by template:

| template | `off` accuracy |
| --- | --- |
| `rel-007-capacity-scale` | 1.000 |
| `rel-010-loan-review` | 0.964 |
| `rel-002-deploy-window` | 0.821 |
| `rel-008-contract-renew` | 0.768 |
| `rel-001-vendor-outage` | 0.741 |
| `rel-006-refund-request` | 0.607 |
| `rel-003-oncall-escalate` | 0.589 |
| `rel-005-security-patch` | 0.554 |
| `rel-004-inventory-reorder` | 0.536 |
| `rel-009-flight-rebook` | 0.491 |

A range from chance to perfect inside one corpus that was built to be uniform.

And it is not arithmetic. `capacity-scale` needs a percentage applied to a
forecast and scores 1.000. `flight-rebook` is a bare comparison of two stated
minute counts and scores 0.491.

## Which of it survives a better model

94 calls on `nvbuild/nvidia/nemotron-3-nano-30b-a3b`, no skill, the
four-distractor stratum, accuracy over calls that answered.

| template | 1.7B | 30B |
| --- | --- | --- |
| `rel-009-flight-rebook` | 0.491 | 0.636 |
| `rel-006-refund-request` | 0.607 | 0.667 |
| `rel-002-deploy-window` | 0.821 | 0.833 |
| `rel-004-inventory-reorder` | 0.536 | 1.000 |
| `rel-005-security-patch` | 0.554 | 1.000 |
| `rel-003-oncall-escalate` | 0.589 | 1.000 |
| the other four | 0.74 to 1.00 | 1.000 |

Overall 86 of 94, which is 0.915 and agrees with the 0.967 the ceiling screen
read on 30 items.

**Three templates that are hard for the small model become perfect on the larger
one, and two stay hard.** That split is the finding. Difficulty that comes from
arithmetic or from pulling three numbers out of prose is a statement about model
capability and it evaporates. Difficulty that comes from working out *which
comparison the policy is asking for* does not.

## What separates the two survivors

Compare the policy fact of a template that collapsed with one that held.

`rel-003-oncall-escalate`, 1.000 on the 30B:

> The escalation policy triggers when more than {threshold_pct}% of requests are
> affected.

`rel-006-refund-request`, 0.667:

> The published refund window is {window_days} days from delivery.

The first is an explicit conditional: a trigger, a comparator and a threshold in
one sentence. The second is a fact, and the reader has to supply the rule that
turns it into a decision. `rel-009-flight-rebook` goes further, stating the rule
through a protection clause the reader must invert, next to a real-world prior
that argues the other way.

So the lever is **whether the decision rule arrives as a stated conditional or
has to be constructed**, plus whether an everyday prior cuts against the
constructed answer.

## What this predicts, before the corpus is built

Registering these now.

1. **A template set built on constructed rules rather than stated conditionals
   puts a 30B model near 0.7**, the band `rel-009` and `rel-006` already sit in,
   and well under the 0.90 that makes a study pointless.
2. **The same set stays above chance for `qwen3:1.7b`.** If it does not, the
   corpus has become a coin flip for the small model and the two venues can no
   longer be compared on it.
3. **Adding arithmetic will not help and may hurt.** Three templates say
   arithmetic difficulty does not survive, and it costs small-model accuracy,
   which prediction 2 needs.
4. **Distractors stay worth their 13 points** and are kept at four, but they are
   not the mechanism and will not be asked to carry the drop.

## What this does not settle

The 30B numbers rest on 6 to 12 answered calls per template, because the free
tier rate-limited about a fifth of them. The extremes are clear and the middle
of that table is not, and nothing here should be read as ordering
`deploy-window` against `vendor-outage`.

One thing measured that contradicts a document here: an earlier entry called a
corpus change "a governed path". It is not. `GOVERNED` in `decisions.py` is
`datasets/triggers/`, `datasets/tailoring/`, `skills/` and `arenas.py`.
`datasets/templates/` is none of them, so a template change needs no
`DECISIONS.md` entry. It does need `pytest --bless`, because `datasets/golden/`
pins the generated corpus byte-exact.
