# Family B, `cascade`: what the set form buys and what it still owes

**Audience:** whoever builds or kills the decision-quality venue for `cascade`.

**What this is.** The design argument behind `C01-forge-lease-buyout-{foreclosing,effect}.yaml`,
written as an attack on it. The item is a pilot for the planted-set form named in
`notebook/2026-08-25-prediction-the-quality-venue-and-the-tau-rule.md`, where
`cascade` and `hinge` sit in Family B because the scalar form died on
`cascade.md` Step 3.

The instrument: one base scenario, two closing paragraphs, one elicited block.
Primary as authored is P(target named in `CANNOT` | the plan really removes it)
minus P(target named in `CANNOT` | the target is an event the plan brings about).

**That primary does not survive its own pilot, and the fix is in the file
already.** One blind instance per arm scored sensitivity 1 and specificity 0 on
it, for J = 0, because the effect the control plants is a legitimate member of
the set under the contract's own wording. The secondary check in
`C01-forge-lease-buyout-effect.yaml`, which reads the same string set in both
arms, scored J = 1 on the same two responses. Section 5 has the responses and
section 6 the recommendation, which is to promote the secondary and drop the
primary. Sections 1 to 4 are the design argument as written before those two
responses came back, left standing because the pilot is what corrects them.

---

## 1. Does set membership escape the reordering objection?

Partly. It converts a fatal objection into a countable one, and it does that by
moving the damage off the answer key.

The scalar form died because the key held a number. A model that reports the
resequencing which preserves the foreclosed option leaves the quantity where it
was, and the key says the quantity should have moved, so competence scores as a
sensitivity failure. Set membership has no such key. The option is removed by the
plan as posed whatever a cleverer plan would have achieved, so the key stays true
under every reordering a model can find.

The objection returns twice.

**Through the response.** A model that finds the better sequencing can write
`CANNOT: NONE`, or `nothing, if you keep a foot in the door until February`. The
key is still correct and the response still misses. The punishment has moved from
the answer key to the elicitation, which is a better place for it, because an
elicitation can be repaired without touching the labels. C01's repairs are the
framing sentence pinning the answer to the plan **exactly as described**, and the
`VERDICT` block, which gives the smarter plan somewhere to go that is not the
scored block. Both are mitigations and neither is a proof. A pilot run should
count treatment-arm `CANNOT` blocks that contain a resequencing hedge in place of
the target, and that count should be registered as a secondary before the run,
not read off afterwards.

**Through the item.** C01 survives only because every resequencing route is shut
by a stated fact. Now attack it:

| route | what shuts it | how hard |
|---|---|---|
| stay past 2027-01-11 and apply, then surrender | the offer is out by 2026-10-31 with the building empty; refusing is a different plan and belongs in `VERDICT` | shut |
| apply before leaving | the round opens 2027-01-11, after she is out | shut |
| apply from new premises | the rule needs the same premises for the three years ending on the application day | shut |
| take a licence back, or sublet a corner, and keep holding | the building is to be empty on completion and the buyer will work it himself | narrowed, not sealed |

The fourth is a real hole. A reader can always say *ask them for a licence back*,
and nothing in the prompt makes that impossible, only unpromising. Sealing it
needs a sentence whose only job is to seal it, which is disqualifier 14's tell.
So the hole stays, and it is small enough to count rather than argue about.

The larger cost is what shutting the first three did. **C01 measures Step 2 with
Step 3 switched off.** An item where the ordering is genuinely live is an item
where a competent reader can decline to call the option foreclosed, which is
disqualifier 15 in new clothes and biases the primary toward zero. The venue's
scope claim has to say this out loud: it measures whether a model separates
things that happen from things that stop being doable, on decisions where the
sequence is fixed. That is narrower than *cascade improves decisions* and it is
the honest reading of what a Family B corpus can support.

## 2. Is the effect arm matched, or is it obviously the boring one?

Matched on the two closing paragraphs: same actor writing, same date
(2026-08-21), same sum (£18,000), same deadline (2026-10-31), same sentence
skeleton, same position, same deontic register, 43 words against 42.

