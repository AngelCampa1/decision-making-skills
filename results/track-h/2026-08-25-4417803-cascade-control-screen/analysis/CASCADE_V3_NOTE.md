# `cascade` C01: the primary at version 4, and what still gets past it

**Audience:** whoever builds or kills the decision-quality venue for `cascade`.

**What this is.** A primary that divides by nothing the model controls, a
survival rule that reads an observation instead of an idiom list, a scorer whose
container precedence cannot change between two runs of the same code, a battery
of forty-four replies and eleven mutants each with a sole witness, and five keys
of which one is authored and blocked from running.

Two adversarial reviews took the instrument apart. The first killed version 2's
estimator; the second killed version 3's scorer. What follows is what each broke,
what was repaired, and the four things that are recorded as limits rather than
fixed. **One of the second review's findings changes what may be published and it
is §3.**

---

## 1. The primary

For item C01, the primary is Youden's J on one target read in both arms,
**applying to the 2027 round of the Workshop Continuity Grant**: the proportion
of foreclosing-arm replies whose `CANNOT` block names it as lost, over every
scoreable foreclosing-arm reply, minus the same proportion in the effect arm,
over every scoreable effect-arm reply.

| | |
|---|---|
| **Estimator** | Youden's J, paired by item. `Summary.youden_j`. |
| **Records** | The `CANNOT` block of each reply, or `FORECLOSES` when the reply carries only that. A reply carrying both is read on `CANNOT`. Entries reassembled from wrapped lines, matched sentence by sentence. |
| **Sensitivity denominator** | Every foreclosing-arm reply that produced such a block. |
| **False-alarm denominator** | Every effect-arm reply that produced such a block. |
| **Survival rule** | A target named in `STILL CAN` decides against a positive in `CANNOT`, in both arms. |
| **Labels** | Every scored positive is queued for three-judge blind adjudication, and the adjudicated rate is what enters J. |

Both denominators are ungated. The primary reads one bit per reply. Everything
richer is a flag counted beside it.

## 2. The identity, published

Version 2 ran the false-alarm rate over replies that mentioned the target
somewhere. That is exact:

```
J_gated  =  sensitivity  −  FAR_ungated / engagement
```

It divides by the model's own verbosity. Two cohorts with the same four misfiles
in twenty score **0.500** and **0.800** under it and **0.800** under the current
primary. A terse model correct on 19 of 20 replies scores **0.000** under it
while a talkative model correct on 17 of 20 scores **0.700**. Both runs are in
the battery, Direction 3. `Summary.youden_j_gated` still computes it and prints
it as a sensitivity analysis with the identity below it, so nobody has to derive
it again.

## 3. A bracket built from two lists by one author is not an error bound

**This is a law and it is recorded as one.** Version 3 offered a narrow survival
guard list and a wider one, reported the count of replies whose verdict moved
between them as `guard_sensitive`, and wrote that the flag "says how often it may
be wrong". **That sentence is false and it is withdrawn in those words.** A
second review wrote fourteen ordinary survival phrasings; thirteen scored false
alarms with `guard_sensitive` false, because both lists agreed and both were
wrong. Three and a half such replies erase the primary. `guard_sensitive` may not
be reported as a residual-error estimate, and neither may `j_alternate_guards`.
Both are still computed and both are labelled as what they are: two lists
disagreeing with each other.

The repair is structural rather than lexical. **A target named in `STILL CAN`
decides against a positive in `CANNOT`.** That reads something the reply
observably did, it is what the block was added for, and it depends on nobody's
vocabulary. The guards stay as a fallback for replies carrying no `STILL CAN`
block at all.

What the structural rule cannot resolve goes to hand adjudication.
`adjudication_queue` counts the positive cell in both arms and
`adjudicated_fraction` says how much of it has a label behind it. **The primary
is refused, not warned about, until that fraction reaches its registered
threshold.** §3a.

### 3a. The refusal

`Summary.youden_j` returns a `Refusal` object rather than a number when the
positive cell is not fully adjudicated. `float()`, `int()`, any numeric format
spec, arithmetic and comparison all raise `Unpublishable`; the only thing a
caller can do with it is read the reason. This repository has twice shipped a
figure whose caveat existed and was dropped — 0.890 by counting words, and five
unearned points of recall. The number is what gets quoted and the warning is what
gets dropped, so there is no number to quote.

Two conditions hold it to its job.

**It refuses the primary and nothing else.** Sensitivity, the false-alarm rate,
every per-arm count, both engagement figures, all eleven secondaries and the
queue size still compute and still print, because those are what tell a reader
whether the adjudication is worth doing. The two alternate readings and version
2's gated figure are also withheld, because they are J as well.

