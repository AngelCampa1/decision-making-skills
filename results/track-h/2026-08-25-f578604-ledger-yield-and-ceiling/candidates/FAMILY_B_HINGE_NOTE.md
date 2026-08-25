# Family B, `hinge`: what the instrument measures and where it can fail

**Audience:** the evaluating reader deciding whether this venue gets built.

**What this is.** The design behind `H01-nettlefold-flour-contract-pivotal.yaml`
and `H01-nettlefold-flour-contract-decoy.yaml`, one pilot item for the
planted-set membership family registered in
`notebook/2026-08-25-prediction-the-quality-venue-and-the-tau-rule.md`.

**The headline, and it is a design finding rather than an item.** The contrast
works. Four blind instances that saw the prompt and nothing else, two per arm
across two versions of the item, named the planted fact in the pivotal arm every
time and dropped it in the decoy arm every time, one of them writing that the
water *"looks like the question"* and is not. The instrument identifies. What does not survive is the matched arm's
answer key: **NONE was never the answer any instance gave, and it never will
be.** Every version closed the silence the last instance had named, and every
version opened a new one. The enumeration does not terminate, and a required
single-slot naming block always finds the gap. That is the thing this pilot was
for, and the redesign it implies is at the bottom.

---

## The form

`hinge` claims a fact matters only when resolving it changes the answer, and
Step 2 is the test: answer the decision under each value, and drop the fact if
the answer holds. So the scored object is **which** unsettled detail a model
names, never how well it argued.

One scenario, three things it does not settle, at version 3:

| | candidate | type | forks at 40 t | forks at 22 t |
|---|---|---|---|---|
| F_A | working days a year the leat is below milling flow | pivotal / dominated range | yes | no |
| F_B | the 2026 harvest grain price | common mode | no | no |
| F_D | whether Ashgrove wants a second year | downstream of a closed gate | no | no |

The two arms are the same prompt with one token changed, the order size. At 40
tonnes the mill needs 207 milling days of the 250 it has, so it signs below 43
low-flow days a year and declines above. At 22 tonnes it needs 154 and signs up
to 96, which is above the worst figure on the mill's own record, so F_A decides
nothing. The prompt delta is zero characters, and F_A keeps its wording, its
length, its bullet position and its mechanism across both arms.

The decoy types are chosen so each fails Step 2 for a different reason. A
common-mode decoy moves both courses equally and cancels from the comparison. A
dominated-range decoy has a genuine range that never crosses the threshold. A
closed-gate decoy would matter only under a branch the prompt already shuts.
Each takes the same two-value computation `hinge` prescribes, which is the point:
a decoy droppable without computing anything measures nothing.

A fourth candidate, the sifted share, was cut at version 3. It is recorded below
because the reason is instructive.

### The response contract

```
RECOMMENDATION   one word: SIGN or DECLINE
BASIS            free text -- the reasoning that gets you there
LEVERAGE         one sentence naming the single unsettled detail, whether it is
                 raised above or not, that would most likely put you on the
                 other course of action if you knew it -- or NONE if no such
                 detail exists
CONFIDENCE       one word: low, moderate, or high
```

Byte-identical in both arms, and identical across treatment and control when
they run. The exclusion `scripts/probe_casefile.py` describes for the
evidence-ledger venue applies here: block names and the operational vocabulary
avoid `hinge.md`'s own, so the `on` arm gets no lexical head start on the
contract. Confirmed absent from the contract: UNKNOWNS, HINGE TEST, THEREFORE,
hinge, missing, absent, unknown, fact, plausible, values, swing, ask, decide,
guess, twice. RECOMMENDATION, BASIS, LEVERAGE, CONFIDENCE, course and unsettled
appear nowhere in `hinge.md`.

The exclusion covers block names and the distinctive operational vocabulary. It
stops at ordinary connectives, and pushing further buys nothing: a contract that
cannot say "if you knew it" is a contract nobody can follow.