Not matched on consequence magnitude: the treatment's target is a £40,000 round
and the control's is a £12,600 repayment. That gap is forced. Raising the
repayment until it rivals the round means it starts to gate the £38,500 hammer,
and an effect that gates a purchase **is** a foreclosure, so the control arm dies
the moment its target gets big enough to match. Shrinking the round instead makes
the treatment's foreclosure less worth naming and drives sensitivity down. The
mismatch is the price of a control that provably removes nothing.

What keeps the control from being obviously boring is where it sits rather than
what it is worth. The repayment is grant-shaped, dated, four figures, and one
bullet away from the grant the other arm really does end, so the surface cue *a
grant is at stake in 2026* fires in both arms and the model has to do the
eligibility check in both.

What might make it boring anyway is the `CANNOT` gloss. It asks for something the
writer **can do today**, and a repayment is not something she does. Filing it
there takes an extra move: *keep the £12,600*, *avoid paying it back*. A careful
model will not make that move, and if no model makes it, specificity is 1.0 and
the stratum closes.

That is the venue's whole risk, and the knob has no neutral setting:

- Keep `RESULTS`, and effects have a correct home, so specificity rises toward 1
  and the measurement is about the contract.
- Drop `RESULTS`, and `CANNOT` is the only place to put anything, so specificity
  falls toward 0 and the measurement is about the contract.

There is no wording that measures the model free of the contract. The most this
design can do is put the contract in one place, hold it byte-identical across
arms, and report the specificity **against the count of responses that mentioned
the target at all**, so a ceiling can be told apart from an instrument that
nothing reached. That is why the control file carries an attention set and gates
specificity on it.

## 3. Where judgement creeps back

No judge model runs anywhere in this instrument, which is what `docs/PROTOCOL.md`
§7 asks. Every rule below is a string rule fixed before the run and checkable by a
second reader from the two files. That is the argument that the primary is not a
judge score. It is not an argument that the scoring is free of judgement, and
these are the five places it is not.

1. **The `accepts` lists are authorship.** They are judgement frozen at authoring
   time, bounded and reviewable, and a paraphrase outside the list scores as a
   miss. Bare `grant` is deliberately absent from both lists because two grants
   appear in the prompt, so a model writing only *the grant* scores zero in both
   arms.
2. **`negation_guards` is the one rule that reads meaning.** *The continuity
   grant is not affected*, written inside `CANNOT`, is a hit on presence and a
   miss on sense. The guard list fixes that case and creates its own: `still` is
   a guard in the control arm and would drop a line reading *she will still not
   be able to keep the £12,600*. Every guard is a small judge with a fixed
   vocabulary.
3. **The hammer counts as naming the grant.** A response whose `CANNOT` block
   says only *buy the pneumatic hammer* has traced the same loss one step
   further, and scoring it as a miss is the shape that produced 21 of 21 scored
   failures in this repository. Accepting it is a judgement about how far down a
   chain a name still counts.
4. **The attention scope.** Specificity runs over responses that mention the
   repayment anywhere. Scoping it to `RESULTS` instead would be defensible and
   would give a different denominator.
5. **The residue in the control arm.** Relining removes the 1902 hearth, so the
   control's set is not empty. This item scores the named target and ignores the
   rest of the block, which is a decision that a different author could take the
   other way by grading block contents.

## 4. The seventeen disqualifiers

**Transfer, with the wording changed from quantity to set.**

- **2, the matched fact arguably governs** becomes *the control's target is
  arguably foreclosed*, and it is the central one. Its Family B form is the
  vacuous reading: every event removes the world in which it did not happen, so
  any effect can be talked into the set. C01 answers it in the contract rather
  than in the key, by asking for things the writer **can do today**.
- **4, salience.** Applies unchanged to the two closing paragraphs. Scored in
  `key.salience_match` at seven dimensions closed and one open.