**The threshold is registered and derived.** `adjudication_coverage = 1.000`,
full coverage of the positive cell, and it is derived from the movement
threshold rather than chosen. That threshold is defined over the positive cell:
more than 20% of positive labels moving means the scorer is not fit. A movement
rate computed over a subset cannot be compared to it, because the unadjudicated
remainder is unobserved and 20% within 80% coverage is indistinguishable from
36% over the whole. Partial coverage also leaves unquantified bias: 13 of 14
ordinary survival phrasings scored as positives the scorer got wrong, so an
unadjudicated remainder of size f admits up to f × FAR of bias in one arm and
the same again in the other. At FAR 0.3, leaving a fifth unadjudicated admits up
to 0.12 on J, over half the movement threshold it is meant to be read against.
The refusal cites the registered value in its own message.

Direction 3.5 runs the ladder: nothing adjudicated and half adjudicated both
refuse, full adjudication lifts the refusal to J = 0.500, and flipping one of
six labels moves it to 0.250 — which is why the movement threshold is read over
the whole cell rather than a sample of it.

**The same rule governs the uncued arm.** `assert_runnable()` raises
`Unadjudicated` for an arm carrying `runnable: false`, so scoring it refuses
rather than warns. The battery shows the cued arm loading and the uncued arm
raising.

The negative cell is taken as read, and the accepts-list gap that biases it has
its own registered threshold.

## 4. Container precedence, and why a `frozenset` was a defect

Version 3 held the container names in a `frozenset` and took `next(...)` over it.
Iteration order flips with the interpreter's hash seed: `['CANNOT','FORECLOSES']`
at seeds 0, 11 and 42 and `['FORECLOSES','CANNOT']` at 1, 7 and 99. A reply
carrying both containers was scored on whichever this process happened to order
first, the order is fixed within a process so every dual-container reply in a run
moved together, and dual containers concentrate in the skill-on arm.

`CANNOT_CONTAINERS` is now an ordered tuple and `Rules.container_precedence` is a
field, so the choice is expressible and the sole-witness discipline can reach it.
**Precedence goes to `CANNOT`**, and that is a choice with a reason: reading
`CANNOT` says the contract answer is the answer, reading `FORECLOSES` says the
skill's reasoning is, and scoring one arm on a container the other arm cannot
produce is scoring the two arms on different objects. `dual_container` counts the
exposure whether or not it bit. The whole battery is now byte-identical under
`PYTHONHASHSEED` 0, 1, 42 and 99.

## 5. The battery

`python cascade_battery.py`, no model calls, no network, no inputs. Forty-four
replies, eleven mutants, five cohorts, five keys. Full output in
`battery-output.txt`. Its Direction 1 summary:

```
  sensitivity        0.542   (13 hit / 24 scoreable treatment)
  false-alarm rate   0.278   (5 / 18 scoreable effect, nothing gated)
  PRIMARY  J         0.264      [readable]
    same replies, other readings: chain strings in 0.292   alternate guard list 0.333
      NOT an error bracket. Two lists by one author bound their disagreement with
      each other, never their error. The residual goes to adjudication below.
    version 2's gated figure 0.157   (SENSITIVITY ANALYSIS, never the primary)
      identity: J_gated = sensitivity - FAR / engagement
  engagement         treatment 0.875   effect 0.722   (reported, never divided by)
  format violations  treatment 1   effect 1   gap -0.013
  ADJUDICATION       queue 18 positive(s)   adjudicated 0.000   (the primary is not publishable until this is 1.000)
  secondaries        explicit survival 5   STILL CAN vetoes 2   dual containers 2
                     hedges 2   engaged misses 8   guard-disagreement 3   chain-only 4   skill containers 2
```

These are fixtures. The numbers say the scorer works. Nothing has been measured.

**Direction 2 requires a sole witness.** Each rule must be flipped by a reply no
other mutant flips. That requirement has now caught three inert rules across two
versions: `line` and `block` scope were indistinguishable until `units()` was
rewritten, the container rule had no witness until `G2` was written, and the
version 3 precedence defect was unreachable because precedence was not a `Rules`
field at all. A rule that cannot be expressed as a configuration cannot be
falsified by this battery, which is the general lesson.

## 6. The construct claim survived a direct attack

The second review wrote the reply that would have killed the venue: a model
running `cascade` Step 3, finding the order question, saying which order spends
the round, and reporting the foreclosure conditionally. **It scores a hit.**
`STEP3-order-found-and-reported` is that reply, in the battery.