Three things the contract deliberately does not do. It does not ask for the
plausible values, because that is Step 2 and teaching Step 2 to the control arm
destroys the contrast the treatment arm exists to show. It does not put LEVERAGE
last, because the final block gets the most attention. It does not tell the
model the brief is incomplete, because the casefile probe shows the block alone
gets a naming rate of 1.00, so the extra sentence buys nothing and spends
neutrality.

**"Not given above" was the wording until version 3 and it was wrong.** All three
candidates *are* raised above; what is not given is their value. On a literal
reading none of them qualified, and the honest answer in both arms became
something the brief never mentions. Models would have split between the literal
and the loose reading for reasons unrelated to the tonnage, and a difference of
two probabilities cannot survive a bimodal split inside its own numerator. That
is disqualifier 12 in its Family B form, and an adversarial reviewer named it as
the item's single most severe defect.

---

## Can this be scored without a judge

Yes for the primary, and there are five places judgement gets back in. Naming
them is more useful than claiming it is clean.

The primary reads one block, casefolds it, and tests membership in a phrase set
written before any response exists. No model reads the response, which is what
`docs/PROTOCOL.md` §7 asks when it holds that no primary metric is ever a judge
score.

**The phrase list is judgement executed in advance.** Every paraphrase that
counts as naming F_A was decided by me. Writing it before the data is the only
thing separating it from tuning, so the amendment rule is part of the
instrument: the list may grow, only from a held-out pilot, and each amendment is
dated in the file.

**The residual goes to a person, and that person is a judge.** A LEVERAGE block
where no accept fires, where two candidates' accepts both fire, or which runs
past one sentence, cannot be scored mechanically. The mitigation is that this is
a string-identity call, does this sentence name the low-flow question, rather
than a quality call, was this a good decision, and §7's ban is on the second.
Three things keep it honest: adjudicate blind to arm, report the adjudicated
fraction beside the primary, and kill the phrase list above 0.25, because past
that the adjudicator is the instrument. **On the evidence below that kill fires.**
Both blind decoy-arm responses named something off-list, so the adjudicated
fraction in that arm ran at 1.00.

**NONE has to take precedence over every phrase match, and the reason is that
the scorer would otherwise run against the skill it measures.** A model
following `hinge` writes its dropped candidates out by name: the procedure's own
output block mandates a line reading *"same answer either way, dropped"*. So the
correct decoy-arm answer is a sentence like "NONE; not even the low-flow count,
since 22 tonnes fits inside the old seventy", which fires the F_A phrase list on
every plausible wording. Without the precedence rule, P(F_A | decoy) goes toward
1.0 for exactly the models that ran the procedure properly, and the primary goes
to zero or below. The rule is now written into both files. An adversarial
reviewer found this and it is the sharpest scoring defect in the family.

**The key's plausible values are my call.** "About 15 or about 70 low days" is an
authoring judgement. The blind pass answers it from the model population rather
than from my say-so, and it did: instances computed break-evens of 43 and 96 in
the two arms, which are the key's numbers, and placed 15 and 70 either side in
the pivotal arm and both below in the decoy arm.

**The negation guard is incomplete by construction.** A finite reject list cannot
catch every way of writing "not the flow". The bias has no known sign: a false
positive in the pivotal arm inflates the difference and one in the decoy arm
shrinks it.

---

## The matched arm, and what cutting it does

The matched arm is the decoy file. It is matched harder than the tailoring
triplets manage, because the delta is zero characters rather than a pair of
inserts held inside a 10% length band. `docs/TAILORING_CORPUS_SPEC.md` §4 spends
a page deciding whether `max` or `min` is the denominator of that band; this form
gets dimensions 2, 5 and 6 free and has no inserts for dimension 7 to balance.

