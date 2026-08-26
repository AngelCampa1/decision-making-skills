# Family C v2: second-position rate as the primary

**Audience:** the evaluating reader.

**What this is.** The registered primary for the `council` order-effect
instrument, the rule that decides how a stated tie is scored, the gate that
decides when a directional claim may be published, the sample size the band
needs, and the scorer with the battery that gates it. Everything below is
computed by `council_primary.py` in this directory. It runs on a bare
interpreter, makes no model calls, and exits non-zero when the battery fails.

Three adversarial reviews stand behind this version. The first killed flip rate
and gave the design second-position rate. The second found that the repaired
design carried the same defect its two sibling instruments carry, one level up
from where they carry it, and the sections that follow are mostly its
consequences.

## The primary, in one sentence

Over every response record of one stratum **and one arm**, held to equal
committed counts per item per ordering by the balance trim, the
**second-position rate** is the count of records whose `CALL` block names the
course printed second in that record's own prompt, divided by the count of
records whose `CALL` block names either course, computed by `compute_primary`
and tested against an exact null of 0.5 by the two-sided binomial
`exact_two_sided_p`.

Estimator: `compute_primary(...).rate`. Denominator: committed records after the
per-item balance trim, reported as `Primary.committed`. Numerator:
`Primary.second`. Two arms are never pooled into one rate; `compute_primary`
raises when asked. The comparison between arms is `compare_arms`.

## Why the null is exactly 0.5, and what that buys

Write **a** for the course printed first under AB. A model whose answer depends
on content and not on print position names **a** with the same probability under
both orderings; call that probability α, conditional on committing. Under AB the
second-printed course is **b**, so the model names second with probability 1 − α.
Under BA the second-printed course is **a**, so it names second with probability
α. With r committed draws under each ordering of one item, the item's
second-position count has expectation r(1 − α) + rα = r, for every α.

**The conditional mean is free of α.** An item on which the model is 90% settled
and an item on which it is a coin flip contribute the same expectation. There is
no between-item variance component, so the pooled count over items is the right
object and the per-item clustering needs no correction.

**The variance sits below the reference.** Conditional on α the variance of the
item's count is 2r·α(1 − α), at most r/2, which is the variance of the
Binomial(2r, 0.5) the test is read against. Response noise and item
heterogeneity both shrink the statistic's spread below the reference, so the
exact binomial test is conservative and noise costs power while never
manufacturing an effect.

**The test is directional.** Above 0.5 is recency, below is primacy.

### The equal count per item does a second job nobody had credited it with

The same-order screen admits an item on four AB draws, which is a data-dependent
selection on exactly the quantity the AB half of the sample measures. In a
candidate population of six items at β = 0.05 and six at β = 0.60, where β is
the probability of naming the second-printed course under AB, admission weight
β⁴ + (1 − β)⁴ moves the AB half's expected rate from 0.325 to **0.138**. It
moves the BA half from 0.675 to **0.862**. The two cancel to 0.5000 exactly,
because the weight is symmetric in β ↔ 1 − β and under the null β_BA = 1 − β_AB
for every item.

The cancellation is bought by the equal count per item per ordering. Without it
the pooled rate is a commit-count-weighted average of two halves that are
biased in opposite directions, and the screen's bias leaks in at −0.037 for a
commit-count ratio of 1.5 and −0.062 at 2.0. So the trim is load-bearing twice:
for the α-freeness, and for the screen. **No per-ordering rate is interpretable
on its own**, and the run report may not carry one.

## Two classes of non-answer, and they are different classes

This is the repair. The version this note replaces held `BALANCED` out of the
numerator and the denominator, on the argument that a stated tie occupies
neither print position and that assigning it to either asserts a position the
response declined to take. That argument is right. It then put `BALANCED` into
the Manski bound, which performs exactly the assignment it had just forbidden.

**`BALANCED` is a stated absence of preference.** The contract defines it as
"you judge the two genuinely even", so the record says what it is. Imputing a
preference to a record that denies having one contradicts the record. It leaves
the numerator, the denominator and the bound, and it is reported as its own
rate, by ordering and by arm.

**`OFF_MENU`, `AMBIGUOUS` and `NO_CALL` are unresolved.** What the model would
have picked is genuinely unknown. These enter the bound: the primary is
recomputed with every unresolved record assigned to the first-printed course,
then to the second.

The bound is pooled over the same live items and the same kept records the point
estimate uses. It therefore **brackets the point estimate by construction**:
`S/(K+U) ≤ S/K` and `(S+U)/(K+U) ≥ S/K` whenever `K ≥ S`. The earlier bound was
computed over untrimmed records and over items the estimate had dropped, and
returned a rate of 1.000 sitting inside a bound of [0.500, 0.750].

### The identity the gate turns on, corrected

Writing rho for the second-position rate among kept committed records and u for
the resolution rate, u = K / (K + U) over those same items, the bound runs from
rho*u to rho*u + 1 - u. The gate needs it to exclude 0.5, which either endpoint
can do:

```
REPORTABLE  <=>  p < 0.05  AND  ( rho*u > 0.5  OR  rho*u + 1 - u < 0.5 )
            <=>  p < 0.05  AND  u > 1 / (1 + 2*|rho - 0.5|)
```

| true rho | direction | minimum resolution u | maximum unresolved |
|---|---|---|---|
| 0.10 | primacy | 0.5556 | 44.4% |
| 0.20 | primacy | 0.6250 | 37.5% |
| 0.35 | primacy | 0.7692 | 23.1% |
| 0.55 | recency | 0.9091 | 9.1% |
| 0.60 | recency | 0.8333 | 16.7% |
| **0.65 (registered)** | recency | **0.7692** | **23.1%** |
| 0.70 | recency | 0.7143 | 28.6% |
| 0.75 | recency | 0.6667 | 33.3% |
| 0.80 | recency | 0.6250 | 37.5% |
| 0.90 | recency | 0.5556 | 44.4% |

What a directional claim costs depends on the size of the departure and not its
direction. 0.35 and 0.65 are the same row, which is what a two-sided bound
around a symmetric null should say.

**The previous version of this section was wrong and the correction belongs
here rather than in a quiet edit.** It published only the first disjunct,
`u > 0.5/rho`. That is right for recency and wrong for every primacy result: an
independent verifier scored 60,000 random corpora and found 250 of 489
directional verdicts violating it, all of them primacy, including one of this
file's own battery cases. Below rho = 0.5 the printed table demanded a
resolution rate above 1, and the maximum-unresolved column went negative, which
no run can reach and nothing refused.