The membership form does not inherit the scalar form's anti-correlation between
reasoning well and scoring well. In the cued arm the stated facts genuinely close
the routes, so a perfect reasoner has no resequencing to find and no reason to
withhold the foreclosure, and the contract gives the better plan its own block to
live in. That is disqualifier 12's Family B mitigation working under attack, and
it is the venue's central construct claim.

**What it does not establish.** It survives in the cued arm *because the stated
facts there genuinely close the routes*: the buyer wants the building empty and
will work it himself, so a perfect reasoner finds no resequencing that keeps the
round and has no reason to withhold the foreclosure. That is a property of this
prompt, not of the construct. Whether the claim survives where the facts do not
close the routes is **unknowable until the uncued arm has an adjudicated label**,
and that arm is blocked. Read the fixture as one arm's evidence, never as the
venue's.

## 7. The uncued arm does not run

Version 3 shipped `C01-forge-lease-buyout-foreclosing-uncued.yaml` carrying the
cued arm's `one_reading_check` byte for byte. That check asserts that a buyer who
will work the forge himself closes every route back in. **Its own prompt deletes
that buyer.** The file contradicted itself two hundred lines apart, and a `miss`
scored against it might have been a correct answer.

`one_reading_check` is now **replaced rather than supplemented**, and the
replacement reaches the opposite conclusion: with nothing stating that a buyer
wants the building empty, a licence back, a short sublet and a delayed completion
are open by silence, so a competent reader may decline to call the round
foreclosed. That is disqualifier 15 in its Family B form, the shape that got
`t01` and `t05` cut.

So the arm carries `runnable: false` and `label_status: unadjudicated`, and the
battery refuses if either changes without an adjudication record. It needs a
three-judge blind label before one reply is elicited against it.

**The hedge decomposition is retired.** Version 3 registered `resequencing-hedge`
as the instrument that would separate cue loss from route opening. It cannot:
`hedged` is set by whether the block opens with `NONE` or carries a conditional
idiom, it does not read why, and a cohort losing the cue raises it exactly as a
cohort finding a newly open route does. The confound stays registered and
undecomposed. Separating the two needs an instrument that reads the rationale and
none exists here.

## 8. The contract is a factor, not an assumption

Adding `STILL CAN` was justified on the grounds that it turns a correct rejection
from an inference into an observation. That is a claim about the instrument, and
if the block also helps the model then it is a treatment and every
skill-on-minus-skill-off figure computed under it is attenuated by construction.

A second review pointed out the asymmetry: a prompt-change objection got a whole
arm when it was about the finality cue and a recorded limit when it was about
`STILL CAN`. Upheld. `C01-forge-lease-buyout-foreclosing-nostill.yaml` and
`C01-forge-lease-buyout-effect-nostill.yaml` carry the version 1 three-block
contract and the version 4 key, so the design is
`{with STILL CAN, without} × {skill on, skill off}` and the registered read is
whether `J_off(with)` exceeds `J_off(without)`.

One limit on the factor, stated because it is real: no reply under the `without`
level can carry a `STILL CAN` block, so the structural survival rule never fires
there and every positive rests on the guard list alone. The two levels do not
have the same scorer.

## 9. The five registered thresholds

Each reuses the repository's only registered movement figure, 20% of labels
moving under three-instance blind adjudication, rather than inventing a number.
The reuse is the choice; the arithmetic says what it buys. `THRESHOLDS` in
`cascade_scoring.py` carries them in full.

1. **Adjudication movement.** More than 20% of positive labels moving under
   three-judge adjudication means the string scorer is not fit and the run is a
   scorer failure rather than a model result.
2. **Accepts-list gap.** `misses_engaged / scoreable_treatment` above 0.20 means
   sensitivity is understated by up to 20 points by the list alone and the list
   is the finding. The ratio is an upper bound on the list's false-negative
   contribution, because every engaged miss reached the target and was not
   credited.
3. **Cue ablation.** A sensitivity drop above 20 points between the cued and
   uncued arms. **Underpowered at ten replies per arm, and that is the finding.**
   The standard error of the difference at p near 0.5 is
   `sqrt(0.25/n + 0.25/n)`, which is 0.224 at n = 10, so the threshold sits
   inside one standard error; 80% power needs about
   `2 × (1.96 + 0.84)² × 0.25 / 0.04 = 98` replies per arm.
4. **`STILL CAN` as treatment.** `J_off(with)` exceeding `J_off(without)` by more
   than 0.20. Same figure, same source, same underpowering.
5. **Adjudication coverage.** Full coverage of the positive cell, derived from
   threshold 1 rather than chosen, and enforced by refusal rather than by a
   warning. §3a carries the derivation.

