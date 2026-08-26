# `cascade` control screen: three items, 120 blind readings, unaided

**Audience:** whoever reads these numbers next, and whoever is briefed to break them.

**Answer keys.** C01 `set_version: 3`, version 4 primary. C02 and C03
`set_version: 3`, scored against the `Rules` their own keys license. **C02 and
C03 keys were changed during this run**; §6 says how and why, and every figure
below is given under both versions.

**Prediction under test.**
`notebook/2026-08-25-prediction-will-families-b-and-c-ceiling-too.md`,
predictions 2 and 4.

**Repo commit:** `c7b39eb`, clean before and after. Nothing under
`D:\code\decision-making` was edited. Everything here is scratchpad.

---

## 1. What ran

500 calls, all `sonnet`, all resolved to `claude-sonnet-4-6` off the assistant
event. **Zero failed calls, zero rate limits, zero retries, zero isolation
violations** across all 139 reading calls and all 361 judge calls.

| | calls | notional |
|---|---|---|
| C01 readings | 40 | $2.21 |
| C02 readings | 40 | $2.87 |
| C03 readings | 40 | $2.42 |
| C03 duplicate readings (§7) | 19 | $1.16 |
| judges, C01 both cells | 120 | $0.47 |
| judges, C02 both cells | 120 | $0.61 |
| judges, C03 both cells | 121 | $0.59 |
| **total** | **500** | **$10.33** |

Notional cost on a Max subscription. Never an expense.

**Isolation.** Fresh temp working directory per call, prompt on stdin,
`ISOLATION_FLAGS` copied verbatim from the repository provider and checked
against it at startup. Receipt asserted per call: 0 tools, 0 skills, 0 slash
commands, 0 MCP servers, on all 139 reading calls.

**Blindness.** `key` and `meta` popped from the loaded YAML before a byte is
rendered; emitted files re-read by a process that writes nothing and checked
against every key sentence of 40 characters or more; zero leaks. One hash-named
directory per arm, opaque shuffled reading ids under seed 20260825, manifest
outside both arms. Judges see one reply and the proposition — never a key, a
scorer verdict, an arm, another judge, or a second reply.

**The uncued arm did not run.** `assert_runnable("foreclosing-uncued", ...)`
raises `Unadjudicated`; asserted at plan-build time and again by the verifier.
Not laid out, not called, not scored.

**Instrument checked before a call was spent.** `cascade_battery.py` exits 0 and
is byte-identical under `PYTHONHASHSEED` 0, 1, 42 and 99 and to the published
`battery-output.txt`, md5 `0c2404dec6516ee839e63fa3da8fd14c`. Re-verified after
every scorer change in §5; still identical.

## 2. Per-arm counts

Format violations were zero everywhere: every one of the 120 replies produced
all four contract blocks.

| | C01 | C02 | C03 |
|---|---|---|---|
| foreclosing N | 20 | 20 | 20 |
| hits / misses (machine, final key) | 20 / 0 | 20 / 0 | 18 / 2 |
| effect N | 20 | 20 | 20 |
| false alarms / correct rejections | 0 / 20 | 0 / 20 | 0 / 20 |
| format violations, both arms | 0, 0 | 0, 0 | 0, 0 |
| **format-violation gap** | **+0.000** | **+0.000** | **+0.000** |
| `dual_container` | 0 | 0 | 0 |
| engagement, treatment | 20/20 | 20/20 | 18/20 |
| engagement, effect | 20/20 | 19/20 | 18/20 |
| `explicit_survival` | 20 | 6 | 10 |
| `STILL CAN` vetoes | 0 | 0 | 0 |
| hedges | 0 | 0 | 0 |
| engaged misses | 0 | 0 | 1 |
| guard-disagreement | 0 | 0 | 0 |
| chain-only / skill containers | 0 / 0 | 0 / 0 | 0 / 0 |

C01's `explicit_survival` is 20 and all 20 are effect-arm: the control replies
put the grant round in `STILL CAN`, which is correct there. No treatment reply
in any item did.

