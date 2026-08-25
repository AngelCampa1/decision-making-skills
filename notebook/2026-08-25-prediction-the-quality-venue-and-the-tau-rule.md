# 2026-08-25 — prediction: the decision-quality venue, and the rule that fixes tau

Registered before any item is authored, before the elicitation runner exists, and
before the first call. Every sentence below about what will run is in the future
tense on purpose.

This entry registers four things at once because they are one unit of work: the
movement-threshold rule, the extraction consensus rule, the multiplicity family,
and the acceptance tests that decide whether the first two were implemented or
merely typed.

## Why this is registered now

Twelve results are on record and every one of them measures whether the skill
fires. `SCORECARD.md` says so about itself: *"A trigger measurement is about
whether the skill fires, not about whether firing produces a better decision, and
nothing has measured the second question yet."*

Five venues that would have answered the second question are closed. Four closed
on a ceiling, with the unaided model between 0.917 and 0.971. The fifth,
`tailoring`, is open and blocked on authoring yield.

The closed casefile venue was re-checked against its own records rather than
against its closure note before this entry was written. Computed from
`results/probe/casefile-probe.jsonl`: `condition_recall` reads **0.971 over 12
items with three distinct values**, minimum 0.80. It ceilings on the graded
outcome as well as on binary admissibility, so the graded outcome does not
reopen it.

## The three instrument families

`docs/PROTOCOL.md` §7 holds that no primary metric is ever a judge score.
Scoring *did it ask* or *was each case argued fairly* from prose is a judge
call, so the six shipped procedures divide by what a verifier can read.

| family | procedures | primary | answer key |
|---|---|---|---|
| A, scalar triplet | `ledger`, `timing`, `fit` | Youden's J over an elicited quantity | yes |
| B, planted-set membership | `hinge`, `cascade` | J over named-against-not, against a planted key | yes |
| C, order effect | `council` | recommendation flip rate under AB and BA ordering | none |

The families are independent, so a kill in one closes a stratum and leaves the
others running.

**Family A is one venue with three strata, carrying one primary.** `ledger`,
`timing` and `fit` are one contrast wearing three content skins, so three
registered primaries would report the same number three times with the
between-stratum variance attributable to item difficulty. Strata enter as a
covariate. Per-stratum J is a §4 descriptive secondary.

**Family C needs no answer key**, which is worth stating plainly: 21 of 21
scored failures across three corpora in this repository were the answer key. An
instrument with no key cannot fail that way. `council` has no base arm, since a
scenario with an unspecified number of defensible positions already is one of
the two arms, so the triplet form does not apply to it and self-consistency
does.

## The movement threshold, and the two defects in the rule it replaces

`derive_movement_threshold` returns the maximum of the n base-versus-base
relative excursions. That is two separate defects and only one of them was
recorded on 2026-08-19.

**The estimand moves with n.** The expectation of a maximum over n draws is a
function of n, converging to the supremum of the distribution rather than to any
fixed functional. So tau climbs with corpus size, sensitivity falls, and the true
J changes venue between rows of every power table: reconstructed at 0.843, 0.915,
0.956 and 0.977 for n of 5, 10, 20 and 40.

**The interval under-covers, and this half is new here.** Tau is a plug-in
nuisance parameter estimated from the data and then held fixed across every
bootstrap replicate inside `compute_phase0_result`. `cluster_bootstrap_diff`
resamples clusters and recomputes a mean of indicators that were classified
against a threshold it never touches. The analysis treats a random threshold as
known. Measured consequence, recorded on 2026-08-19 and attributed there to
cluster dependence: realised SD 1.23 to 2.31 times the closed form, coverage
0.61 to 0.85 against a nominal 0.95.

Cluster dependence is a true description and the sharper one is that a random
threshold is being treated as a constant. The two readings imply different
fixes, which is why the distinction is worth making before the fix is chosen.

### The rule, registered

**Movement is measured on the log scale.** `log_movement(q_base, q_variant)` is
the absolute difference of the logarithms, and any non-positive quantity is
refused rather than divided by.

The reason is direction asymmetry in the rule being replaced. Under relative
movement a doubling scores 1.000 and a halving 0.500, so down-arms sit lowest by
construction. `datasets/tailoring/index-pass2.yaml` already records the
consequence: `t04` is `blocked_pending_tau` at 0.333, and the deliberate
three-up two-down split bought sign robustness and paid for it in threshold
headroom. On the log scale `t04`'s 6 to 4 reads 0.405 against `t03`'s 4 to 8 at
0.693, narrowing the gap from 3.0x to 1.71x, and `t05`'s 28 to 14 becomes exactly
equal to a doubling. That equality is what the up-down split was buying and what
the relative rule silently broke.