Two things are worth separating. **The gate was never wrong.** It reads both
endpoints and always has, so no verdict this instrument would return was
affected and no number in the sizing or the grid moves. What was wrong was the
published claim about the gate, in the one section headed with the assertion
that it is published. That is the defect class this whole instrument exists to
catch, sitting in the instrument, found by someone else. The shipped table hid
it: every row it printed was above 0.5, where the wrong identity and the right
one agree.

The repair is not only the corrected formula. `reportability_table` now spans
0.5 so the rows themselves would show a one-sided identity failing, and a
structural check compares the published predicate against the gate over a grid
that includes primacy. The superseded predicate is planted in that check and has
to be refused before the check may pass anything.

### What the old rule did, in one comparison

Two models, exact compositions, scored by the shipped code. Model P names the
second-printed course 60% of the time and commits on every draw. Model Q names
it 75% of the time and states `BALANCED` on half its draws.

| | true P(second) | commit | rate | n | p | old bound | new bound | old verdict | new verdict |
|---|---|---|---|---|---|---|---|---|---|
| P | 0.60 | 100% | 0.625 | 208 | 0.00038 | [0.625, 0.625] | [0.625, 0.625] | reported | reported |
| Q | **0.75** | 50% | 0.750 | 104 | <0.00001 | **[0.375, 0.875]** | **[0.750, 0.750]** | **withheld** | **reported, heterogeneous** |

Under the old bound, Q's abstention spread its bound across 0.5 and the model
with two and a half times the true position dependence was the one the
instrument refused. The instrument was hardest on the models that follow the
skill. Under the repair, `BALANCED` leaves the bound and the ranking by
published verdict matches the ranking by truth. `review/pq_check.py` runs both
columns from the same corpora; the old endpoints are closed-form arithmetic,
because the previous scorer is no longer on disk, and they reproduce the
[0.375, 0.875] the review recorded while it still was.

## The verdict has five values

A boolean collapsed four different findings into "no effect reported". The
dispersion flag now decides the verdict. The earlier version printed it beside
a headline that contradicted it and left the reader to reconcile them.

| verdict | when |
|---|---|
| `REPORTED` | significant, bound excludes 0.5, per-item counts within the null |
| `REPORTED_HETEROGENEOUS` | the same, and per-item counts depart from the null |
| `CONDITIONAL_ONLY` | significant, bound spans 0.5 — unresolved records could account for it |
| `HETEROGENEOUS_NO_DIRECTION` | pooled rate at the null, per-item counts departing from it |
| `NO_EFFECT` | none of the above |

`HETEROGENEOUS_NO_DIRECTION` is the one the earlier design could not say. A
corpus split between a recency half and a primacy half pools to exactly 0.5, and
the pooled statistic reports nothing while every item in it is order-driven.

## The trim selects on a hash of the record's coordinates

Three rules were available and two of them are wrong.

**Head truncation** keeps the lowest draw indices. It is unbiased only when the
draw index is exchangeable with respect to the outcome, and the obvious runner
behaviour breaks that: a runner that appends retries at higher indices is
appending exactly the draws that failed to commit the first time. On a corpus
whose per-ordering rates are both exactly 0.5 but whose draws arrive in blocks,
head truncation returns **0.750**. Under a true null with a 75% commit rate and
drift across the draw index, it took the exact test's level to **0.100** against
a nominal 0.05.

**Even spacing** removes the retry problem and adds an aliasing one. The battery
lays compositions out at evenly spaced indices too, so the two grids beat
against each other and a minority outcome can be kept or dropped wholesale: on
`{second: 2, first: 6}` keeping four of eight, even spacing lands on both of the
seconds.

**Sorting on a hash of the record's coordinates** — item, arm, ordering, draw —
depends on neither the draw order nor the layout nor the outcome, and needs no
assumption about the index at all. It is deterministic across runs and machines,
so a published number reproduces without carrying a seed. It is what runs.

The structural check plants a head-truncating trim on the same corpus and
refuses to pass anything until that planted defect has failed it. The band is
three standard errors of the pooled rate under the null, which is a choice and
is stated as one in the code.

`review/mc_repaired.py` runs the two rules side by side under a true null on the
corpus's own shape, 11 items × 8 draws per ordering, 800 trials, with drift
across the draw index and no order effect anywhere. Monte Carlo standard error
0.0077.

| commit | drift | hash P(sig) | head P(sig) |
|---|---|---|---|
| 1.00 | 0.0 | 0.0250 | 0.0250 |
| 1.00 | 0.6 | 0.0013 | 0.0013 |
| 0.90 | 0.0 | 0.0250 | 0.0262 |
| 0.90 | 0.6 | **0.0088** | **0.0512** |
| 0.75 | 0.0 | 0.0275 | 0.0200 |
| 0.75 | 0.6 | **0.0075** | **0.1050** |

The hash rule stays under the nominal 0.05 in every cell, worst case 0.0275.
Head truncation reaches 0.1050 in the cell that combines abstention with an
informative draw index.

One more thing that run shows. Every non-answer in it is a stated tie, so there
are no unresolved records, the bound collapses onto the point estimate and
P(reported) equals P(significant) in every cell. Under the old design the same
simulation had the Manski gate refusing on its own account and covering the
trim's inflation without being credited for it. The gate no longer does that
job here, because the trim no longer needs it done. Where a run does carry
unresolved records the bound binds again, and the identity says exactly when.

## Arms

`Record` carries an `arm` field drawn from `ARM_NAMES`, mirroring
`decision_evals.solvers.arms`: `off`, `on`, `placebo`, `cot`, `in_situ`. The
names are that module's and are not re-coined here, because a run filed under a
different vocabulary cannot be joined to anything else in the repository.

The version this note replaces had no arm dimension anywhere. Every number it
could produce was a one-arm description, while the kill condition it registered
required an arm comparison and the question the programme exists to answer is
`on` against `off`.

Two questions, two tests, and they are not the same question.

- **Each arm against the design null.** Exact binomial against 0.5. Asks whether
  that arm is order sensitive.
- **One arm against another.** `compare_arms` runs Fisher's exact test on the
  2×2 of committed calls, conditioning on both margins. Asks whether two arms
  are order sensitive to the same degree, and assumes nothing about where either
  one sits.

`ArmCell` reports every outcome class for every (arm, ordering) cell, with the
commit rate, the abstention rate and the resolution rate beside it. The report
prints it and may not omit it.

## The required n, corrected

Detect a second-position rate of 0.65 against the 0.5 null, two-sided α = 0.05,
power 0.80. Normal approximation: 85. Exact binomial, held stable for the next
twenty sizes: **97 committed records**, power 0.8338. The stability requirement
returns 97 for every `stable_for` from 5 to 100, so that parameter is not
load-bearing.

