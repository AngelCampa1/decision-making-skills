# G2: adversarial review, both directions

**Audience:** the dispatcher. The two blocks under "G2a" and "G2b" are what those
instances receive.

G2 is the only gate that cuts on judgement. Both reviewers see everything,
including the `key` block, and both hold G1's disagreement dossier.

`docs/TAILORING_CORPUS_SPEC.md` §8 already requires G2a. **G2b is new**, and it
exists because pass two discovered its failure mode the hard way: two of five
items were cut for an ambiguous *governing* arm, and nothing was reviewing for
that.

The framing is trust-based rather than fear-based throughout, which
`docs/AUTONOMOUS_WORK_ORDER.md` records as surfacing 59% more hidden issues.

**Reliability is measured, or this gate is decoration.** Run G2a a second time on
a resample and report Cohen's kappa from `stats/agreement.py` **before** reporting
any yield. The pass-two entry's own top risk is *"Reviewer B, which never
reported"*, and this is that risk measured rather than worried about.

---

## G2a — prove the matched fact governs

> You are reviewing one item from a corpus that is about to be used to measure a
> model. Your job is to find the reading under which the item is wrong. A review
> that returns "looks good" has not run.
>
> **The item's claim, which you are here to break.** The author asserts that the
> fact inserted in the MATCHED arm does not change the answer. Construct a
> reading under which it does: even a little, even on a contingency, even only
> for some professionals in the field. You are not looking for mistakes in the
> prose. You are looking for an arithmetic or legal channel from the matched fact
> to the elicited quantity.
>
> **Work these in order. Each has killed a real item in this corpus.**
>
> 1. **Enumerate every date, deadline, effective date, commencement date, waiting
>    period, qualifying period and precondition in the base prompt.** For each,
>    ask whether it delays the moment the matched fact starts to bite. An item
>    died on exactly this: a 30-day pre-authorisation lead time was neutralised
>    against a slot 40 days out, but the plan carrying the clause did not
>    commence until a date that pushed the earliest filing past the slot. The
>    matched fact governed through a precondition nobody had enumerated.
>
> 2. **Compute where the matched fact would land the answer if it did govern, and
>    compare that to where the governing fact lands it.** An item died at 8.29
>    against 7.71, two facts producing corrections 0.57 months apart. Where both
>    land the answer in roughly the same place there is no contrast left to
>    measure, whatever the labels say.
>
> 3. **Is the neutraliser over-determined?** The base is meant to neutralise the
>    matched fact through one non-adjacent sentence. Where two or more independent
>    sentences each close it on their own, the two-hop read collapses to one hop
>    and the item stops being hard.
>
> 4. **Is the matched insert self-neutralising?** Where reading the insert alone
>    is enough to know it does not bite, the item measures one sentence of
>    reading comprehension.
>
> 5. **Read the matched fact as a different professional.** Would a conservative
>    practitioner, an insurer, a regulator or an auditor treat it as material
>    where a majority would not? Name that professional and their reasoning.
>
> 6. **Is the standard treatment of this fact-type in this field to adjust for
>    it?** Excluding restricted cash from a runway calculation is standard
>    treatment, and that is how one item's matched fact turned out to govern.
>
> **The disagreement dossier.** Three professionals read each arm blind, without
> the answer key. Their answers and their arithmetic are below. Where they
> disagreed, decide which of two things happened:
>
> **AMBIGUITY** — a competent professional could defensibly hold the minority
> reading. The item is cut, on either arm, and you say so.
>
> **DIFFICULTY** — the minority reading is a mistake a careful professional would
> not defend. The item survives, and the disagreement is the property the item
> exists to have.
>
> Rule on every disagreement in the dossier by name. Do not summarise them.
>
> **Return, in this order:**
>
> a) Every channel you found from the matched fact to the elicited quantity, each
>    with the arithmetic it implies and the sentence in the base it routes
>    through. Say "none found" only after working all six checks, and name each
>    check you ran.
> b) Your ruling on each dossier disagreement: AMBIGUITY or DIFFICULTY, with the
>    reason.
> c) A verdict: CUT or SURVIVES.
> d) If SURVIVES: the single strongest objection you could not make stick, and
>    what would have to be true in the prompt for it to stick. This is the most
>    useful thing you will write, and an empty answer here means the review did
>    not run.
>
> Where your objection to a matched fact is not clearly wrong, the item is cut.
> Nineteen good items beat twenty with one disputed label among them.

---

## G2b — prove the governing fact does not govern

Same preamble and same dossier section as G2a. The middle is replaced with this.

> **The item's other claim.** The author asserts that the fact inserted in the
> GOVERNING arm does change the answer, and that it changes it to the value
> recorded in the key. Construct a defensible reading under which it does not, or
> under which it moves the answer somewhere else.
>
> **Why this matters more than it looks.** The primary measure is a difference of
> two probabilities. An ambiguous governing arm depresses the probability of
> change through a defect in the item while looking exactly like a model that
> failed to notice, so it biases the primary toward zero and makes a null
> unreadable. Two items in this corpus died here and nothing but a blind
> re-derivation caught them.
>
> **Work these in order.**
>
> 1. **Does every term in the governing insert have one reading?** An item died
>    because a reader may decline to read "30-litre returnable containers" as
>    kegs, forking the answer between 6 and 10 weeks. Take every noun phrase in
>    the insert and ask whether a professional could read it narrowly.
>
> 2. **Is the governing fact an entitlement or an event?** An item died because
>    an earlier slot was *offered* rather than accepted, against a base in which
>    the persona says of the original date "that is the one I hold". The base
>    value stayed defensible, so the governing arm did not have to move.
>
> 3. **Does the governing fact change the definition of the elicited quantity
>    rather than its value?** Where the extractor would be scoring two different
>    questions across the two arms, the contrast is destroyed silently.
>
> 4. **Does the elicited quantity forbid the professionally correct answer?** Ask
>    what you would actually advise in the governing arm, and whether that advice
>    is expressible as a single number in the stated unit. One item asked for
>    "weeks of notice counted from today" where the right advice produced the same
>    number as the base, so the better reasoner scored as a failure to move. This
>    shape produced 21 of 21 scored failures in this repository.
>
> 5. **Is the value integral in its stated unit, and can a correct reading land
>    outside the tolerance by rounding?** All three first-pass items failed this:
>    7.71 months, 12.57 weeks, 14.71 weeks.
>
> 6. **Does the base pre-announce that a catch is coming?** "On the face of it",
>    "nothing in it requires more", "it is not urgent" all appeared in first-pass
>    bases and all bias a reader toward movement on the arm where movement is
>    scored as failure. Quote any you find.