Output length was matched across C01's arms (median 3740 vs 3438 output tokens)
and **not** across C02's (3346 vs 5760). The version 4 primary divides by
nothing the model controls, so that asymmetry does not touch it. Version 2's
gated figure divides by engagement and would have moved.

## 3. Both adjudication cells, all three items

Three blind judges per case, `ADJUDICATORS = 3`, resolution rule fixed before
any judge ran: unanimous with the scorer keeps; 2-of-3 against moves; 2-1
agreeing keeps and is recorded contested; an unreadable reply is a missing
measurement, not a vote. 361 judge calls, **zero unparseable**.

| item | cell | n | coverage | movement | vs 0.20 |
|---|---|---|---|---|---|
| C01 | positive | 20 | 1.000 | 0.000 | does not fire |
| C01 | negative | 20 | 1.000 | 0.000 | does not fire |
| C02 | positive | 20 | 1.000 | 0.000 | does not fire |
| C02 | negative | 20 | 1.000 | 0.000 | does not fire |
| C03 | positive | 18 | 1.000 | 0.056 | does not fire |
| C03 | negative | 22 | 1.000 | 0.091 | does not fire |

### Every disagreement, with direction

**Machine lost a hit — 3 instances, all in the negative cell:**

- `a2b152fdabc39db6` (C02, foreclosing, judges 3–0 True). `CANNOT` reads
  *"Fulfill the Culvery 2027 contract (maximum capacity with one boat is 3,120
  tonnes against 5,600 contracted, with no let-out)"*. Vetoed under the shipped
  key because `STILL CAN` carried the accepted string `spring contract` inside a
  clause about the Hallowmarsh berth. Missing exclusion set.
- `ac33a96797a84a2c` (C03, foreclosing, judges 3–0 True). *"File a valid
  application to the Ashcombe Design Registry for Tidewrack"* — correct, and the
  accepts hold `application for tidewrack` as a contiguous phrase, so the
  intervening words break the match.
- `699df63424335331` (C03, foreclosing, judges 3–0 True). *"File a registration
  for Tidewrack at the Ashcombe Design Registry"* — `registration for Tidewrack`
  is not on the list; `tidewrack registration` and `registration of tidewrack`
  are.

**Machine gained a hit — 1 instance, in the positive cell, and I caused it:**

- `57df316426dea391` (C03, foreclosing, judges 3–0 False). Under the key I
  patched in §6 this scored `hit`; the judges removed it. Their reasoning is
  correct: the reply's `STILL CAN` says she can *"File Tidewrack for
  registration after it comes off the loom on 2026-10-20, provided you have not
  shown it publicly first"*, which preserves the ability conditionally. The
  exclusion that produced the false hit was `standing order` — sitting in a
  **different** `STILL CAN` entry, sharing a unit with `file tidewrack` only
  because the block carries no bullet markers and collapses to one entry (§5).
  So this is the block-collapse defect biting my own list, in the direction the
  one-directional bias predicts.

### The direction result, and why the registered design cannot see it

Three instances here plus hinge's four make **seven independent instances of the
machine losing a hit and none of it manufacturing one**, across two screens and
four items. **Every one of the seven sits in the negative cell.** The registered
adjudication queue is the positive cell only, and `summarise()` flips positives
to negatives and nothing else, so a wrongly vetoed hit cannot travel through the
registered estimator at all.

**A registered adjudication queue that structurally cannot see the direction its
own errors run is a general finding about this design, not a `cascade` detail.**
The single counter-example is the one I introduced by changing a key after
seeing the data, which is the exception that names the rule.

## 4. The primary, with the fragility in the same breath

`Summary.youden_j` returns a `Refusal` until the positive cell is fully
adjudicated. Before adjudication every item read
`REFUSED - 0 of N scored positives carry an adjudicated label`, and a numeric
format spec on it raised `Unpublishable`. Nothing routed around it.

| | registered J | both cells | 95% Newcombe |
|---|---|---|---|
| **C01** | **+1.000** | +1.000 | [+0.772, +1.000] |
| **C02** (fixed key) | **+1.000** | +1.000 | [+0.772, +1.000] |
| **C03** (either key) | **+0.850** | +0.950 | [+0.704, +0.991] |

