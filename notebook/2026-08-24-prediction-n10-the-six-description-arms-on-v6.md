# 2026-08-24 — prediction: N10, the six description arms on v6

Registered **before the first call** and committed before the run is launched.

## Why this run exists

The corpus moved to answer key **v6** and every published trigger number was
scored at **v4**. `label_versions_comparable` refuses the comparison, so nothing
on record describes the corpus on disk. This run rebuilds the baseline that
every downstream arm is scored against.

## What runs

Six arms — `full`, `no-exclusions`, `opener-only`, `no-opener`, `stakes-named`,
`stakes-shown` — × **330 items** × 2 repeats = **3,960 calls**, `haiku`, through
`claude -p`, answer key **v6**.

The call arithmetic is recomputed here at 330 rather than carried. Track N's
registered run sizes derive from 258 items at v4 in three places; those are
registered numbers for runs that have not happened and they stay as written.

Serial. `scripts/run_triggers.py` has no concurrency of any kind, and wiring the
2026-08-20 falsifier's result into it would be new code on the path that
produces every published number. Roughly fifteen hours, checkpointed and
resumable, which is what the checkpoint is for.

## What the corpus did between v4 and v6, checked rather than assumed

`ancestry:` warns against carrying a per-item fact across corpus versions, so
the two hops were diffed with the repository's own loader before any figure
below was reused.

**All 258 v4 items are present at v6 with turn text, label and route
byte-identical.** The 72 items added at v5 are entirely new, and the three asks
the v6 bump rewrote — `l24n1`, `m25p`, `m29n2` — are among those 72 and have
never existed at v4. So v4 per-item facts carry for the carried 258 and there
is nothing measured about the other 72.

| | items | positives | negatives |
|---|---|---|---|
| carried from v4 | 258 | 86 | 172 |
| new at v5 | 72 | 24 | 48 |
| **v6** | **330** | **110** | **220** |

The 24 new positives are 12 `council` and 12 `hinge`, six per band. Those are
the two procedures that had no positives to be correct about until v5, which is
what made every routing number computed on v4 a six-way choice graded against a
four-way key.

## What will be computed, from which records, over which denominator

- **Per arm:** `trigger_arms.summarise` over 660 parsed records — accuracy,
  precision, recall and FPR, record-weighted and item-weighted.
- **Carried against new:** the same rates over the 258-item and 72-item subsets
  separately. The subsets are disjoint and the split is by item id.
- **Routing:** `trigger_arms.routing_by_procedure` under both the `first` and
  `any` rules, which disagree on this corpus and are both printed.
- **By band:** FPR and accuracy per `s`/`m`/`l`/`xl`.
- **Pooled item analysis:** `trigger_arms.item_analysis` over all six arms via
  `--pool`, a denominator of 12 respondents, which is the registered set.
- **Not computed:** no cross-version comparison against N6 or N7. Six arms
  compared pairwise is fifteen comparisons and this run has no multiplicity
  control, so no p-value is offered on the arm ordering.

## The baselines these predictions are registered against

All from the six published v4 arms, 12 respondents over 258 items, recomputed
from the records rather than read off the run READMEs. The recomputation
reproduces the published N6 and N7 table exactly, which is the check that the
scorer here reads the same object those runs did.

| quantity | v4 |
|---|---|
| per-item recall ceiling on the 86 positives | **1.0000** |
| positives firing on every one of 12 respondents | 81 / 86 |
| negatives never false-firing on any respondent | 103 / 172 |
| negatives false-firing on every respondent | 1 (`l19n1`), an FPR floor of 0.0058 |
| pooled firing on positives | 0.9913 |
| routed correct when fired, four registered routes | 0.5327 |

Per route, routed correct when fired: `cascade` 0.8586, `timing` 0.8371, `fit`
0.7500, `ledger` 0.4369.

## Predictions

**1. The instrument check, and the only one whose failure invalidates the
rest.** Per-arm recall on the 258 carried items lands within ±0.02 of its v4
value (`full` 0.9651, `opener-only` 0.9884, `stakes-shown` 0.9942, and 1.0000
for `no-exclusions`, `no-opener` and `stakes-named`). The items are
byte-identical and the model and tier are unchanged; only the corpus around them
grew. A larger move means something other than the description changed, and the
other five predictions should not be read until that is explained.

**2. The 24 new `council` and `hinge` positives fire at a lower rate than the 86
carried positives, in every arm.** Pooled carried firing at v4 was 0.9913. The
carried positives were authored against a four-procedure router and have been
through six arms; these 24 have been seen by nothing. Direction registered,
magnitude not.

**3. Routing to `council` and `hinge`, when fired, is below 0.5327**, the pooled
figure the four established routes reached at v4. The shipped description
enumerates six procedures and two of them have never been measured against a
positive.

**4. `ledger` stays the weakest of the four carried routes**, and its
misroutings continue to concentrate on `cascade`. At v4 it routed correct on
0.4369 of its fires against `cascade`'s 0.8586. This is the carried-route
prediction that can fail cleanly, and S9 retargeted `ledger`'s router row
against exactly that confusion pair.

**5. The FPR ordering survives the 48 new negatives.** `no-exclusions` and
`opener-only` remain the two highest-FPR arms, and remain separated from the
highest of the other four by more than 0.10. At v4 that gap was 0.2500 against
0.0988. If it closes, the v4 FPR result was a property of that negative set
rather than of the descriptions.

**6. Recall is saturated, so the band goes where it can fail.** The per-item
ceiling on the carried subset is 1.0000 — every one of the 86 positives fired on
at least one of 12 respondents — and three arms already sit at 1.0000. A recall
band under that ceiling cannot fail on the carried items, and registering one
would be theatre. **The band is registered on the 24 new positives instead: no
arm reaches 1.0000 recall on them.**

## Where I expect to be wrong

**Prediction 5 is the shakiest.** The v4 FPR gap rests on a negative set of 172
items authored alongside the positives they sit with. The 48 new negatives were
authored later, for triples whose positives route to procedures the earlier
negatives were never written against. A gap that closes is at least as
interesting as one that holds, and it would say the exclusion clause's measured
value was specific to how those first negatives were written.

**Prediction 2 could be met for an uninteresting reason.** If the new positives
fire lower simply because they are harder turns rather than because `council`
and `hinge` are unfamiliar to the description, the direction is met and the
mechanism is not tested. The check is prediction 3: if firing drops and routing
is fine, the items are harder. If firing drops and routing to the two new
procedures is bad, the description is the thing that has not caught up.

**Prediction 1 is the one I most expect to hold, and holding buys the most.** It
is the closest thing this instrument has ever had to a free replication: the same
258 items, the same model, the same tier, six arms, one corpus revision apart.
Nothing has ever re-run an arm on unchanged items before.

## The void condition

A parse rate below the coded 0.90 floor over **all** repeats voids the run, per
`parse_rate_over_all_repeats`. No separate higher floor is registered here. The
0.95 that N9 registered against a 0.90 code floor was never forced to matter
because every reading there sat below both, and carrying two numbers forward
without deciding between them is how that ambiguity survived.