Cut it and the surviving quantity is P(named the planted detail), which has no
interpretation, because it rises with every authoring artefact. An adversarial
reviewer listed five surface features that rank the low-flow bullet first with no
arithmetic at all: it is the longest bullet, the only one with a time series, the
only one where the author undermines his own evidence, the only one with a
base-rate contrast, and the only unsettled item whose uncertainty is quantified.
Each pushes the number up and none is about the skill.

**The metric does not shrink when the arm is cut. It goes up, and it looks like
a result.** That is the boxed warning's shape, and this repository has the
receipt: the first three tailoring triplets were separable 6 of 6 by a single
surface feature, penalty language, and the contrast is what caught it, because a
feature present in both arms cancels from a difference and dominates a single
number.

Made arithmetic here, and this is the reviewer's own correction to its finding:
**the two arms differ by one token, so no within-arm heuristic can separate
them.** Every one of those five tells fires identically at 40 tonnes and at 22.
They do not manufacture sensitivity. What they do is put a floor under
P(F_A | decoy), which subtracts from the primary one for one, so they cost the
instrument power and cannot fake an effect. Cutting the decoy arm converts that
conservative cost into the whole reported number.

The second thing the difference buys is separating two models a single arm
reports identically. A model naming the capacity question because capacity is
what one asks about, and a model that computed 235 against 207 and then 180
against 207, both name F_A at 40 tonnes. Only the second stops at 22.

**The honest cost of that, also from the reviewer.** The decoy arm gives no
surface signal that capacity is comfortable; seeing it requires the division. So
the difference is bounded above by the rate at which models do the arithmetic,
not by anything about `hinge` reasoning as such. Since `hinge` Step 2 *is* an
arithmetic instruction, that is closer to the construct than it first sounds, but
it is a real ceiling on sensitivity and it belongs in the write-up rather than in
a footnote.

---

## Does the base rate saturate

The worry in the brief lands on a different quantity than the one being scored,
and the pilot evidence splits it cleanly in two.

**The naming rate saturates, immediately, and it is not the primary.** Rescoring
`results/probe/casefile-probe.jsonl`: 12 of 12 responses filled the MISSING
block, and on the nine cases with a fact planted the model named a fact 9 times
out of 9. A required naming block gets filled. Three blind instances on this item
did the same. Settled.

**The single-slot contract makes saturation in both conditions structurally
impossible.** The block asks for *the single detail*, so one response spreads one
unit of mass across F_A, F_B, F_D, NONE and off-list. P(F_A | pivotal) and
P(F_A | decoy) are shares of one slot rather than two independent Bernoullis, and
two shares of one slot cannot both be 1.0. Making the block a list throws this
away, which is the argument for keeping it singular.

**The matching rate does not saturate.** The casefile records give 4 of 9 where
the model's named fact matched the author's, and NONE 3 times out of 3 where
nothing was planted. Different venue and different key, so an anchor rather than
a prediction, but the *which* question has room in it.

### What the pilot actually found, and where my registered band was wrong

Four blind instances, one per arm on versions 1 and 2, prompt and contract
only, no key and no repository.

| version | pivotal arm LEVERAGE | decoy arm LEVERAGE |
|---|---|---|
| 1 | the low-flow day count, **F_A, scores correct** | the delivery schedule and shortfall penalties, off-list |
| 2 | what the gauge shows in a dry spell, **F_A, scores correct** | whether the agreed sum would fold the mill, off-list |
| 3 | *(not yet run)* | *(not yet run)* |

**Both pivotal instances named F_A and both decoy instances dropped it.** The
pivotal instances put it first in their own rankings and computed the key's
thresholds unprompted: 43 milling days with the full quarter sifted, 50 with
none. The decoy instances computed 96 against a 70-day historic worst, and one
wrote that the water *"looks like the question"* and is not. Both ranked the
grain price and the renewal question as non-deciding, matching the key.

So the observed shares are 2 of 2 and 0 of 2, a difference of 1.00. On two
responses an arm that is unmeasurable, and the direction it points is the
**ceiling** rather than the saturation the brief worried about. If it holds,
P(F_A | pivotal) above 0.95 is one of the registered kills.