The earlier sizing then divided 97 by the commit rate. That is wrong, and the
error is one-sided. The trim keeps `min(C_AB, C_BA)` per item, so the yield is

```
E[kept] = 2 * sum_k P(Bin(r, c) >= k)^2   per item
```

and not `2·r·c`. The old recommendation of 13 items × 4 draws per ordering
delivers 104 records at a 100% commit rate and **86.3 at 90%**, against a
registered 97. The old issued-draw table said 108 draws at a 90% commit rate;
the correct figure is 120.

| commit | r = 3 | r = 4 | r = 6 | r = 8 |
|---|---|---|---|---|
| 100% | 17 items, 102 issued | 13, 104 | 9, 108 | 7, 112 |
| 95% | 18, 108 | 14, 112 | 9, 108 | 7, 112 |
| 90% | 20, 120 | 15, 120 | 10, 120 | 8, 128 |
| 80% | 24, 144 | 18, 144 | 12, 144 | 9, 144 |

Every cell is the fewest items whose expected kept yield reaches 97.

## The grid, chosen on joint power

The old grid rationale was that 13 items gave "enough items for the dispersion
flag to have degrees of freedom". That reasoning runs backwards: more items with
fewer draws each gives the flag **less** power, because each item's term gets
noisier against its own signal. Both powers, at the registered effect size, each
row sized to deliver 97 kept records at a 95% commit rate:

| r | items | issued | E[kept] | primary power | dispersion power | joint | one item is |
|---|---|---|---|---|---|---|---|
| 3 | 18 | 108 | 97.9 | 0.834 | 0.324 | 0.324 | 5.6% |
| 4 | 14 | 112 | 101.8 | 0.858 | 0.419 | 0.419 | 7.1% |
| 6 | 9 | 108 | 98.5 | 0.814 | 0.528 | 0.528 | 11.1% |
| 8 | 7 | 112 | 102.4 | 0.841 | 0.600 | 0.600 | 14.3% |
| **10** | **6** | **120** | **110.0** | **0.884** | **0.685** | **0.685** | **16.7%** |

Primary power is on a uniform effect at ρ = 0.65. Dispersion power is on a
corpus split half at 0.65 and half at 0.35, which pools to exactly 0.5 and which
the primary cannot see. Chosen on the weaker of the two, the smallest grid that
delivers the band is **6 items × 10 draws per ordering**.

Those rows are the fewest items that reach 97 records. The corpus on disk is
larger, and the scorer prints what it can actually run:

| r | issued | E[kept] | primary | dispersion | joint |
|---|---|---|---|---|---|
| 4 | 88 | 80.0 | 0.751 | 0.357 | 0.357 |
| 6 | 132 | 120.4 | 0.892 | 0.598 | 0.598 |
| 8 | 176 | 161.0 | 0.970 | 0.763 | 0.763 |
| 10 | 220 | 201.7 | 0.991 | 0.873 | 0.873 |

Eleven items × 6 draws per ordering reaches the same joint power as the minimal
6 × 10 grid for 132 issued draws against 120, and spreads the exposure over
eleven items at 9.1% each. Eleven × 8 reaches 0.763 for 176.

The last column is what it costs. One item carries 16.7% of the stratum there
against 7.1% at 14 items, a mislabelled item is that much of the headline, and
the blind adjudication's 20% kill reads against the same denominator.
Registering the grid registers that trade with it. Full budget for the
asymmetric stratum: 120 primary calls, 4 screen calls per candidate, 3
adjudication calls per admitted item.

The dispersion flag's exact null size at that grid is **0.0484** against a
nominal 0.05. The χ² reference is Wilson-Hilferty and runs **low** against the
true quantile at every degree of freedom checked, by 0.095 at df 1 and 0.012 at
df 13, so on its own account it fires slightly more often than nominal. The
earlier note claimed the approximation ran the safe way. It does not; the flag
is conservative because discreteness and the below-reference variance more than
cover the approximation, and the margin is stated here.

## Ruling on the strata, reversed: the primary is `undefeated`

The previous version of this note ruled that the asymmetric stratum alone is the
primary. That ruling is withdrawn. The argument under it was sound and the
conclusion did not follow from it.

The argument was that flip rate needed the tie stratum as an empirical baseline
and second-position rate does not, because the null is analytic. That is
correct. The contrast really does cost a factor of four in calls: with a budget
of 2n split evenly the difference has SE = 0.707/√n against 0.354/√n for a
single stratum. Dropping the contrast was right.

The conclusion drawn from it was that the primary is therefore the asymmetric
stratum. An exact null removes the need for a **contrast between two strata**.
It says nothing about **which** stratum to run. Dropping the subtrahend and then
keeping the subtrahend as the primary is a non-sequitur, and it went unnoticed
here for a version.

**The primary is the second-position rate on the `undefeated` stratum.** Both
courses survive the stated facts, nothing but the print order is left to break
the indifference, and the design's own theory of when order bites puts the
effect at its largest exactly there. The exact null at 0.5 holds for any item
under balanced orderings whatever its content preference, so the stratum is
self-sufficient and needs nothing subtracted from it. This is the programme's
original design, restored.

**`asymmetric` is registered as the specificity stratum and it is not deleted.**
A position effect on an undefeated item is an inconsistency with no cost
attached: the model swapped between two answers that were both defensible. A
position effect on an asymmetric item is print order overriding a stated,
checkable fact that defeats one of the courses, which is the stronger claim and
the harder corpus to author. It is registered, it has no items, it is never
pooled with the primary, and nothing is reported from it until it has items.
The difference between the two survives as a registered secondary with its power
stated as what it is. Flip rate survives as the legible secondary.

The instrument prints the refusal in capitals for whichever stratum the primary
is registered on. With the primary on `undefeated` and eleven measured items
there, it now falls silent, and the plain note about the empty specificity
stratum prints in its place.

## Ruling on the screen, and the kill it invalidates

**Specification, unchanged.** Four draws on the AB ordering of a candidate, at
the model and settings of the run, under the shipped contract. Admitted only if
all four return the same call, `BALANCED` counting as a call. Early stop on
first disagreement. Screen draws are discarded from the primary. A failed
candidate may be re-authored once; a candidate that fails twice is retired.

**One ordering, always the same one**, because requiring unanimity under both
would condition admission on the absence of the effect being measured, and
because a screen run on both orderings would make commitment treatment-dependent
through the selection and cost the test its exactness.

**The screen attenuates a real effect, and the kill has to say so.** Take the
design's own theory of when print order bites: it breaks the tie hardest when
content does not settle it. Model that as δᵢ = D·4αᵢ(1 − αᵢ) — the interaction
shape is a choice and it is recorded as one; the claim that the interaction
exists is this note's, in the paragraph justifying the `undefeated` stratum.
With δ constant across items there is no attenuation at all, verified as a
control. With the interaction:

