# 2026-08-28 — Policy selection is the lever, and it costs the small model

Hypothesis 1 said a rule stated as a fact rather than a conditional would make a
capable model work. `hrd-001-warranty-claim` was built to it and a 30B scored 24
of 24. That entry is corrected
[there](2026-08-28-what-makes-an-item-hard-survives-a-capability-jump-and-arithmetic-does-not.md).

Hypothesis 2 was next on the list: two policies and a precedence rule, so the
model has to work out which rule is in force before it can compare anything.

## The template

`hrd-002-shipping-escalation`. A contract tier decides whether the standard or
the priority grace period applies, both are stated plainly as rules, and the
comparison itself is a single integer test. Nothing is spent on arithmetic,
because arithmetic difficulty was measured not to survive a capability jump.

Two properties are enforced by constraint rather than hoped for:

- The two grace periods differ.
- **They disagree about this consignment.** Without that line the policies
  usually sit on the same side of the delay, both readings give the same answer,
  and picking the wrong one costs nothing. Measured at 0.21 before the
  constraint and 1.00 after, so four items in five had not been testing
  selection at all.

Answers come out 84 to 84 across six seeds.

## What it scores

36 items, four-distractor stratum, three seeds, arm `off`, no skill.

| model | correct | accuracy | 95% CI |
| --- | --- | --- | --- |
| `nvbuild/nvidia/nemotron-3-nano-30b-a3b` | 23/36 | **0.639** | [0.48, 0.78] |
| `ollama/qwen3:1.7b` | 18/36 | **0.500** | [0.34, 0.66] |

For comparison, on the same stratum and sample size: `hrd-001` reads 1.000 on
the 30B and 0.889 on the 1.7B, and the hardest published template reads 0.833 on
the 30B.

**Hypothesis 2 holds.** Policy selection drops a 30B from 0.83 to 0.64, which is
the band a five-arm study needs and which no amount of rewording reached.

## And it falsifies prediction 2

The earlier entry registered: *the same set stays above chance for
`qwen3:1.7b`; if it does not, the corpus has become a coin flip for the small
model and the two venues can no longer be compared on it.*

The 1.7B scored 18 of 36. That is chance, to the item.

So the prediction is falsified and the consequence it named is real. This is not
a defect in the template. It is the shape of the design space: difficulty here
is close to monotone in capability, so a corpus with headroom for a 30B has none
for a 1.7B.

## The blend, computed rather than chosen

Mixing the two templates in a corpus moves both numbers together. From the four
measurements above:

| share of `hrd-002` | 30B | 1.7B |
| --- | --- | --- |
| 0.00 | 1.000 | 0.889 |
| 0.50 | 0.820 | 0.695 |
| 0.75 | 0.729 | 0.597 |
| 0.80 | 0.711 | 0.578 |
| 1.00 | 0.639 | 0.500 |

A corpus that is three quarters selection items puts a 30B at about 0.73 and
leaves the 1.7B at about 0.60. That is a screen-tier corpus with the small model
still above chance, and it is the first configuration measured here that could
carry a verdict.

The arithmetic assumes the blend is linear in the mix, which it is by
construction, and that these two templates stand in for their kinds, which is
the part that is not yet shown.

## What is not done

One template of each kind is not a corpus. The five-arm study's own result is
that both engines memorised template-level decision rules, so a corpus of one
scenario measures memorisation and nothing else. A screen-tier corpus needs
six to eight selection templates over different domains before it is worth
registering anything against.

The two numbers each rest on 36 items with intervals about 0.30 wide. They
separate 0.64 from 1.000 and they do not pin 0.64 against 0.70.

## Predictions for the next run

1. **Six more selection templates land the 30B between 0.60 and 0.75 as a set.**
   Two instances is not a rate, and the failure mode is a template whose
   selection cue turns out easy for reasons its author did not see.
2. **The 1.7B lands between 0.50 and 0.60 on that set**, which the blend
   arithmetic requires and which decides whether a mixed corpus is worth
   building at all.
3. **Adding distractors past four does not move either**, since distractors were
   worth 13 points across their whole range and selection is worth 19 on its
   own.