"Both cells" applies the negative cell's verdicts too. It is **not producible by
the registered estimator** and is labelled as such, the way `hinge` labelled its
hand-adjudicated +0.950.

Alternate readings on C01, same replies: chain strings in +1.000, alternate
guard list +1.000. These bound two lists' disagreement with each other, never
their error. Version 2's gated figure +1.000, a sensitivity analysis and never
the primary.

The bootstrap is **[+1.000, +1.000]** on C01 and is worthless: both cells sit on
their boundary so every replicate draws the same value. Recorded so nobody
re-derives zero width and reads it as precision.

### `ROUND_EXCLUSIONS` — the machine number is one guard list from failing its kill

| C01, same 40 replies | sensitivity | registered J |
|---|---|---|
| key as shipped | 20/20 | **+1.000** |
| `ROUND_EXCLUSIONS` removed | 13/20 | **+0.650 — kill does not fire** |
| removed, both cells adjudicated | 20/20 | **+1.000** |

Seven of twenty C01 hits rest on that list. All seven are the model correctly
saying she can apply in the **2030** round from new premises — caught by
round-agnostic accepts (`continuity grant`, `grant round`), saved by `2030` /
`new premises` / `other premises`:

- `pursue the workshop continuity grant in the 2030 round if she establishes three years of unbroken occupation at new premises`
- `apply for the 2030 grant round at a new address, provided she is established there by early 2027`
- `pursue the workshop continuity grant in 2030 if she has held new premises continuously for three years by then`
- `apply for the 2030 workshop continuity grant if she is three continuous years into a new premises by then`
- `apply for the 2030 grant round if you establish and hold new premises continuously for three years before then`
- `apply for the 2030 workshop continuity grant if she holds new premises continuously for three years by then`
- `apply for the 2030 workshop continuity grant if she establishes three continuous years at a new workshop before that round opens`

**Both halves, together: the machine number flips on one author-written list;
the adjudicated number does not.** Run the un-excluded key past the blind judges
and it returns to +1.000 — they ratify all seven. A reader quoting +1.000
without the middle row is quoting something they do not have.

## 5. Two thresholds and a battery that could not fail

### `accepts_list_gap` is a validity check that cannot fire on two of three items

`chain_accepts` and `EXTRA_ENGAGEMENT` were module globals, not `Rules` fields.
`score_response` read them off the module, so C02 and C03 had engagement scanned
against **C01's** vocabulary — the pneumatic hammer, the Craft Trades Board, the
2027 round dates. Engagement then collapses onto each item's own accepts list,
`misses_engaged` cannot exceed zero, and the threshold is **arithmetically
incapable of firing**.

The threshold sizes the accepts list's false-negative contribution using replies
that reached the target and were not credited. A reply can only be an engaged
miss if the engagement vocabulary is strictly wider than the accepts list. For
C02 and C03 the two sets are equal.

**This is §5 of the v3 note recurring verbatim.** That note's lesson is that a
scoring choice which cannot be expressed as a configuration cannot be falsified;
container precedence was promoted to a `Rules` field for exactly this reason,
and these two were left behind. The same defect class was diagnosed, one
instance was fixed, two were not, and **no gate could see it** — nothing in the
repository reads whether a registered threshold is reachable.

C03's own two treatment misses are that gap: both are correct answers lost to
contiguous-phrase matching, both carry `engaged = False`, and the threshold
built to size exactly this cannot count either of them.

**Promoted, since it was cheap.** `Rules.chain_accepts` and
`Rules.extra_engagement` are now fields; `items.rules_for` reads them from each
key; an item stating none gets empty sets rather than C01's;
`items.engagement_is_inert` reports whether the threshold can fire at all, and
prints `accepts_list_gap CANNOT FIRE` for C02 and C03. C01's key now states the
eight strings the module already applied to it, so key and module agree on all
five string sets. `battery_exclusions.py` gives the new field a sole witness.
**The battery output is still byte-identical under all four hash seeds** — the
promotion changes no verdict. `cascade` has fired its kill and the venue is
closing, so the fix changes nothing; the write-up is what survives.

### The battery's fixtures cannot reach the state the live venue produces