**These instances are not a control arm, and the reason is my own instruction.**
Each was asked, in the same message, to answer the contract and then to
enumerate every unsettled detail, take two plausible values and work the
arithmetic. That is `hinge` Step 2 handed over in the prompt, so what ran is
closer to a treatment arm than to the unaided control the primary is defined on.
The blind pass is therefore evidence about the item, which is what it was for,
and not an estimate of any base rate. A real control arm sees the four blocks
and nothing else, and its numbers will be lower.

**P(NONE | decoy) is not 0.20 to 0.40. On this evidence it is near zero.** My
registered band was wrong, and wrong in the direction that flattered the design:
I predicted the matched arm's correct answer would be given a fifth to two fifths
of the time, and it was given none of the time. The registered kill was aimed at
the wrong tail as well. I wrote that P(NONE | decoy) above 0.90 would signal an
inert instrument. The observed failure is the opposite: NONE never happens, and
the mass that the key expected there goes off-list where the phrase list cannot
see it.

### Why more closures do not fix it

Each version closed the silence the previous instance had named. Version 2 closed
the shortfall remedy with an agreed sum of £14,000. The version 2 instance then
named whether £14,000 would fold the mill. Version 3 closed that with a cash
figure. There is no reason to expect the next instance to return NONE, and the
reviewer independently found two more open silences of the same class, the
delivery schedule and Ashgrove's creditworthiness, which version 3 also closes.

**The enumeration of silences does not terminate.** A scalar item can leave a
hundred things unsaid because only one number is scored. In a planted-set item
every silence is a candidate, so a matched arm whose correct answer is NONE is
asking the author to have closed everything, and no prompt of readable length
does. The single-slot block then does what it is built to do and finds the gap.

### The redesign this implies

**Give the matched arm its own on-list pivotal candidate.** Instead of an arm
where nothing forks, author an arm where a *different* named candidate forks, so
the model's naming drive lands inside the candidate set. The primary is
unchanged, P(F_A | pivotal) minus P(F_A | decoy), and NONE stops being load
bearing. What it costs is the zero-character prompt delta, since the edit has to
both un-fork F_A and fork something else, which is at least a clause. That is a
real loss and it is smaller than the loss of an unreachable answer key.

I considered and rejected this at authoring time, on the grounds that the matched
arm should exercise `hinge`'s "say so and answer now" branch. The evidence says
that branch is unreachable in a required single-slot block, and the design
decision was made on an argument where a measurement was available.

### Numbers that would still kill it, restated for the redesign

- **P(F_A | decoy) below 0.05.** Specificity on its structural ceiling, the
  difference is sensitivity wearing a second name, and the registration's
  inert-instrument signature has fired. Not observed yet: both decoy instances
  dropped F_A, but on n of 1 each, 0.05 is unmeasurable.
- **P(F_A | pivotal) above 0.95.** No headroom. Two of two so far, on
  instances that were handed Step 2, so this is a warning rather than a
  reading.
- **Primary below 0.10 with an interval covering zero at 20 items.**
- **Off-list rate above 0.25 in either arm.** Currently 1.00 in the decoy arm,
  which is what the redesign is for.
- **F_B or F_D named zero times across both arms.** A decoy nobody names is dead
  weight and manufactures specificity by absence. Reported per decoy, never
  pooled.

---

## The seventeen disqualifiers

Fifteen from `docs/TAILORING_CORPUS_SPEC.md` §5, plus 16 and 17 from the Track H
registration.

### Transfer unchanged

**8, real personal data.** Every persona, mill, brook, bakery and shop is
invented.

**9, a domain used twice.** Watermilling appears nowhere else in Track H.