- **6, the base is not determinate enough.** Becomes: the base must establish the
  foreclosed option as live and worth having, or naming it is not clearly right.
  C01 does it with the round's dates, the £40,000 cap and the hammer's price.
- **8, real people.** Unchanged.
- **9, a domain used twice.** Unchanged.
- **10, the fact is gated by a precondition stated elsewhere.** Transfers, and it
  nearly took C01 twice. The annual October shutdown against *without a break*
  was the first, fixed by writing the rule on **holding** premises rather than
  working them. A debt owed to one body against the other body's decision was the
  second, fixed by giving the two grants two bodies with two jobs. Both are
  written out in `key.preconditions_enumerated`.
- **14, the base pre-announces a catch.** Unchanged, and it is the reason the
  prompt nowhere says the two bodies are independent, which was the first draft's
  fix for the second precondition above.
- **15, the governing fact admits a reading where it does not govern.** Transfers,
  and section 1 is where it now lives.
- **16, the question enumerates the constraints.** Transfers to the block gloss.
  C01's gloss is categorial and names none of the grant, the lease or the hearth.
- **17, the answer is infeasible against the information timeline.** Transfers
  inverted: the foreclosed option has to be **reachable** in the base's own
  timeline, or it was already spent and naming it is right for the wrong reason.
  The 2027 round opens after the deadline and inside the lease, so it is live
  until the plan removes it.

**Do not transfer.**

- **1, the professional's sentence.** Replaced by a weaker requirement: the target
  is nameable in one noun phrase. C01's is *applying to the 2027 round*.
- **3, the self-neutralising insert.** No neutraliser exists here. The control's
  paragraph is not built to cancel itself, it is built to cause something.
- **5, the fact redefines the quantity**, **7, the quantity can be zero**, and
  **13, integrality.** There is no quantity.
- **11, the two corrections land near each other.** No arithmetic to collide. Its
  cousin is that the two arms must not score the same object, which C01 keeps as a
  secondary check rather than as the primary.
- **12, the elicited quantity forbids the correct answer.** Transfers in spirit
  and not in form, and this is the whole reason `cascade` is in Family B. Naming
  the foreclosure and then recommending a better plan both fit inside this
  contract, in two different blocks.

**New, and needed by this form.** Numbering continues from the seventeen.

- **18. The control's target is not named anywhere in the response.** Counting
  that as a control success hands a perfect specificity to a model that skipped
  the item, which is the inert-instrument signature the registration asks to be
  made visible. Every Family B control carries an attention set, specificity runs
  over attended responses, and the unattended count prints beside it.
- **19. The block admits no correct empty answer.** A block that demands content
  cannot be passed by a control arm. *Write NONE if there is nothing* is not
  optional.
- **20. The treatment's target is foreclosed by the scenario rather than by the
  plan.** The Family B cousin of disqualifier 5. If the option was gone before the
  plan, both arms are right to name it and the contrast disappears.
- **21. The control's set is empty and the item knows it.** Then `NONE` is the
  graded answer and `NONE` is what an incurious response writes, so discrimination
  and laziness score the same. C01 keeps one true and worthless entry in the
  control's set, the 1902 hearth that has cracked twice, and scores the named
  target rather than the block.

## 5. Blind re-derivation, and what it found

I authored the key, so my own re-reading is not blind. Two independent instances
answered the two prompts with the framing and the contract and nothing else: no
key, no repository, no tools, one instance per arm, same model, single sample.
Everything below is n = 1 per arm and is reported as an existence proof rather
than a rate.

**Foreclosing arm.** The `CANNOT` block returned three lines: working Bellwether
Forge after 2026-10-31, taking up the five-year lease from 2027-04-01, and
*Apply in the 2027 round of the Workshop Continuity Grant (next round not until
2030)*. That is a hit on the planted target with no negation guard firing. It
matched the key's set exactly, including the two entries the key lists that the
target does not cover, and its `RESULTS` block volunteered that the £12,600
clawback is **not** triggered, which is the key's `still_available_after` entry
reached independently.