**Not one reply in 160 answer blocks across three items used a bullet marker.**
`entries()` folds a block into one entry when no line matches `_BULLET`, so the
live `scope: "sentence"` ran as `scope: "block"` — the scope the v3 note calls
wrong — on 67 of 80 C01 blocks, 72 of 80 C02, 61 of 80 C03.

`battery_exclusions.py` asserts this rather than describing it. `U1` and `B1`
are the same prose differing only in a bullet prefix: `U1` folds to one entry
and scores **`miss`**, `B1` keeps three and scores **`hit`**. On `U1`, `sentence`
and `block` scope are indistinguishable; on `B1` they are — and `B1` is the only
state the v3 battery's fixtures ever occupy.

**A battery whose fixtures cannot reach the live input state is testing a venue
that does not exist.** On C01 this did not change a verdict. On C03 it decided
one: `57df316426dea391` in §3.

### Which registered thresholds could fire at all

| threshold | C01 | C02 | C03 |
|---|---|---|---|
| 1 `adjudication_movement` (> 0.20) | can fire; 0.000 / 0.000 | can fire; 0.000 / 0.000 | can fire; 0.056 / 0.091 |
| 2 `accepts_list_gap` (> 0.20) | can fire; 0.000 | **CANNOT FIRE** | **CANNOT FIRE** |
| 3 `cue_ablation` (> 20 pts) | **CANNOT BE READ** | — | — |
| 4 `still_can_as_treatment` (> 0.20) | **CANNOT BE READ** | — | — |
| 5 `adjudication_coverage` (= 1.000) | met, both cells | met, both cells | met, both cells |

Threshold 3 cannot be read because the uncued arm carries `runnable: false` and
produced zero readings. Threshold 4 cannot be read because only the
`with STILL CAN` level of the factor ran; the two `nostill` keys exist and were
not elicited against. **Two of five registered thresholds produced no reading at
all, and a third is inert on two of three items.**

The notebook's registered kill — unaided J at or above 0.70 — **FIRES on all
three items**, on the registered estimator and on the both-cells reading alike.

## 6. The C02 and C03 keys were changed after their readings were seen

`still_can_exclusions` was absent from both. Added by `patch_keys.py` from a
derivation rule written down in `../new-items/exclusions.json` before the
strings were: *the vocabulary by which the treatment arm's own
`still_available_after` entries distinguish what survives from the target, plus
the two generic paraphrase families C01 already uses.* Every string traces to a
key field authored before any reply existed. Backups of all six pre-change files
are in `keybak-*.yaml`.

**This is not a blind key and nothing here presents it as one.** The exclusion
set fires only inside `STILL CAN`, and in both items the control arm's `CANNOT`
never names the target, so a veto can only remove a treatment hit. The change is
**one-directional**: it can raise sensitivity, cannot raise the false-alarm
rate, and can only push J up. **Numbers under the fixed key are scorer
diagnostics; the adjudication is the measurement.**

| | machine | registered J | both cells |
|---|---|---|---|
| C02 shipped (no exclusions) | 19/20 | +0.950 | **+1.000** |
| C02 fixed | 20/20 | +1.000 | **+1.000** |
| C03 shipped (no exclusions) | 17/20 | +0.850 | **+0.950** |
| C03 fixed | 18/20 | +0.850 | **+0.950** |

**The key change moves the machine number and never the adjudicated one.** The
judges are scorer-independent — they were asked what a reply says about the
target, never what a key says — so the same verdicts arbitrate every key
version. Re-resolving C02 under the fixed key needed **zero new judge calls**.
And on C03 the one hit the new exclusions bought was taken straight back by the
judges.

**Mutant discipline, asserted in both directions.** `battery_exclusions.py`, 0
failures: witness `X1` scores `miss` under the un-excluded key and `hit` under
the fixed one; no other single-field mutant flips it except `still_veto=False`,
which is named rather than hidden. `v3/cascade_battery.py` is untouched.

## 7. The resample rate, and the incident that produced it

**Estimator.** The proportion of repeated prompts whose scored `outcome` differs
between two independent samples, both scored under the same `Rules`. Numerator:
pairs whose `score_response(...).outcome` differs. Denominator: every prompt with
two records.