**Tau is `k` times sigma-hat, where sigma-hat is the root mean square of the n
base-pair log differences.** Root mean square about zero rather than standard
deviation about the mean: under the null nothing was perturbed, so the mean is
known to be zero, and centring spends a degree of freedom to estimate a drift
term the design says does not exist. Sigma is a population parameter and
sigma-hat is root-n consistent, so the estimand is fixed in n and tau-hat
stabilises as the corpus grows.

**The bootstrap recomputes tau inside every replicate.** This is the fix for the
second defect, and it is valid only because a root mean square is smooth where a
maximum is not. The bootstrap of an extreme order statistic is inconsistent, so
no amount of recomputation would have rescued the maximum. That ordering is the
argument for the pooled estimator over a high quantile, which fixes the drift and
leaves the coverage alone.

**A per-triplet tau is cleaner and is rejected on cost.** It has no drift and
exactly independent clusters. At two repeats there is one base pair per triplet,
so classifying one noise draw against another puts specificity near 0.5 under the
null and makes the kill's arithmetic unreachable. Stabilising it needs five or
six repeats, which contradicts Track I's registered *"Two, not five."* Recorded
as a choice under standing rule 1, with the reason.

### `k` is a choice, and the trap it carries is registered before it can be sprung

Any tau calibrated to a target false-movement rate makes specificity a near
constant and hands all of J's variation to sensitivity. Setting `k` to put
specificity at 0.85 would make the registered prediction *specificity will be
below 0.85* true by construction and unfalsifiable. The maximum rule has the same
disease in the limit: it targets a false-movement rate near zero, forcing
specificity toward 1 and J toward sensitivity.

So `k` is declared as a choice, its sensitivity is swept in the simulator rather
than argued, and `Phase0Result` gains a `specificity_ceiling` field that
`disposition()` prints beside specificity every time. **A specificity equal to
its structural ceiling is an inert-instrument signature and is now visible as
one.** This repository records five inert-estimator instances, one of them inside
the module whose job was hunting inert estimators.

## The extraction consensus rule

The Track H registration names Fleiss kappa over movement calls, and
`extractor_movement_agreement` computes it. Three extracted **scalars** need a
combination rule and none exists anywhere in this repository.

> The quantity for a response is the **median of the three parsed values**. A
> response where fewer than two extractors parse is a missing measurement; its
> whole (triplet, repeat) event is dropped, and the dropped count is printed on
> the result.

Median rather than mean, because one extractor reading a planted distractor
numeral is exactly what `fal-p` exists to catch, and a distractor moves a mean
while leaving a median of three where it was. The three-way disagreement rate is
printed beside the quantity, because a median hides a three-way split.

## The multiplicity family

Six constructs is six primaries, which is a family. `stats/multiplicity.py`
implements `benjamini_hochberg`, exports it, property-tests it, and nothing calls
it. That is the uncounted eleventh entry on `docs/STATUS.md`'s broken-measurement
list, where `paper/CHECKLIST.md` had ticked *"multiplicity controlled"* over an
uncalled function. `scripts/score_quality.py` will be its first caller.

Family: the primary of each construct that reaches a reported J. Benjamini
Hochberg at q = 0.10, matching `docs/PROTOCOL.md` §5. Guards stay uncorrected,
for the reason §5 already gives.

## The acceptance tests, registered before the implementation lands

`scripts/size_track_h_phase0.py` **cannot see the defect that invalidates its own
tables.** It draws change indicators directly from a true J through
`draw_triplet_rates` and `draw_event_indicators`, so no quantity is ever
simulated and tau never exists inside it. Verified by reading it: neither
`derive_movement_threshold` nor `classify_movement` nor any elicited quantity
appears anywhere in the file. That is a twelfth instance of a measurement that
produced clean numbers while measuring nothing, and it is the reason the
acceptance tests below are two-branch rather than one.

A quantity layer goes in upstream of the existing indicator layer, drawing
log-normal elicitation noise and then calling the real `derive_*` and
`classify_*`. Two gates wire into `check_known_answers`, so `main()` exits
non-zero and prints no recommendation when either fails.

**Drift gate.** The maximum absolute difference in true J across n of 5, 10, 20
and 40 must read below 0.02 under the pooled rule **and above 0.10 under the
maximum rule**. Both branches run every time.

**Coverage gate.** Realised two-sided coverage at n of 15 and 20 must land within
Monte Carlo error of 0.95 with the threshold recomputed per replicate, **and must
reproduce the recorded 0.61 to 0.85 with it held fixed**.

The second branch of each is standing rule 2. A drift detector that has not first
reproduced the known drift has not been shown able to detect drift at all, and a
threshold estimator that returns a constant would produce a perfectly stable
table and a clean pass.