| D | true corpus ρ | admitted ρ | fraction surviving | admit rate |
|---|---|---|---|---|
| 0.05 | 0.533 | 0.524 | 71.5% | 0.408 |
| 0.15 | 0.600 | 0.576 | 76.0% | 0.444 |
| 0.30 | 0.699 | 0.674 | 87.6% | 0.570 |

At D = 0.15 the power at 97 records falls from 0.474 to 0.294. The screen
preferentially rejects the items where the effect is largest.

**How hard that bites depends on the stratum, and it is now the undefeated one.**
The attenuation comes from a spread in α across items: the screen rejects the
items whose α sits near 0.5, which are the items where δ is largest. Holding δ
constant across items removes the attenuation entirely, which is the control row.
An undefeated item is one where no stated fact defeats either course, so the
stratum's α spread is narrower by construction than a mixed corpus of the same
size. That moves the primary toward the control and away from the table above.
It does not reach it, and the distance cannot be derived here: it needs the α
spread on the admitted corpus, which needs the run. The table stands as the
pessimistic end of the range rather than the estimate.

**So the kill is restated.** The old wording was: if the stratum cannot be
distinguished from 0.5 at 97 committed records and the free-prose contract arm
returns the same, the venue has no headroom for this construct. That inference
does not hold, because the screen removed the headroom by construction. The
registered kill is now:

> If the **undefeated** stratum's second-position rate cannot be distinguished
> from 0.5 at 97 committed records **on the admitted corpus**, and the same
> holds in the `off` arm, then **this instrument on this admitted corpus** has no
> headroom. That is a statement about items that pass a four-draw unanimity
> screen. It is not a statement about the venue, and the run report may not
> carry the second sentence.

Blind adjudication moving more than 20% of stratum labels still kills it.

## The specificity stratum has no items

Thirteen items exist. Eleven are in the measured corpus and every one of them is
`undefeated`, which is now the stratum the primary is registered on. The only
`asymmetric` item is K02, which is withdrawn on the contract digest. So the
primary can be run on this corpus and the specificity stratum cannot.

That is the right way round, and it is worth being clear that it was not
arranged that way. The corpus was authored to a brief that assumed the
superseded registration was wrong, the registration was then corrected to agree
with it, and the two now agree by a route nobody would design. The record says
so rather than presenting the agreement as planned.

What the empty stratum costs is a specificity claim. Without it, a departure
from 0.5 on the undefeated stratum says the model's recommendation moves with
print order between two defensible courses. It does not say print order can
override a fact that defeats a course, because no item in this corpus puts that
question. Authoring the asymmetric stratum is a separate unit of work with its
own four-draw screen, and it is where the stronger claim would come from.

## The items

**K03 ships.** The review disqualified it on a timeline: the prompt states "One
vessel does all of it", the Suilvenaig is "handover available from 2026-11-20",
and Kittiwake Brokers held the GBP 610,000 valuation only "until 2026-11-09".
The single operating vessel cannot be sold before its replacement arrives, so
the valuation lapsed **11 days before the earliest date the sale was possible**
and VELLACOTT's GBP 2,680,000 was undefended. Kittiwake now holds to
**2027-02-11**, six months from the 2026-08-11 valuation and **83 days past** the
earliest feasible sale date. The figures are unchanged: GBP 2,680,000 against
GBP 1,730,000, a gap of GBP 950,000 against GBP 190,000 a year of fuel, five
years exactly.

"We are seven people" against "nine masters" is resolved to "seven people ashore
and we crew from a rota of nine masters", so both counts stand and both remain
usable.

The two course paragraphs are rewritten to three favourable and three
unfavourable points each, mirrored: linkspan, masters and insurance are TARNSIDE
credits and VELLACOTT costs; yard period, fuel and hull age are TARNSIDE costs
and VELLACOTT credits. No point appears on one side only. The GBP 240,000
Ardvraich linkspan is now priced on the course that pays it, where before it
appeared only as a TARNSIDE positive. K01's deleted VELLACOTT favourable is
restored. Hedging is zero on both sides. Word counts are 70 and 66, a relative
delta of 5.9%.

**K03's contract is the registered one, and K01's and K02's is the defect.** K01
and K02 read "written exactly as it is written **above**". That is a positional
word in the contract of an instrument whose entire primary is a position effect.
K03 does not carry it, so K03's contract is what the corpus standardises on:
digest `8f04cff5e61beb7c`, 505 bytes, carried by eleven items. `CONTRACT_DIGEST`
holds it and `item_defects` returns `contract-is-not-the-registered-one` for
anything else.

**K01 and K02 are withdrawn from the corpus in the files themselves.** Two
contracts in one directory is a decision, so it is recorded where the items are
rather than left to the next reader. Both carry `in_measured_corpus: false` and
a `withdrawn_because` line naming the contract and the digest. They stay on disk
for K01's screen result, which is the only evidence anywhere for the screen, and
for K02's four pilot records. Neither is corpus. The report prints eleven
measured and two withdrawn.

**The four pilot records from K02 do not count toward the band.** Two reasons,
and the smaller one was the only one on record before. They are 2 AB and 2 BA
where the screen asks for four under one ordering. They were also collected
under a contract carrying a positional cue, so they are contaminated for this
purpose and are not pooled with anything run since.

**A defect the checker finds has to be declared.** `item_defects` returns short
names for the four authoring defects the checks can find, and every one has to
appear in the item file's `known_defects:` list. An undeclared defect fails the
run and so does a stale declaration. K01 declares one, K02 declares two, K03
declares none and is clean. Admission is a separate question: the screen and the
adjudication decide whether an item is admitted, these decide whether it was
written correctly, and an author can fix all four without a model call.

**The pair check gates on words and reports characters.** The old check gated on
a character delta of 5, with K02 sitting at exactly 5 — a parameter read off the
data. The tolerance is now a relative word delta of 10%, derived from the item's
own layout before the items were measured: the paragraphs hard-wrap near 76
columns, one wrapped line runs about 12 words against a paragraph of about 65, a
line is roughly 18% of a course block, and half a line is 9%, rounded to 10%.
K02's course paragraphs run 53 and 62 words, a delta of 15.7%, and **fail** it.
They sit 5 characters apart, which is the whole reason characters do not gate:
hard wrapping equalises typographic width, and words are what a model reads.

**The item gate computes rather than asserts.** Two defects in this corpus
survived prose that asserted a check and died to something that computed one.
K03 held a valuation that lapsed eleven days before the earliest date the sale
it priced could happen. K12 held a permission dated after the works it
authorised, and export figures larger than the scheme generating them could
produce. Neither is a defect a scorer can catch from a response.