**15, the governing fact admits a reading under which it does not govern.** Its
form here: a defensible reading under which 70 low days still leaves the mill
able to deliver, or 15 still does not. **The item failed this at version 1 and
the failure was invisible to me.** The reviewer showed that with no stated
consequence for under-delivery, signing at 70 low days yields about £10,000
against nothing for declining, so a commercial reader signs at every value and
the fork dies. Version 2's agreed sum of £14,000 is what restores it. A fork
that rests on an unstated premise is not a fork.

### Transfer with a changed shape

**1, the professional's sentence.** Two clauses rather than one: *the
recommendation is SIGN at 15 low days and DECLINE at 70.*

**2, the matched fact arguably governs.** Reads as *a decoy arguably forks*, and
it is the central risk. **The item failed this too, on the sifted share, and two
readers found it independently.** The adversarial reviewer derived the band, and
the version 2 pivotal instance derived the same two thresholds unprompted and
ranked the share third for the same reason. The
requirement is 200 milling days with none sifted and 207 with the full quarter,
so for any low-flow estimate between 44 and 50 the share flips the answer, and
that band sits inside the range a reader gets by discounting the gauge toward the
pre-weir record. No tonnage makes the two thresholds coincide, so tuning cannot
repair it and the share is settled in the prompt at version 3. The cost is a
decoy: the item now runs three candidates rather than four.

**3, the self-neutralising insert.** Transfers to decoys. The sifted share was
the near miss and is now gone.

**4, the eight salience dimensions.** Dimensions 2, 5 and 6 are satisfied by
construction. Dimension 7 has no inserts to balance. Dimensions 1, 3 and 4 move
*inside* the prompt: they now govern the pivotal candidate against its decoys
rather than one insert against one insert, and must hold three ways rather than
two.

**6, the base is not determinate enough.** Harder here. A scalar venue needs one
determinate base number; this needs every decoy's two values to give a checkable
identical answer, which is why the item carries a full capacity model in its key.

**10, the matched fact is gated by a precondition elsewhere in the base.** The
sharpest of the fifteen. It becomes: before labelling a candidate a decoy,
enumerate every number and date in the prompt that could put it back on the
threshold.

**12, the elicited quantity forbids the professionally correct answer.** The
shape behind 21 of 21 scored failures here, and the item failed it at versions 1
and 2 through the "not given above" wording. Fixed at version 3.

**14, the base pre-announces a catch.** The tell moves from phrasing to
formatting, since with several unsettled details in one prompt, one of them being
longer or later is the giveaway. The item still fails this softly: the low-flow
bullet is the longest in the prompt. The failure is arm-invariant, so it costs
power rather than validity, and the repair for the next item is to level the
bullets.

**16, the elicited question enumerates the constraints.** The tightest constraint
on the contract wording. "The single unsettled detail" names no candidate.

### Do not transfer

**5, the governing fact redefines the elicited quantity.** No elicited quantity
to redefine. Its analogue, an arm edit changing what the block asks, is clean.

**7, the quantity can be zero.** No division, no relative movement, no threshold.
The largest simplification Family B buys: the whole tau argument in the
registration, the log scale, the pooled estimator, the bootstrap recomputation,
does not touch this family.

**11, the corrections land near each other.** No numeric correction to compare.
Its analogue matters and differs: two candidates a reader would describe in one
sentence collapse into one, and no phrase list separates them.

**13, integrality and rounding.** Nothing is rounded. The analogue is the phrase
list, the same problem in a different medium.

### Inverts

**17, the governing arm's answer is infeasible against the information
timeline.** In Family A this kills an item. Here it helps: the gauge cannot see a
dry September before the 2026-09-04 deadline, so nobody escapes into "go and find
out", `hinge` Step 3 leaves only the guess-out-loud branch, and both arms end in
a recommendation. An authoring brief carrying this rule unamended would cut good
items.

### New, and this form needs all six

**18. Two candidates' accepted phrasings overlap.** Substring matching over
several candidates has to partition. Checked before an item ships; an overlap is
a cut rather than a repair.