Version 3's "a wide bracket should not be reported" is **not** among them,
because §3 removed bracket width from the set of things that can license a
publication.

## 10. What is recorded rather than repaired

**A correct answer outside the accepts list scores a miss.** `D1` names the body,
the sum, the timing and the mechanism correctly and scores a miss. Widening the
list widens it in the control arm too. Sized by `misses_engaged` with threshold 2.

**The survival guards are a finite list over an open class, and no list bounds
its own error.** §3. The structural rule covers replies with a `STILL CAN` block;
`I2`, `I3` and `I4` have none and are still graded wrongly. They sit in the
adjudication queue, which is the only thing here that bounds the error.

**The two version 1 blind responses are not on record.** No raw transcript of
either exists in the repository; the only record is a prose summary in
`FAMILY_B_CASCADE_NOTE.md` §5. `T1` and `E1` are labelled `AUTHOR-WRITTEN`.
**Anything resting on them is unauditable, including the prediction that
specificity at 1.0 is the likeliest outcome.**

**`explicit_survival` may never be compared across skill-on and skill-off.**
`cascade.md` emits no block for what survives, so a skill-shaped reply
structurally cannot produce one and any difference would be the container rather
than the judgement.

**Two accepts strings are redundant.** `january 2027 round` and `£40,000 grant`
each contain a shorter string already on the list. Noted, not removed.

## 11. Ledger

The first review's thirteen objections, and the second review's rulings A–H.

| | | Status |
|---|---|---|
| 1 | The gate manufactures the skill effect | **closed** — Direction 3.1 |
| 2 | J non-monotone in control accuracy | **closed** — Direction 3.2 |
| 3 | Wrapping decides the verdict | **closed** — sentence-in-entry scope |
| 4 | `the hammer` inside `the hammered` | **closed** — word boundaries |
| 5 | Correct answers outside the accepts list | **accepted limit** — §10, threshold 2 |
| 6 | `NONE` with a rationale; hedges naming the target | **closed** |
| 7 | The shared string set is asymmetric | **closed** — hammer out of the primary |
| 8 | Format violations dropped, attrition invisible | **closed** — containers accepted, gap reported |
| 9 | The blind responses are reconstructions | **cannot be closed** — §10 |
| 10 | `holding-rationale` can only confirm | **closed** — rewritten as a 2×2 |
| 11 | An informative correct rejection thrown out | **closed** |
| 12 | Redundant accepts strings | **accepted limit** — §10 |
| 13 | Disqualifier numbering collision | **out of scope** |
| A | Hash-seeded container precedence | **closed** — §4, ordered tuple, `dual_container`, mutant, sole witness, seed-identical output |
| B | A two-list bracket is not an error bound | **closed as a repair, open as a measurement** — §3; the structural rule lands and the residual moves to adjudication, which has not run |
| C | The hedge decomposition is non-identifying | **closed by retirement** — §7 |
| D | The uncued arm contradicts itself | **closed as a repair, arm still blocked** — §7 |
| E | `STILL CAN` flags the key's own model answer | **closed** — exclusions, `X1` and `X2` |
| F | The `STILL CAN` asymmetry | **closed** — §8, two new keys |
| G | Engagement measured quoting; `no-signal` validated nothing | **closed** — block-scoped engagement, `no-signal` retired |
| H | Three qualitative triggers | **closed** — §9, five numeric thresholds, one of which reports its own underpowering |
| — | A refused primary printed beside a warning | **closed** — §3a, `Refusal` raises on every route into a number, threshold derived and cited |

**Three items are open. All three need something other than code, and none
should be closed by writing more of it.** The adjudication in B needs three blind
judges. The label in D needs three blind judges. The transcripts behind objection
9 need a run that was never recorded, and no amount of scorer work will produce
one. A further repair round on the instrument would move none of them, and
shipping one that appeared to would be the failure this note exists to prevent.

## Files

- `cascade_scoring.py` — the scorer, the thresholds, and a self-check on
  container precedence. `python cascade_scoring.py`.
- `cascade_battery.py` — forty-four replies, eleven mutants each with a sole
  witness, five cohorts including the refusal ladder, and key agreement over
  five keys.
- `battery-output.txt` — the run.
- `build_items.py` — regenerates the five keys and refuses to write if the wrong
  region moved, if the uncued arm inherits the cued reading check, or if
  `STILL CAN` reaches a `nostill` contract.
- `C01-forge-lease-buyout-{foreclosing,effect,foreclosing-uncued,foreclosing-nostill,effect-nostill}.yaml`