So an item declares its dated and arithmetic claims and `computed_checks`
evaluates them:

```yaml
  checks:
    dates:
      - "2027-02-11 after 2026-11-20  # the valuation outlives the earliest sale"
    arithmetic:
      - "3050000 + 240000 - 610000 == 2680000"
```

Four date comparisons and five arithmetic identities ship with K03. The
falsifier plants K03's own lapsed date and K12's own impossible sum and refuses
to pass anything until both have failed it. That falsifier has already earned
its place: the first planted sum was true, the check refused to certify itself,
and the plant was wrong rather than the code.

One of eleven measured items declares them. The other ten carry their timeline
as prose in the authoring record, which is the form both defects survived, and
the report names them as work outstanding.

**Keep `mechanism_honesty`.** The item blocks carry it wherever a mechanism
label is arguable, and three items were rebuilt instead of relabelled when the
mechanism list was reassigned. A label nobody can argue with is usually a label
nobody checked.

**The positional-language scan ships with the instrument.** It runs over every
model-visible region — `prompt`, `format_contract`, `elicited.question` — in
both orderings. Nineteen layout-deixis patterns gate, and the scan runs twice over each
region: line by line for the line number, and again with the line breaks
collapsed, because the files hard-wrap near 76 columns and a two-word cue lands
across two lines often enough that a line-by-line scan alone would miss it. The
wrapping is an artefact of a column width no author chose.

`CUE_FIXTURES` ships 27 cues an author might plausibly write and 5
phrases that have to stay quiet, and the structural check runs the scan against
all 32 on every pass. A deixis list is only as good as the evasions
tried against it, and these were tried against an earlier list that missed six:
"the former" split across a line break, "whichever appears earlier", "the
first-listed course", "the second-named option", "read them in order" and "in
the sequence given". Quiet: "in this order" describing the output blocks, the
registered contract's own wording, and three lines of ordinary business prose
from K03. Three words that are
positional in some uses and ordinary in others are reported with their line and
gate nothing, because a scan that refuses "eleven crossings a day" gets switched
off within a week. The scan is falsified against a planted cue before it is
allowed to pass any shipped item.

## The battery

Fifty-two checks: extraction under both orderings of the same text, aggregate
corpora built from explicit compositions, and seven structural refusals
and invariants. Every aggregate case asserts the exact rate, the exact verdict, the
direction, and that the bound brackets the estimate.

**Seven mutants, each the honest scorer with one decision flipped, and each
caught by at least one case that catches it alone.** The version this note
replaces reported "each caught by a different case" on the strength of printing
only the first failure. Four of its six mutants had no case that caught them
alone, and dropping any one of three cases would have left a mutant uncaught.
`mutant_matrix` now computes the full case-by-mutant table and the run fails if
any mutant is merely shadowed by a blanket case.

Two pairs of decisions were each merged into one flag, because no corpus can
separate them and two mutants for one decision is decoration:

- `BALANCED` in the denominator and `BALANCED` in the bound are one decision at
  two sites. Any corpus that exposes the bound site contains `BALANCED` records,
  and a `BALANCED` record in the denominator always lowers the rate, so the rate
  assertion fires first on every such corpus.
- Trimming wrongly and not trimming at all are both visible only when the trim
  fires with unequal counts, and both change the answer whenever it does. The
  trim rule is checked by a structural test that plants the wrong one.

## Battery output, verbatim

`python council_primary.py`, on the corpus as it stands.

