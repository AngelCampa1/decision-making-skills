# Track H — the `cascade` control screen: the third family ceilings

**Audience:** whoever reads this number next, and whoever is briefed to break it.

**Answer key:** `keys/C01-forge-lease-buyout-*.yaml` v3, matching the
`set_version: 3` stamped into all 40 rows of each of `readings-C01.jsonl`,
`readings-C02.jsonl` and `readings-C03.jsonl`. C02 and C03 carry their own keys
in the same directory, built to the contract read out of C01's key.

Prediction: [`notebook/2026-08-25-prediction-will-families-b-and-c-ceiling-too.md`](../../../notebook/2026-08-25-prediction-will-families-b-and-c-ceiling-too.md),
prediction 2, first committed at `cf7a3f8` and an ancestor of this run's commit.

**Repo commit at run time:** `c7b39eb`. Nothing in the repository was edited by
the run.

**Not a published run.** The 500 calls were dispatched directly rather than
through `scripts/run_triggers.py`, so there is no checkpoint, no
`total_cost_usd` from the runner, and nothing here belongs in
[`SCORECARD.md`](../../../SCORECARD.md). It is a screen that decides whether a
procedure has anything to work on.

## What was run

120 blind readings on `sonnet`, 20 per arm on three items, unaided — the item's
framing and format contract and nothing else. Then 380 adjudication calls: three
blind judges over both cells of all three items. Zero failed calls, zero
retries, zero isolation-receipt violations. USD 10.33 notional, which is a burn
meter rather than an expense.

`foreclosing-uncued` did not run. It carries `runnable: false`, its label has
never been adjudicated, and a miss there could be a correct answer.

## The primary

| item | sensitivity | false alarms | registered J | both cells adjudicated | 95% Newcombe |
|---|---|---|---|---|---|
| C01 | 20/20 | 0/20 | **+1.000** | +1.000 | [+0.772, +1.000] |
| C02 | 20/20 | 0/20 | **+1.000** | +1.000 | [+0.772, +1.000] |
| C03 | 18/20 | 0/20 | **+0.850** | +0.950 | [+0.704, +0.991] |

**The registered kill at 0.70 fires on all three items.** Format-violation gap
is +0.000 everywhere, `dual_container` is 0, and all 120 replies produced all
four contract blocks.

Adjudication coverage is 1.000 on all six cells. Movement is 0.000 on five of
them and 0.091 at most, against a registered `adjudication_movement` threshold
of 0.20 that could fire and did not.

## The number rests on one guard list, and both halves belong together

`ROUND_EXCLUSIONS` carries 7 of C01's 20 hits. On the same 40 replies:

| C01 scoring | sensitivity | J |
|---|---|---|
| key as shipped | 20/20 | **+1.000** |
| `ROUND_EXCLUSIONS` removed | 13/20 | **+0.650 — kill does not fire** |
| removed, both cells adjudicated | 20/20 | **+1.000** |

All seven are the model correctly saying she can apply in the 2030 round from
new premises, matched by round-agnostic accept phrases and saved by the
exclusion. The blind judges ratify all seven, so the **machine** number is one
author-written list away from failing its kill and the **adjudicated** number is
not. Anyone quoting +1.000 needs both rows.

## C02 and C03 keys were changed after their readings were seen

The change came from a rule written down before the strings were, and every
string traces to a key field authored before any reply existed. It is still not
a blind key and is not presented as one. The veto fires only inside `STILL CAN`
and neither control arm's `CANNOT` names the target, so the change is
one-directional and can only raise J.

| | machine | registered J | both cells |
|---|---|---|---|
| C02 shipped / fixed | 19/20 → 20/20 | +0.950 → +1.000 | **+1.000 either way** |
| C03 shipped / fixed | 17/20 → 18/20 | +0.850 → +0.850 | **+0.950 either way** |

The key change moves the machine number and never the adjudicated one.
Re-resolving C02 under the fixed key cost zero new judge calls, because the
judges never see a key. **Numbers under the fixed key are scorer diagnostics;
the adjudication is the measurement.**

## Two validity checks produced no reading, and a third cannot fire

`cue_ablation` and `still_can_as_treatment` **cannot be read from this run at
all** — the uncued arm is blocked and only the `with STILL CAN` level of that
factor ran. The ceiling is measured in the cued arm, where the stated facts
genuinely close the routes.

`accepts_list_gap` **cannot fire on C02 or C03.** `chain_accepts` and
`EXTRA_ENGAGEMENT` were module globals rather than `Rules` fields, so both items
had engagement scanned against C01's vocabulary; engagement then collapses onto
each item's own accepts list, `misses_engaged` cannot exceed zero, and the
threshold is arithmetically incapable of firing. C03's own two misses are
exactly the gap it was built to size and it can count neither. The same defect
class was diagnosed in the v3 note, one instance was promoted to a `Rules`
field, and two were left behind — and no gate could see it.