It also did the thing section 1 predicted and put the resequencing where the
contract asked for it. Its `VERDICT` reads *do something else instead*, and
proposes renegotiating the exit date, while its `CANNOT` block still names the
grant. The mitigation for disqualifier 12 worked on its first live test: the
better reasoner named the foreclosure and kept its better plan.

**Effect arm.** The `CANNOT` block returned two lines: *Keep the original 1902
hearth*, which is the residue the key records and does not score, and

> Keep the £12,600 Hearth Repair Grant without repaying it in full by roughly
> 2026-11-28

That is a hit on the control's planted target, so specificity is 0 on this
instance and the authored primary reads J = 0.

The secondary check went the other way. The 2027 round appears nowhere in the
control arm's `CANNOT` block, and the response's reasoning states that the round
tests unbroken holding of the premises rather than the fabric of the hearth, so
relining does not disturb it. Read on the string set the two arms share, the pair
scores a hit in the treatment arm and a correct rejection in the control arm, for
J = 1.

**What that means, and it is not a scoring accident.** Read the contract back:
*something the writer can do today and will not be able to do once the plan is
carried out*. Ines can hold the £12,600 today. After the reline she cannot. The
line is true, and it is correctly filed under the definition I wrote. Disqualifier
2's Family B form, the one section 4 calls central, fired on this item, and the
defence section 2 offered against it, that converting a repayment into an ability
takes an extra move a careful model will not make, was wrong. The move took one
clause.

Generalise it and the construct is the problem rather than the item. Any effect
that touches the actor can be written as an ability she loses, because *doing
without X* is an ability. A gain, an obligation, a bill, a record: each supports
its own *keep*, *skip*, *avoid* phrasing. The partition `cascade.md` Step 2
asserts is real as advice, in that a good adviser flags the door and not the bill,
and it is not a partition a membership scorer can read off a response, because
membership under any honest wording of the block is decided by grammar rather than
by register.

So the effect-only arm as specified cannot be scored the way it was specified. Two
repairs are available and only one of them is cheap.

## 6. The recommendation

**Promote the secondary and drop the authored primary.** Score one target across
both arms: *applying to the 2027 round of the Workshop Continuity Grant*, a hit in
the foreclosing arm and a miss in the effect arm, on one `accepts` list used
twice. It is immune to the vacuous reading, because the application is
unambiguously an action of hers and it unambiguously survives the reline. The two
arms then differ by one paragraph, the answer on one string set inverts between
them, and no judgement about register enters the scorer at all. `C01` already
carries this as `key.scoring.secondary_control` in the effect file and needs no
rewriting to run it.

What it costs is a narrower claim. The same-target form measures whether a model
over-attributes foreclosure to a vivid nearby event, which is one consequence of
`cascade` Step 2 rather than Step 2 itself. Written up honestly, the venue
measures that and says so.

What it risks is the ceiling that closed four venues. The blind control instance
got it right and explained why, in a single sample, which is one observation in
the direction of specificity 1.0. The other repair, keeping the register primary
and wording the block to exclude *keep* and *avoid* phrasings, buys headroom by
telling the model the answer, and lands back in section 2's knob with no neutral
setting.

## 7. What would kill this

Three counts, and none of them has a threshold yet, because a threshold picked
from no data is the trap the registration names for `k`.

- **Specificity at its ceiling with a full attention denominator.** Ten items
  returning specificity 1.0 on the promoted target, with nearly every response
  mentioning the round, closes the stratum on a ceiling as four venues already
  have. That is a publishable negative and, on the evidence of one control
  instance that reasoned its way to the right answer, it is the likeliest outcome.
- **Resequencing hedges displacing the target in the treatment's block.** One
  instance put its hedge in `VERDICT` and kept the target. If that does not hold
  up over ten items, disqualifier 12 came back through the elicitation and the fix
  is another contract rather than another corpus.
- **`CANNOT` blocks whose entries are all `keep` and `avoid` phrasings.** The
  count that would say the effect arm is unscoreable on any target, not just on
  the one this item planted.

All three are counts over the same responses, so one pilot run at ten items
produces them together.