```
==============================================================================
COUNCIL ORDER-EFFECT PRIMARY: second-position rate
==============================================================================

-- extraction, both orderings of the same text ---------------------------------
  case                                             AB        BA
  commits to the course printed first under AB     first     second    
  commits to the course printed second under AB    second    first     
  declares an explicit tie                         balanced  balanced  
  commits to something not on offer                off_menu  off_menu  
  no extractable commitment                        no_call   no_call   
  inline call of the superseded contract           no_call   no_call   
  call block naming both courses                   ambiguous ambiguous 
  call block carrying a sentence as well           no_call   no_call   
  the Course prefix the prompt itself prints       second    first     
  blocks restated, the last standing               second    first     
  a recommendation the grounds line qualifies away second    first     
  the call in markdown emphasis                    first     second    
  the call in title case                           first     second      <- normalised
  the call with a trailing gloss                   first     second    
  emphasis around a course that is still not on offer off_menu  off_menu  

-- branch one: an effect that is there must be reported ------------------------
  recency effect present                    rate=0.667 n=144  p=0.00008 -> recency
                                             reported
  primacy effect present                    rate=0.333 n=144  p=0.00008 -> primacy
                                             reported
  heavy abstention over a real effect       rate=0.625 n=192  p=0.00066 -> recency
                                             reported
  the trim carries the weight               rate=0.750 n=64   p=0.00008 -> recency
                                             reported
  heterogeneous items with a net direction  rate=0.625 n=144  p=0.00339 -> recency
                                             reported, and per-item effects are heterogeneous

-- branch two: an effect that is not there must not be -------------------------
  content-driven answer, no effect          rate=0.500 n=144  p=1.00000 bound=[0.50,0.50] u=1.00 T ok  
                                             no effect reported
  coin-flip noise, no effect                rate=0.500 n=144  p=1.00000 bound=[0.50,0.50] u=1.00 T ok  
                                             no effect reported
  strong content preference, no effect      rate=0.500 n=144  p=1.00000 bound=[0.50,0.50] u=1.00 T ok  
                                             no effect reported
  heavy abstention, no effect               rate=0.500 n=96   p=1.00000 bound=[0.50,0.50] u=1.00 T ok  
                                             no effect reported
  unresolved records could carry it         rate=0.650 n=60   p=0.02734 bound=[0.36,0.81] u=0.56 T ok  
                                             conditional only: unresolved records could account for it
  differential commitment, no effect        rate=0.500 n=192  p=1.00000 bound=[0.50,0.50] u=1.00 T ok  
                                             no effect reported
  departure too small for the sample        rate=0.583 n=24   p=0.54126 bound=[0.58,0.58] u=1.00 T ok  
                                             no effect reported
  opposing effects cancelling across items  rate=0.500 n=144  p=1.00000 bound=[0.50,0.50] u=1.00 T FLAG
                                             order dependence present, direction cancels across items
  ordinary scatter around the null          rate=0.500 n=144  p=1.00000 bound=[0.50,0.50] u=1.00 T ok  
                                             no effect reported
  blocked draw order, no effect             rate=0.500 n=192  p=1.00000 bound=[0.50,0.50] u=1.00 T ok  
                                             no effect reported

-- attrition by arm and ordering, on the case that turns on it -----------------
  arm    ord     first   second balanced off_menu ambiguou  no_call  commit abstain resolve
  on     AB         24       72       96        0        0        0   0.500   0.500   1.000
  on     BA         48       48       96        0        0        0   0.500   0.500   1.000
  trimmed=0  dropped_items=[]  normalised_calls=0  order_balanced_rate=0.6250
  the resolution rate is the one the gate uses. BALANCED is in neither half of it.

-- the same stratum under two arms, and the contrast between them --------------
  arm on       rate=0.667 n=96   p=0.00142  commit AB/BA 1.00/1.00  -> reported
  arm off      rate=0.500 n=96   p=1.00000  commit AB/BA 1.00/1.00  -> no effect reported
  contrast on - off = +0.167, Fisher exact p=0.02782  (arms differ)
  each arm is tested against the design null of 0.5; the contrast assumes
  nothing about where either arm sits and is the on-against-off question.

-- the honest scorer against the whole battery ---------------------------------
  54 checks, 0 failures

-- the same code path, one decision flipped at a time --------------------------
  caught    BALANCED treated as missing data
            by 4 case(s), 2 of which catch it alone
            alone by aggregate/heavy abstention over a real effect
  caught    per-item AB/BA balance skipped
            by 3 case(s), 2 of which catch it alone
            alone by aggregate/the trim carries the weight
  caught    position read from the course name
            by 14 case(s), 7 of which catch it alone
            alone by aggregate/primacy effect present
  caught    Manski bound ignored
            by 1 case(s), 1 of which catch it alone
            alone by aggregate/unresolved records could carry it
  caught    no significance test
            by 9 case(s), 4 of which catch it alone
            alone by aggregate/blocked draw order, no effect
  caught    per-item dispersion never looked at
            by 2 case(s), 1 of which catch it alone
            alone by aggregate/heterogeneous items with a net direction
  caught    surface form never normalised
            by 8 case(s), 5 of which catch it alone
            alone by extraction/emphasis around a course that is still not on offer under AB

-- what a directional claim costs, as a resolution rate ------------------------
  the bound runs from rho*u to rho*u + 1 - u and the gate needs it to
  exclude 0.5, so reporting needs u > 1 / (1 + 2*|rho - 0.5|).
    true rho   direction    min resolution u    max unresolved
        0.10     primacy              0.5556            0.4444
        0.20     primacy              0.6250            0.3750
        0.35     primacy              0.7692            0.2308
        0.55     recency              0.9091            0.0909
        0.60     recency              0.8333            0.1667
        0.65     recency              0.7692            0.2308
        0.70     recency              0.7143            0.2857
        0.75     recency              0.6667            0.3333
        0.80     recency              0.6250            0.3750
        0.90     recency              0.5556            0.4444
  the cost depends on the size of the departure and not its direction:
  0.35 and 0.65 are the same row. An earlier version of this table read
  only the lower endpoint, printed u > 1.43 at rho = 0.35, and a negative
  unresolved share below that. It was right for every row it shipped with
  and wrong for every row it did not, which is why the rows now span 0.5.
  a subtler true effect demands a more resolvable run. At the registered
  alternative of 0.65 the run needs u > 0.769 whatever the sample size.

-- sizing ----------------------------------------------------------------------
  detect a second-position rate of 0.65 against the 0.5 null
  two-sided alpha 0.05, power 0.8
  normal approximation      85 committed records
  exact binomial, stable    97 committed records
  power at that size        0.8338

  the trim keeps min(C_AB, C_BA) per item, so the yield is
  2 * sum_k P(Bin(r,c) >= k)^2 per item and not 2 * r * c. Issued draws
  divided by the commit rate overstates it at every commit rate below one.
    commit   r  items  issued   E[kept]  naive items/issued
      100%   3     17     102     102.0  17/97
      100%   4     13     104     104.0  13/97
      100%   6      9     108     108.0  9/97
      100%   8      7     112     112.0  7/97

       95%   3     18     108      97.9  18/103
       95%   4     14     112     101.8  13/103
       95%   6      9     108      98.5  9/103
       95%   8      7     112     102.4  7/103

       90%   3     20     120      99.0  18/108
       90%   4     15     120      99.6  14/108
       90%   6     10     120     100.7  9/108
       90%   8      8     128     108.2  7/108

       80%   3     24     144      98.4  21/122
       80%   4     18     144     100.2  16/122
       80%   6     12     144     102.6  11/122
       80%   8      9     144     104.1  8/122


-- choosing the grid on joint power, at the registered effect size -------------
  primary power is on a uniform effect at rho=0.65 over the delivered
  records. dispersion power is on a corpus split half at 0.65 and half at
  0.35, which pools to exactly 0.5 and which the primary cannot see.
  every row is sized to deliver 97 kept records at a 95% commit rate.
     r  items  issued  E[kept]   primary  dispersion    joint  one item
     3     18     108     97.9     0.834       0.324    0.324      5.6%
     4     14     112    101.8     0.858       0.419    0.419      7.1%
     6      9     108     98.5     0.814       0.528    0.528     11.1%
     8      7     112    102.4     0.841       0.600    0.600     14.3%
    10      6     120    110.0     0.884       0.685    0.685     16.7%
  the grid to register is 6 items x 10 draws per ordering, chosen on the weaker of the two powers.
  the last column is the cost: one item carries 16.7% of the stratum there against 7.1% at 14 items.
  A mislabelled item is that much of the headline, and the blind
  adjudication's 20% kill reads against the same denominator.
  Registering the grid registers that trade with it.
  exact null size of the dispersion flag at that grid: 0.0484 against a nominal 0.05

  the rows above are the fewest items that deliver the band. The corpus on
  disk is larger, so here is what it can run, by the stratum it belongs to:
  undefeated: 11 measured item(s) -- K03, K04, K05, K06, K07, K08, K09, K10, K11, K12, K13
         r  issued  E[kept]   primary  dispersion    joint
         4      88     80.0     0.751       0.357    0.357
         6     132    120.4     0.892       0.598    0.598
         8     176    161.0     0.970       0.763    0.763
        10     220    201.7     0.991       0.873    0.873
  The specificity stratum, asymmetric, has no measured item.
  It is registered, it is never pooled with the primary, and it is
  a separate authoring unit with its own screen. Nothing is reported
  from it until it has items.

-- the corpus: pairs, language, contract and computed checks -------------------
  a defect the checker finds has to be declared in the item's known_defects.
  an undeclared defect fails the run and so does a stale declaration.
  an item in the measured corpus has to carry no defects at all.
  item  rebuild  words       delta   contract   cue   checks   corpus
  K01   True     70/64       9.0%    OLD        HIT   none     withdrawn
  K02   True     53/62       15.7%   OLD        HIT   none     withdrawn
  K03   True     70/66       5.9%    registered clean computed measured
  K04   True     61/62       1.6%    registered clean computed measured
  K05   True     62/62       0.0%    registered clean computed measured
  K06   True     61/63       3.2%    registered clean computed measured
  K07   True     60/59       1.7%    registered clean computed measured
  K08   True     63/62       1.6%    registered clean computed measured
  K09   True     60/60       0.0%    registered clean computed measured
  K10   True     61/61       0.0%    registered clean computed measured
  K11   True     65/65       0.0%    registered clean computed measured
  K12   True     64/64       0.0%    registered clean computed measured
  K13   True     64/64       0.0%    registered clean computed measured
  11 item(s) in the measured corpus: K03, K04, K05, K06, K07, K08, K09, K10, K11, K12, K13
  2 withdrawn and not corpus: K01, K02
  11 of 11 measured item(s) declare dated and arithmetic checks the instrument computes:
  K03, K04, K05, K06, K07, K08, K09, K10, K11, K12, K13. The rest carry their timeline as prose in the
  authoring record. Two defects in this corpus survived prose that asserted the check
  and died to something that computed it, so the remaining items are work outstanding.

-- the pilot's own K02 records, scored -----------------------------------------
  rate 0.500 on 4 committed records
  exact p 1.000, 95% CI [0.068, 0.932]
  reading: no effect reported
  4 of the 97 records the registered band needs, and they do not count toward it:
  they were collected under K01's and K02's contract, which reads
  "written exactly as it is written above". That is a positional word in
  the contract of an instrument whose primary is a position effect, so the
  four records are contaminated for this purpose and are not pooled with
  anything run since. The count problem is real and it is the smaller one.

==============================================================================
BATTERY PASSED
==============================================================================
```

