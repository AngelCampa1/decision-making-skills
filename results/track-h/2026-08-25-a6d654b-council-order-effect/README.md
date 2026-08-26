# Track H — the `council` order-effect primary: no order effect, and the screen was the defective instrument

**Audience:** whoever reads this number next, and whoever is briefed to break it.

**Answer key:** `items/K*.yaml` v2, matching the `set_version: 2` on all twenty
item files. **No key decides any item here.** `council` is the one construct in
this programme with no answer key: the two orderings are scored against each
other, and the version governs the corpus rather than a label. The runner did
not stamp `set_version` into its records, so it is carried in
`draws-index.json` and sourced from the item files. `records/` holds every reply
exactly as written, unaltered, and nothing here is a `RunRecord` checkpoint.

Prediction: [`notebook/2026-08-25-prediction-will-families-b-and-c-ceiling-too.md`](../../../notebook/2026-08-25-prediction-will-families-b-and-c-ceiling-too.md),
prediction 3, first committed at `cf7a3f8` and an ancestor of this run's commit.

**Repo commit at run time:** `c7b39eb`. Nothing in the repository was edited by
the run.

**Not a published run.** Dispatched directly rather than through
`scripts/run_triggers.py`, so there is no checkpoint and nothing here belongs in
[`SCORECARD.md`](../../../SCORECARD.md).

## What was run

An admission screen of 41 draws, then the primary at **176 draws**: eleven items,
both orderings, eight draws each. All on `sonnet`. **Zero failed calls of any
kind**, 176 of 176 recorded, 176 clean isolation receipts, 176 distinct working
directories, zero replacement characters. USD 24.60 notional for the primary and
USD 5.82 for the screen, which is a burn meter rather than an expense.

Nine items are the pre-registered primary. The two the screen rejected are a
separately reported stratum and the two sets are never pooled.

## The primary

**Second-position rate 0.4722** on 144 kept committed records, 68 of them
second-position. Exact two-sided p **0.5598**, 95% CI **[0.3885, 0.5571]**. The
null under balanced orderings is exactly 0.5 and the interval contains it.

**No order effect is reported.** Delivered joint power 0.695 against the
registered 0.685.

**Every exclusion class is zero.** `BALANCED` 0, `OFF_MENU` 0, `AMBIGUOUS` 0,
`NO_CALL` 0, in both orderings, with the four arms that did not run printed as
zero rows. Nothing left any denominator, `u = 1.000`, and attrition by ordering
is 88/88 against 88/88, Fisher p 1.0000.

### The pooled rate hides the finding

Eight of the nine admitted items named the same course 16 times out of 16, with
*identical* counts under both orderings. Under balanced orderings a purely
content-driven answer produces exactly 0.5 — so those eight sit at the null for
the one reason a null rate does not license calling a model indifferent: total
order-blindness with a hard content preference.

This is the case the second-position-rate ruling was made for. The flip rate
would have read 0.000 here and called it the same thing.

Three items depart, and all three are **primacy**: K06 0.250, K09 0.312, K03
0.438. Three of three in one direction is a sign test at p 0.25 — a direction,
and not a finding.

## The recorded stratum, never pooled

K03 and K09 together: **0.3750** on 32 records, p 0.2153, CI [0.2110, 0.5631],
primacy. Fisher against the admitted set gives p 0.3348, so the two sets are not
distinguished.

Pearson r between an item's within-ordering instability and its |rate − 0.5| is
**+0.959** across all eleven items. That is not definitional — a pure position
effect would give instability 0 with |rate − 0.5| = 0.5. Departures here travel
with internal instability, which reads more like sampling variation than like a
position preference.

## The screen was the defective instrument

The admission screen rejected K03 and K09 for disagreeing under a single
ordering, and the primary shows what that gate actually did.

A four-draw unanimity screen rejects an item of consistency `p` with probability
`1 − p⁴ − (1−p)⁴`. K03 is 7 of 8 consistent under AB, so **that screen rejects
it 41.4% of the time**. K09 at 5 of 8 rejects 82.8% of the time and is a real
property of the item. **The gate could not tell those two apart**, which is the
Family A G1 correction arriving in a second venue: a gate that cannot separate
ambiguity from difficulty should record rather than cut.