**19. The pivotal candidate is the only one the prompt gives a range for.** A
model finds it by looking for the range. **H01 fails this**, along with four
other surface tells the reviewer enumerated. It survives because every one of
them is arm-invariant and therefore cancels from the difference, which is the
argument for the matched arm stated as arithmetic. It is also why the single-arm
secondary is not reportable.

**20. The arms carry different numbers of candidates.** Different denominators,
incomparable shares. Both arms here carry three candidates in identical words.

**21. NONE is the matched arm's correct answer.** Registered at authoring as a
band to be set from data. **The pilot upgrades it to a hard disqualifier.** A
matched arm keyed to NONE requires the author to have closed every silence in the
prompt, the enumeration does not terminate, and the observed off-list rate in
that arm was 1.00. Author the matched arm with its own
on-list pivotal candidate.

**22. A closure introduces a candidate.** Every repair to a planted-set item is
itself new text and new text carries new silences. The agreed sum added at
version 2 to close the shortfall gap immediately became the version 2 instance's
named answer. Each closure gets a blind re-derivation of its own, and an item is
not finished when its last known gap closes.

**23. The scored block's correct answer names the scored candidate.** A model
running the procedure writes out what it dropped, so a dismissal fires the phrase
list. Every planted-set scorer needs NONE-exclusive precedence and a
negation-aware matcher, or it is anti-correlated with the skill under test.

---

## The adversarial review, and its disposition

A reviewer briefed to break the item, working from the version 1 text plus
`hinge.md` and the corpus spec, returned **CUT** with seven named repairs. Three
of its findings had already been closed at version 2 before it reported: the
sign-and-under-deliver escape, the delivery schedule, and the shortfall remedy.

| finding | verdict | disposition |
|---|---|---|
| the sifted share forks over 44 to 50 low days | accepted, fatal | share settled in the prompt at v3, decoy count drops to two |
| "not given above" excludes every candidate | accepted, fatal | LEVERAGE reworded at v3 |
| the correct NONE answer fires the F_A phrase list | accepted, fatal | NONE made exclusive and tested first |
| Ashgrove's creditworthiness beats F_A in both arms | accepted | stated at v3 |
| Saturday working is an open third course | accepted | closed at v3, Tobin stands the market himself |
| 250 working days is derivable and wrong, 251 or 246 | accepted | figure asserted at v3 rather than derived |
| "32 tonnes off the stone" against "40 tonnes of flour" | accepted | 32 t stated as throughput, all wholemeal |
| the market volume could fall if grain spikes | accepted | volume stated to hold whatever grain does |
| the five surface tells rank F_A first | accepted, and the reviewer's own correction stands: arm-invariant, so it costs power and cannot fake an effect | recorded as disqualifier 19 |
| the item measures arithmetic execution rather than hinge discrimination | accepted in part | `hinge` Step 2 is an arithmetic instruction, so the two are closer than the objection allows; recorded as a ceiling on sensitivity |
| renewal is a clean decoy | the reviewer tried and failed to break it | kept |

Version 3 is the item as delivered. **It has not been blind-tested.** The
evidence on record ran on versions 1 and 2.

---

## What I would run, and what I would change first

The two-arm pilot is 20 control-arm repeats per arm, 40 calls, and it measures
every number in the tables above on one item. It is cheap and it is not the first
thing to do.

**The first thing is the redesign.** Re-author the decoy arm with its own on-list
pivotal candidate, so NONE stops carrying the matched arm, then run the 40 calls
on that. Running them on version 3 as it stands would measure an off-list rate
already known to be near 1.00 in the decoy arm, and spend the calls confirming
something four blind instances have shown for free.

**If the redesigned pilot identifies**, the authoring bill is the thing to price,
and it is higher than Family A's. Three of the eleven review findings above are
silences that had to be closed, each closure is new text, and each piece of new
text needs a blind re-derivation of its own. The item took three versions, four blind
instances and one adversarial review to reach a state I would run. That number is the yield estimate,
and it is what the registered kill on authoring yield exists to catch.