## The law this is the third instance of

`cascade` divides a false-alarm rate by an attention rate the model controls.
`hinge` keeps `OFF_LIST` in the denominator and drops `NO_BLOCK`. `council`
cancels the commit rate out of the estimator and lets it back in through the
reporting gate. Every one is an exclusion correlated with competence, and in all
three the exclusion counts were computed without an arm breakdown, so the
attrition was invisible in the published output.

For every rule that removes a record from a denominator, three questions: what
makes a record leave, is that correlated with doing the task well, and which way
does the resulting bias run. Three of `council`'s six could not answer the third
cleanly before this version, and the two rows that still cannot are marked.

| rule | what makes a record leave | correlated with competence | which way the bias runs |
|---|---|---|---|
| `BALANCED` | model states an explicit tie | **Yes, by design.** `council.md` calls a surviving tie a finding | None on ρ: the commit rate cancels. None on the gate since the repair, because `BALANCED` leaves the bound |
| `NO_CALL` | no bare `CALL` header, empty block, block carrying more than the call, no admissible call | **Both signs.** A qualified commitment is excluded; so is a model ignoring the format | None on ρ. Against verbose and hedging models on the gate. **Still unresolved:** the two populations are not separated |
| `AMBIGUOUS` | names both courses | Yes — cannot separate them and writes both instead of `BALANCED` | None on ρ; raises the unresolved count and tightens the gate |
| `OFF_MENU` | names a course not on offer | Mostly negative. Surface-form variants no longer land here | None on ρ; raises the unresolved count |
| balance trim | over-committing ordering loses records | Yes; compounds with abstention, since E[kept] falls faster than the commit rate | None under the hash rule. The sizing now accounts for the loss |
| item `dropped` | zero committed under one ordering | Yes, same as `BALANCED` | None: the bound is computed over live items only. **Partly unresolved:** a dropped item leaves the stratum silently and only `dropped_items` records it |

## What is closed, what is an accepted limit, what is not closed

**Closed, and each changed a number.**

- `BALANCED` leaves the Manski bound. The identity is published with its table,
  in the corrected two-sided form `u > 1/(1 + 2*|rho - 0.5|)`, and a structural
  check holds it against the gate over a grid spanning both directions. The
  ranking inversion between a terse model and a careful one is gone.
- Sizing rebuilt on `E[kept]`. The recommended grid delivers its records.
- The trim selects on a hash of the record's coordinates. The blocked-layout
  artefact of 0.750 against a true 0.500 is gone, and so is the level inflation
  to 0.100 at a 75% commit rate.
- The grid is chosen on joint power. 6 × 10 gives 0.685 against 13 × 4's 0.419
  at a comparable budget.
- `arm` exists, is carried through, and every exclusion class is reported by
  ordering and by arm. `compare_arms` answers the on-against-off question.
- Surface-form normalisation. `Penhallick`, `**PENHALLICK**` and
  `PENHALLICK (the lease)` score as calls, and the count of normalised calls is
  reported so an over-eager normaliser stays visible as a `verifier_defect`.
- The dispersion flag gates the verdict.
- Every safeguard field is printed.
- The pair check gates on a derived word tolerance. K02 fails it.
- K03's timeline, its seven-against-nine, and its course-paragraph balance.
- The positional-language scan ships with thirty-two fixtures and runs on every
  pass. Six evasions an earlier list missed fire, and so do the eleven an
  independent verifier got past the list after that. Those eleven had one thing
  in common: the list matched ordinal deixis and never matched spatial deixis or
  a comparative without an ordinal in it. Coverage was a word list where it
  should have been a concept, and the eleven are kept verbatim as fixtures.
- One registered contract, held by digest, carried by eleven items. The two that
  carry the older one declare `in_measured_corpus: false` in the files
  themselves and say why.
- The item gate computes dated and arithmetic claims instead of reading prose
  that asserts them, falsified against K03's own lapsed date and K12's own
  impossible sum. The evaluator walks the parse tree and refuses anything
  outside arithmetic and comparison.
- All eleven measured items now declare checks: 64 dated and 126 arithmetic
  assertions, each block byte-identical across its pair. Every one is built from
  figures the item's own prompt states, which a provenance guard enforces at two
  sourced literals per arithmetic entry, because one would admit
  `190000 / 190000 == 1`. Backfilling them found a defect prose had carried
  three times: K04 applied a ratio of 1.1 to 1.3 against 1.4 and stated the
  answer as 1.19, where the stated inputs give 1.1846. It is repaired, and the
  equality is now two bracketing inequalities, because a derived decimal should
  not be tested with `==` against a rounded one.
- The corpus is discovered from disk, so the report covers thirteen items rather
  than a hand-kept list of three.

**Accepted limits, stated rather than fixed.**

- The screen attenuates a real effect to 71–88% of its size under the design's
  own theory of when position bites. The kill is restated to be about the
  admitted corpus. Closing it needs a two-ordering screen, which would cost the
  test its exactness, so it stays open and named.