One correction to the record of why: K09's rejection was *partly a parse
artefact*. The shipped screen rejected it on `no_call/no_call/first`, and under
the fixed parser it reads `first/second/first`. Same verdict either way, but the
stated reason was not the operative one at the time.

## The markdown-rule defect, measured

The screen lost two draws because the extractor read the line after a markdown
horizontal rule. That was called arm-correlated attrition reading high on
treatment, and the fix landed before this run.

Realised cost here: **164 of 176 replies carry a thematic break somewhere, and
zero carry one inside the `CALL` block.** All 176 `CALL` blocks hold exactly one
line. Attrition the shipped parser would have taken is **0 of 176, CI [0.0000,
0.0207]**, against the screen's 2 of 41.

The defect was real and the fix is right; its realised cost in this run was
nothing. The arm-correlation hypothesis is **untestable on one arm** — this
measures the floor in the arm where nothing asks the model to structure its
output.

## The leak residual is zero, computed rather than assumed

Every item realised exactly eight committed draws under each ordering, so
`C_AB = C_BA = 8` for all eleven, `g = 0`, and the trim discarded nothing. The
untrimmed pooled rate 0.4722 equals the equal-weight per-item mean 0.4722 to
four places. **Realised leak 0.0000 exactly**, largest single-item leak 0.0000.

## The prediction was wrong in magnitude and in direction

Registered: **true second-position rate 0.60**. Observed **0.4722**, CI [0.3885,
0.5571] — 0.60 sits outside it. On the recorded stratum, which the attenuation
argument said should show *more* order dependence, it is 0.3750, CI [0.2110,
0.5631], and 0.60 is outside that too. And 0.60 was a **recency** prediction,
while every departure observed is **primacy**.

The commit-rate half stays on record as a loss. Registered 0.70; the screen
measured 39/41 = 0.951, CI [0.8347, 0.9940], and this run measured **144/144 =
1.000**, CI [0.9747, 1.0000]. Both exclude 0.70.

Prediction 4 — that at least one screen would be uninterpretable for a reason
that is not the model — **did not fire on this primary**. There is no
reason-that-is-not-the-model to discount it. The nearest thing to a hit is that
the *screen*, rather than the primary, turned out to be the defective
instrument.

## What this decides

The pre-registration for the `council` skill arm made the issuing decision in
advance, as a function of the measured control rate: below a |departure| that
puts ρ_off under 0.566, **the skill arm is not issued**. At 0.4722 the departure
is 0.028 and the arm is not issued. That decision was registered before this
number existed and it saves 2,552 calls.

`council` was the last construct in the programme with no answer key and
therefore no way to ceiling the way the other three did. It did not ceiling. It
returned a null: on this corpus there is no order effect for a procedure to fix.

## What this cannot conclude

Nine items in the primary and two in the recorded stratum, one venue,
single-call draws, one model. A null on the `undefeated` stratum says that
content settles these items for this model; it does not say position never moves
a recommendation. The `asymmetric` stratum, which would give the specificity
half of the design, has no items.

And the corpus carries one quirk nothing in the gate checks: K07 and K10 both
use `HAVERSHOLT` as their first course. Calls are stateless so it cannot leak
between items.

## What is here

`records/` holds all 176 replies verbatim plus their attempt records, exactly as
the runner wrote them. `draws-index.json` indexes them and carries the corpus
version; it is an index rather than a checkpoint, because `council`'s record
shape is its own and `load_records` was never meant to read it. `prompts/` holds the 22 stripped prompts — only `prompt`
and `format_contract` ever reached a call, under opaque shuffled ids.
`screen/` holds the admission screen and its 41 records. `items/` holds the
twenty item files with their authoring records. `analysis/` holds the full
242-line report, the battery before and after the two defect fixes, and the v2
design note.