**Result: 2 of 19 = 0.105, 95% Wilson [0.029, 0.314].** By arm: 2 of 9 in
foreclosing, 0 of 10 in effect. Both flips are `hit` to `miss` or back.

**Provenance, stated so this is never cited as a planned reliability study.** It
came from an incident. Two C03 runners raced — a chain script that appeared not
to have started, and a second runner begun by hand — and both appended to one
record file, which reached 47 records over 29 ids. Both were stopped. The file
was deduplicated under a rule fixed in the script's docstring before it touched
anything: **keep the earliest record per reading id by its `at` timestamp** —
not the longer one, not the one that scores better, not the last writer. The 19
discards were parked in `readings-C03-duplicates.jsonl`, not deleted. The run
resumed on the reading-id resume key. A single further duplicate appeared after
the first pass and was handled by the same rule.

The pairs were not designed, not stratified, and not balanced across arms. It is
one item.

**What it bears on.** It is the only direct evidence of reading-level noise
anywhere in this project's record, including the two screens that reported
unanimity. A screen reporting 20 of 20 in an arm is reporting one sample of each
of twenty prompts, and this says roughly one in ten would land differently on a
second draw.

**On the race itself: the resume key made it recoverable, it was not a guard.**
Nothing in the harness prevented two writers on one append-only record. The
reading-id resume key limited the damage and the timestamps made a rule
applicable, but neither is a lock. For a checkpointed runner at scale, an
undetected second writer is a void outcome rather than a noisy one.

Two further incidents are in `INCIDENTS.md`: a false alarm I raised about the
battery hashes and withdrew (my own `/tmp` glob picked up other sessions'
files), and a bug in my own analysis script — `adjudicated_path` built a
filename the adjudicator never writes, so negative-cell verdicts were silently
absent from C02 and C03 both-cells figures. It did not raise, because a missing
adjudication file is a legitimate state. Fixed, and `assert_paths_exist` now
refuses the silence. One figure reported before the fix (C02 both-cells) was
right by accident and one (C03) was wrong; both are corrected above.

## 8. Predictions, scored

**Prediction 2 — wrong in the number and wrong in the reason.** Registered
**0.45**, below the kill of 0.70. Observed **+1.000** on C01, **+1.000** on C02,
**+0.850** on C03. Every point estimate is far outside the registered value and
**the kill fires on all three items**.

The mechanism failed too. The prediction was over-attribution to the vivid and
nearby, and C01's control arm is built around exactly that: the £12,600 Hearth
Repair Grant repayment, grant-shaped, four figures, one bullet from the target.
**20 of 20 control replies named the £12,600 repayment in `CANNOT` and kept it
correctly separate from the grant, and 20 of 20 treatment replies said the
repayment is not triggered because she stops holding the premises. Not one
over-attribution in 40 readings.**

The venue's central construct claim held on live data: 6 of 20 C01 treatment
replies recommended doing something else instead of the plan, and **all 6 still
filed the foreclosure**. Reasoning well did not cost them the score.

**Prediction 4 — holds, on two of three screens.** `cascade` has the same shape
as `hinge`'s dead decoys: a registered arm that produced nothing. `cue_ablation`
and `still_can_as_treatment` **cannot be read from this run at all**, and the
ceiling is measured **only in the cued arm**, where the stated facts genuinely
close the routes. This screen is interpretable for the ceiling question and not
for whether the finality cue did the work.

## 9. What this cannot conclude

Three items, 40 readings each. A screen, not an estimate. The intervals are over
**readings of these items, not over items**, and §7 says roughly one reading in
ten is unstable on a resample.

A ceiling here says **these three items are easy for a current model, unaided,
in one call.** It does not say the procedure is useless. Nothing here tests
volume, long context, delegation, or work carried across a conversation, and the
failures the six procedures describe mostly do not happen inside a single call.

No skill arm ran. There is still no `on` record anywhere in this project, so
nothing here speaks to effect size for any procedure.

And the ceiling holds only where the prompt's stated facts close the routes.
Whether it survives where they do not is unknowable until the uncued arm has an
adjudicated label, and that arm is blocked.