- No per-ordering rate is interpretable on its own. The AB half moves by up to
  0.19 under the screen and the BA half by the same amount the other way.
- The battery's aggregate cases are exact compositions with no sampling scatter.
  They test the estimator's algebra. A simulation arm over the null with the
  corpus's real compositions is what would test its behaviour under noise. That
  arm lives in review scratch and the shipped battery does not carry it.
- `NO_CALL` mixes a competence-positive and a competence-negative population and
  the instrument does not separate them.
- The registered grid puts 16.7% of the stratum on each item.
- Neither the screen nor the blind adjudication has been run against any of the
  eleven measured items. No order-effect record may be opened until both have.
- The reader that pulls a prompt out of a YAML file is hand-written and stays
  hand-written, because a parser round trip would normalise the whitespace the
  pair check exists to compare. It now raises a named error on every block form
  it does not handle instead of returning something short, which is what let a
  tab-indented prompt scan clean.

**Closed by a ruling rather than by code.**

- **The registered primary stratum had no measured item.** The registration was
  the thing that was wrong, not the corpus: the ruling that put the primary on
  the asymmetric stratum drew a conclusion its own argument did not support.
  The primary is now the `undefeated` stratum, where all eleven measured items
  are, and `asymmetric` is the registered specificity stratum with no items.
  The capitals refusal still fires for whichever stratum the primary sits on
  and is silent because that stratum now has items.

**What an independent verifier broke, and what it confirmed.**

A second agent was briefed to break the repaired scorer and given scipy and
numpy as an independent reference. It ran roughly 95,000 scored random corpora
against the Manski bound, 180,000 Monte Carlo trials against the null, and
every (k, n) pair up to n = 150 against `scipy.stats.binomtest`.

Confirmed against an independent implementation, with no discrepancy: the bound
brackets the point estimate; the exact null survives the hash trim at every
commit rate and grid tried, with a largest exact level of 0.0467 against a
nominal 0.05; `expected_kept` matches exact enumeration to 2e-14; the dispersion
null size of 0.0484 at the registered grid; `fisher_two_sided` against scipy on
45 tables including zero cells; `exact_two_sided_p` and `clopper_pearson`
against scipy on all 1,276 pairs; extraction is exactly symmetric between
orderings over 60,000 fuzzed responses; and one arm's records cannot leak into
another's rate.

It also produced the mechanism that breaks head truncation, which this note had
asserted without one. Appending retries at higher indices does not break head on
its own, because when commitment is independent of content the retried draws
carry the same law as the originals. What breaks it is content drifting with the
draw index together with ordering-dependent commit rates: at a 0.05/0.45 split
the head rule rejects a true 0.5 null 37.2% of the time and the hash rule 2.1%.
The stated reason for preferring the hash was not the operative one, and the
operative one is now recorded.

Six things it broke, all repaired:

1. **The published reportability identity**, above. The largest of them.
2. **The prompt reader returned a lone newline** for any block form it did not
   understand: a tab indent, `|-`, `|+`, `|2`, a quoted scalar. The positional
   scan then read an empty prompt and certified a contract carrying a positional
   word as clean. It now raises a named error. A reader that cannot fail is a
   check that cannot fail.
3. **A CRLF checkout failed every item.** With `core.autocrlf=true` the
   paragraph split never fires, and a correct K03 pair reported three defects it
   does not have. Line endings are now normalised on read, which is the one
   thing about a checkout that is not a property of the item.
4. **The positional scan's coverage was a word list, not a concept.** Eleven of
   thirteen hand-written cues walked past it, every one of them spatial or
   comparative rather than ordinal. All eleven are fixtures now.
5. **The binomial pmf raised `OverflowError` above about 1030 records**, which
   65 items at 8 draws per ordering reaches. The direct expression is kept as
   the primary path so no number this file has printed moves, with a log-space
   fallback where it cannot produce an answer at all.
6. **Float equality in the item checks** compared `(13.6 + 1.8) - 14.2` against
   1.2 and refused a correct item, because in binary the left side is
   1.2000000000000002. The tolerance that replaced it is derived and not chosen:
   the smallest difference an item can mean is a relative 1e-2, accumulated
   double-precision error is around 1e-16, and 1e-9 sits seven orders of
   magnitude from each. It is checked against the defect this corpus actually
   had, which is a relative 4.5e-3 and is still refused.

Left as named limits rather than repaired: `_normalise` can turn one course name
into the other on contrived item names, which is content-wrong and still
position-neutral, so it cannot manufacture a position effect; a record naming an
unknown item or an ordering that is not `AB` or `BA` raises a bare `KeyError`;
and an item whose two courses share a name scores every record `FIRST` in
silence. All three need an item nobody has written.

**Not closed.**

- **The strongest objection I could not make stick remains unstuck, and it is
  now better bounded.** The AB-only screen biases the AB half by up to 0.19 and
  the pooled primary not at all, because the two halves cancel exactly. What
  would make it stick is any run where the per-item AB/BA committed counts are
  unequal when the pooled rate is formed: the leak is −Δ·g/(2 + g) for a
  commit-count ratio of 1 + g, which is −0.037 at g = 0.5 and −0.062 at g = 1.0.
  The three routes are a weakened balance, a non-empty `dropped_items`, and a
  screen ever run on both orderings. The first two are now visible in the
  printed report, which is what a later reviewer needs to settle this rather
  than bound it.

## Files

- `council_primary.py` — the scorer, the battery, the seven mutants, the nine
  structural checks, the sizing, the joint-power grid, the pair check, the
  positional scan with its fixtures, and the computed item checks. Runs on a
  bare interpreter, discovers the corpus from disk, exits non-zero on failure.
- `K03-brindlemere-refit-undefeated-{ab,ba}.yaml` — measured corpus. Authoring
  checks clear, computed checks declared, screen unrun, `admitted: false`.
- `block-A/K04..K08`, `block-B/K09..K13` — measured corpus, ten items, all on
  the registered contract, all screens unrun.
- `K01-brindlemere-refit-tie-{ab,ba}.yaml` — withdrawn from the corpus. Two
  declared defects. Kept for its screen result, which is the only evidence
  anywhere for the screen.
- `K02-ospreyhaugh-cnc-asym-{ab,ba}.yaml` — withdrawn from the corpus. Three
  declared defects, and the only `asymmetric` item there has ever been.
- `make_k03_ba.py`, `revise_k01_k02.py`, `block-*/make_ba.py` — generators.
- `review/` — the adversarial review's scratch: the mutant matrix, the
  falsifiers, the Monte Carlo, the screen arithmetic, the P/Q comparison, the
  patches applied to the scorer, and `battery_output.txt`.