Two of five registered thresholds produced no reading and a third is inert on
two of three items.

## The direction of the errors, and the queue that cannot see it

Seven independent instances of the machine **losing** a hit and none
manufacturing one: C02's vetoed Culvery contract, C03's two accepts-list misses,
and the four from the `hinge` screen. **All seven sit in the negative cell**,
which the registered adjudication queue does not read and which `summarise()`
structurally cannot flip into. A registered queue that cannot see the direction
its own errors run is a finding about the design rather than about `cascade`.

The single counter-example was caused by the exclusion added after the data was
seen, firing by block-collapse accident.

## Reading-level noise, measured by accident

Two runners raced on one append-only file, which was recovered under a
deduplication rule fixed before the file was touched, with the 18 discards
parked in `readings-C03-parked.jsonl` rather than deleted. It left a free
test-retest: **2 of 19 identical prompts scored differently, 0.105, 95% Wilson
[0.029, 0.314]**, split 2/9 in the foreclosing arm and 0/10 in the effect arm.

Unplanned, unstratified, arms unbalanced, one item. It must never be cited as a
reliability study. It is also the only direct evidence of reading-level noise in
this project's record, including the screens that reported unanimity: a 20-of-20
arm is one sample of each of twenty prompts, and roughly one in ten would land
differently on a second draw.

The resume key made the race recoverable. It was not a guard, and nothing in the
harness prevented two writers on one file.

## The prediction was wrong in its number and wrong in its reason

Registered: **unaided J = 0.45**, below the kill, and named as the least
confident of the four. Observed +1.000, +1.000 and +0.850. The point estimate
sits far outside every interval and the kill fires on all three items.

The mechanism failed as well. The prediction was over-attribution to whatever is
vivid and nearby, and the effect arm's £12,600 repayment temptation is exactly
that — grant-shaped, four figures, one bullet from the target. **20 of 20 control
replies named it and kept it correctly separate from the grant, and 20 of 20
treatment replies said it is not triggered because she stops holding the
premises. Not one over-attribution in 40 readings.**

Prediction 4 — that at least one screen would be uninterpretable for a reason
that is not the model — holds on two of three screens. A registered arm that
produced nothing is the same shape as the `hinge` screen's dead decoys.

## What this cannot conclude

Three items at 40 readings each: a screen, and the intervals are over readings
rather than over items. The ceiling is measured only in the cued arm. Nothing
here tests volume, long context, delegation, or work carried across a
conversation.

Three families have now ceilinged on three constructs across six domains —
Family A at 1.000 over 99 readings, `hinge` at +0.950 hand-adjudicated, and this
one. The reading available is that a decision problem compact enough to fit one
prompt is not, for a current model, hard. It says nothing about whether the
procedures help at a scale this venue cannot reach.

## What is here

`readings-C0*.jsonl` are every reply verbatim with its isolation receipt.
`readings-C03-parked.jsonl` holds the race's discards. `adjudication/` carries
both cells for all three items and every judge call. `keys/` holds the answer
keys as authored. `analysis/` holds the scored output, the sensitivity grid, the
interval derivation, the resample figure and the incident record.

The scoring code is not here. It fails `ruff check` and `ruff format`, and
`de check` runs ruff over the whole repository, so landing it would mean
reformatting the scorer into something other than the scorer that ran. It lives
with the run's working files, and the keys plus `readings-*.jsonl` are enough to
check any label by hand.

## Correction, 2026-08-31

Found during the pre-submission audit of `paper/`. Appended, not edited in.

- **"380 adjudication calls" is 361.** `wc -l adjudication/judge-calls*.jsonl`
  gives 120 + 121 + 120. `analysis/INCIDENTS.md` independently says 360
  judgments over 120 cases and three judges; the 361st is the duplicate from the
  race that file records. The 500-call total above still decomposes: 120
  readings, 19 parked, 361 judge calls.
- **"0.000 on five of them" is four.** Movement is 0.000 on `adjudicated.json`,
  `-negative`, `-C02` and `-C02-negative`; 0.056 on `-C03` and 0.091 on
  `-C03-negative`.
- **"the 18 discards" is 19.** `readings-C03-parked.jsonl` holds 19, the next
  line of this README says "2 of 19", and `analysis/RESAMPLE.txt` gives 19
  prompts by arm 9/10. `analysis/INCIDENTS.md`'s "18 readings" and "17 of 18"
  carry the same error, and the `readings-C03-duplicates.jsonl` it names does
  not exist.