Every existing row of the 174-cell grid is superseded by this change, because
true J per cell becomes a derived quantity rather than a dialled one. The
re-derived `smallest_usable_n` is what the authoring bill gets sized against, and
the current answer of ten to fifteen may not be reused until it is re-derived.

## The authoring yield kill

Everything downstream is priced by yield. At the measured one clean triplet in
five, ninety usable triplets is four hundred and fifty authored and roughly four
million characters, which is the bill that closed Track G arriving by another
route. At three in five it is a hundred and fifty authored and the venue is
buildable.

This is in substance a third authoring pass, and the pass-one entry names
*"authoring until it passes"* as corpus p-hacking, so the kill is registered here
before authoring and it is on yield rather than on J.

> **Kill: if fewer than 3 of 5 `ledger` triplets survive blind re-derivation and
> an adversarial review briefed to prove the matched fact governs, the volume
> dial does not solve the yield problem, and the authoring cost is the finding.**

The successor is registered with the kill rather than decided after it: Family A
drops to `timing` alone at reduced n, and Families B and C, which do not use the
scalar triplet, carry the track.

## Two disqualifiers added before authoring

Both were found by adversarial review of the design and neither is among the
fifteen in `docs/TAILORING_CORPUS_SPEC.md` §5.

**16. The elicited question enumerates the constraints the answer is a minimum
over.** A question naming both binding constraints lets a model match two nouns
and score specificity 1.0 with no domain reasoning. This is the mirror of §4.1's
self-neutralising insert, sitting on the question rather than on the insert.

**17. The governing arm's answer is infeasible against the base's own
information timeline.** Where a real deadline precedes the arrival of the
information the decision needs, the correct answer is to commit blind in both
arms and the contrast vanishes.

## Predictions

Each names its estimator and its denominator. All concern the unaided control
arm.

1. **The drift gate passes on the pooled rule and fails on the maximum rule.**
   Estimator: maximum absolute difference in realised true J over n in
   {5, 10, 20, 40}, 2,000 replicates per cell. Direction: below 0.02 pooled,
   above 0.10 maximum. This is the prediction most exposed to the simulator being
   wrong about its own noise model, because no quantity has ever been elicited in
   this harness and the log-normal reconstruction is a reconstruction.

2. **The coverage gate passes on recomputation and reproduces under-coverage
   without it.** Estimator: realised two-sided interval coverage at n of 15 and
   20. Direction: 0.95 within Monte Carlo error recomputed, inside 0.61 to 0.85
   fixed.

3. **`t04` returns.** Under the log rule its movement reads 0.405, which clears
   any tau the pooled estimator produces at plausible sigma. Denominator: one
   item. Direction: unblocked. This is a check on the log scale rather than a
   result.

4. **The authoring yield clears 3 of 5 on `ledger` at K = 10.** Direction: at or
   above 0.60, against the 0.20 measured on `fit`. This is the prediction most
   exposed to wanting the venue to live, and the fourth consecutive prediction in
   this notebook of that shape.

5. **Specificity on Family A will sit below its structural ceiling by at least
   0.05.** Estimator: observed specificity against `specificity_ceiling(tau)`.
   Direction: strictly below. If it equals the ceiling, `k` is doing the work and
   the number says nothing about the model.

## Where I expect to be wrong

**The log scale is a change to the estimand, not only to the arithmetic.** Every
figure in `docs/TAILORING_CORPUS_SPEC.md` §7 about threshold independence is
stated in relative terms, including the interval `(0, 7/9)` the falsifier battery
is scoreable in. Those numbers do not travel to the log scale and must be
recomputed rather than converted in prose. If the battery's threshold-independent
interval turns out to be empty on the log scale, the log scale is wrong and this
entry is what it was wrong in.

**Prediction 4 is the one to watch.** The volume dial has never been tested, and
the argument for it is structural: difficulty bought from volume touches no
label, while difficulty bought from the matched arm's neutraliser is bought out
of that label's own defensibility, which is the mechanism behind the measured one
in five. The argument is clean and the evidence for it is zero items.

**Family B rests on a claim about base rates that is assumed here and measured
later.** Making the missing fact nameable in a fixed output block makes naming
salient in both arms at once, so the base rate rises in both and the difference
still identifies. That is the whole defence of `hinge` as a set-membership
instrument, and if the base rate saturates at 1.0 the specificity term dies and
`hinge` closes. Its control arm is what measures this.

**Sensitivity will be conditioned on items a model already re-derives.** The
authoring gate requires blind unanimity on the governing arm, so the corpus is
selected for items three blind instances agree on. That inflates sensitivity and
it is not an unbiased estimate. Where the gate can run on a weaker model than the
one under test, it will; where it cannot, this sentence is what the write-up
says.
