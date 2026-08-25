# Family B, `hinge` version 6: what the v5 review broke and what replaced it

**Audience:** the next reviewer, briefed to break this.

v5 is `../v5/`, its note is `../v5/REPAIR_NOTE.md`, and the review that broke it
is in `../v5/review3/`. v4 and its note are in the parent. All of them still run.

**What this version's key covers: H01 only.** H02 and H03 have their own keys and
are scored by their own author's battery. Nothing here reads them.

---

## The blocking repair: the scorer holds no key

`ACCEPTS`, `BARE`, `BARE_SUPPRESSED_BY`, `F_C_ACCEPTS` and `ARM_KEY` were module
constants inside `scorer.py`, transcribed from H01, and `label()` reached them by
global lookup. The author of H02 and H03 could not run the unmodified scorer at
all: they had to rebind four module names in a context manager and put them back.

The inconvenience is not the finding. **A second item scored without rebinding
them returns labels drawn from H01's vocabulary, silently, with no error
anywhere.** A scorer holding one item's words as globals scores every other item
against the wrong key and looks like it worked.

So: the tables live in `key_h01.py`, `scorer.ItemKey` carries them, and
`label(response, key)` takes one as a **required positional argument**. Not
optional with an H01 default — an item that forgets to pass one fails at the
call, the way a `council` item in `elicit.py` has no `unit` field to fill in
wrongly rather than an optional one. `bare` and `bare_suppressed_by` are
per-candidate maps, so another item's F_A can be guarded without editing this
package, and `ItemKey.__post_init__` refuses a candidate with bare forms and no
suppressor list.

## The scan arm: `P(NONE | scan)`, and a withdrawn claim

v5 registered `P(F_A | scan) − P(F_A | matched)` on the claim that widths of each
quantity's stated range were *"the only commensuration under which a margin scan
is even well defined"*. **That claim is withdrawn.** A second commensuration
exists, invents no midpoint, is derivable entirely from the prompt, and is what
the LEVERAGE slot's own words — "would most likely put you on the other course" —
ask for: the money each quantity moves across its stated range.

```
  arm         water swing   fee swing   a B-scanner names
  pivotal          17,880       5,000   F_A
  matched               0       5,000   F_E
  scan                  0       1,000   F_E
```

A money-swing scanner scores +1.000 on the pivotal/matched pair exactly like the
range-width scanner, and names the **opposite** candidate in the scan arm. So the
v5 statistic returns "no confound" whenever that is the real policy — the
identical failure `P(F_E | scan)` was withdrawn for at v4. v5 did not fix the
diagnostic; it changed which unmodelled scanner it was blind to.

Registered instead: **`P(NONE | scan)`**, primary for that arm. Nothing forks
there, so only a reply that ran Step 2 has a reason to say so.

```
  hypothesis          P(NONE|scan)   P(F_A|scan)-P(F_A|m)   P(F_E|scan)
  A: range widths            0.000                 +0.589         0.100
  B: money swing             0.000                 -0.111         0.750
  ran Step 2                 0.450                 -0.061         0.000
```

The other two stay, descriptive, and neither may be read alone: `P(F_A | scan)`
cannot see B and `P(F_E | scan)` cannot see A. No band on any of the three.

## The bounds are derived now, and there are two of them

**Dropout.** v5 registered "three more unreadable replies in one arm than the
other moves the primary by 0.027". That is one point on a curve, taken at a 60/40
behaviour mix on v4's denominator. For an arm-invariant policy naming one
candidate with probability `a` in both arms,

```
hits − swaps = (2a − 1)·d        crossed = (2a − 1)·d / N
```

maximised at `a = 0` or `a = 1`, so **|crossed| ≤ d/N**. At `d = 3` that is 0.075,
2.8 times what was registered. At `d = 5` it is 0.125 — above the kill threshold
itself, and the inert-instrument kill stops firing on a policy that named the
low-flow count in both arms twenty times. So the per-arm `NO_BLOCK` counts are
read **before** the primary, not consulted when the primary lands near a line.
Branch three-b.

**Coverage.** New, and it belongs beside the first. Accept-list recall on 34
held-out definite descriptions is `r_A = 0.29`, `r_E = 0.41`, pooled 0.35. A
shared miss rate only shrinks the primary; the difference is what can set a sign:

```
hits − swaps = 20·(2a − 1)·(r_A − r_E)      |crossed| ≤ |r_A − r_E| / 2 = 0.059
```

59 per cent of the kill threshold, and soft at n = 34. Read with the dropout
bound or neither is read. Branch two-b.

Neither is patched away. A list grown to cover the phrasings its author thought of
next is a phrase list written before the data.

## Four additions to the dismissal rule, and then it stops

`swing` is `hinge.md`'s central verb — twice in its opening paragraph and the
whole of its Step 2 heading — and it was not on the relevance list. "same answer
either way" is the line the skill's Output block **mandates**, and `scorer.py`'s
own docstring cites that mandate as the reason `affirmative_region` exists. The
LEVERAGE slot's own "put you on the other course" was missing, and so was the
perfect aspect of every verb that was present. None of these is invention. **An
instrument that cannot parse the output its own skill specifies is broken for a
reason that has nothing to do with vocabulary coverage.**

Then it stops. The rate, on 28 phrasings drawn from outside the author's head —
the skill's vocabulary, three dismissal classes a reviewer named, and the register
of the twelve recorded casefile replies:

```
                                     v5      v6
  closed                           7/28   11/28
  cost a zero, mostly adjudication 20/28   16/28
  manufactured a SWAP               1/28    1/28
```

**Direction holds. Magnitude does not.** One swap in 28 against the 1 in 11
accepted in `known_limits.py`, and the four additions added none — so the v5
judgement that the residue is benign in direction survives its test. But
restricted to the 21 phrasings drawn from the skill's own vocabulary and the three
named classes, **19 of 21 routed to adjudication at v5 and 15 of 21 still do**.
That is 0.71 of correct, procedure-following replies against an
`adjudicated_fraction` kill of 0.25.

**This blocks the skill arm and not the control arm.** The control register is the
twelve recorded casefile replies, where the rate is 1 in 7 and not one of the
twelve carried a dismissal marker of any kind. It is the most important thing on
record before anyone spends a skill-arm call.

## Two senses, split

`settle`, `decide`, `govern` and `determine` mean either "does not matter" or "is
not fixed yet". The second is Step 3's obtainability finding — the thing the item
exists to elicit — and v5 scored *"which it will not settle until its October
meeting"* as `ADJUDICATE_NO_CLAUSE`. Confirmed on H01 before the guard was
written. A WHEN-tail now tips them, and the search steps past and keeps looking
rather than returning nothing, because a piece can carry an obtainability clause
and a real dismissal both.

## A pre-posed set-aside no longer eats the sentence

*"Setting aside the low-flow day count the scheme fee is what turns it"* asserted
nothing at v5: with no comma and no coordinating "and", the marker's scope ran to
the end and took the answer with it. Reproduced on H01 first. The fix applies only
where the head is **empty**, because that is the case where dropping the piece is
already known to lose everything; where a head exists the v5 behaviour is
untouched.

## The register: fee against water

v5 recorded the fee bullet's numeral rank — 10 numeral characters, rank 1 of 16 —
as irreducible, on the ground that a two-ended stated money range needs two
numbers. **The water bullet refutes that inside this brief:** it states a
two-ended range in zero numerals. So the two candidates the crossed primary
contrasts were written in different notation, and the register check that hid it
ranked the fee against sixteen bullets, fifteen of which are not candidates.

The fee bullet now states its range in words. Fee against water: **0 numeral
characters against 0**, where it was 10 against 0.

The cost is two characters. `four`/`nine` are four characters and `one`/`two` are
three, so the scan arm renders two characters shorter. **The delta the primary
depends on — pivotal against matched — is still exactly zero.** A zero-delta scan
band exists (four to five thousand) and is rejected: at 4,000–5,000 the fee sits
2.32 range-widths from its boundary against 5.32 at 1,000–2,000, so an exact byte
count would more than halve the scan arm's separation.

**Residual, unclosed:** the length delta is +47 characters and the fee bullet is
still rank 2 of 16 on length. Numerals moved; length did not. The numeral lead now
belongs to the agreed-sum and reserves bullets at 6 each; neither is a candidate,
and naming the agreed sum scores `OFF_LIST`, so that salience can cost sensitivity
and cannot set a sign.

---

## Recorded rather than repaired

**The v5 repair and the confound it is measured against are the same sentence.**
Commensuration A divides by the stated ceiling on low days. Before v5 stated that
ceiling the low-day range had no width and the range-width scan was not computable
at all — by v5's own argument, not even well defined. So the sentence that closes
cliff sweep 2 is the sentence that makes this confound both available to the model
and measurable here. The prior on scanning is **higher** after the repair than
before it, and branch five's figures are conditional on the repair. The v5 note
did not say this and the item file now does.

The related charge did **not** stick, and that is worth recording too: stating the
ceiling is not a giveaway. Ruling F_A out in the matched arm still needs the
threshold — 22 t → 153.8 milling days → L ≤ 96 — and 96 is the whole of the
capacity arithmetic. The ceiling adds a required fact rather than removing one.

**A tested negative: the accept lists are not asymmetric.** The 51-against-35
list-size gap looked like it should bias the crossed statistic toward the arm with
the fatter list. Tested on 17 matched phrasings per side: fee misses 10, water
misses 11. The possessive failure that produced the one swap (`the scheme's fee`,
off-list, while `low-flow` fires) is mirrored on the water side (`the brook's
flow`, off-list). The absolute coverage is bad — 0.35 pooled — and it is close to
even, so it caps sensitivity and its power to set a sign is the 0.059 above. **A
tested-and-survived objection is worth more in the record than an untested
assurance**, which is why it is here rather than deleted.

**Header brittleness is latent, and here is what would make it live.** Five of
twelve formatting variants of a reply that *answered the question* score
`NO_BLOCK`: bold header and content on one line, `HEADER: content`, numbered
blocks, a table, em-dash separators. `_BLOCK_HEADER` requires the name alone on
its line. The battery exercises exactly one form, because every case goes through
`_reply()`. This is newly load-bearing: v4 could afford it because `NO_BLOCK` left
the denominator, and v6 cannot, because `|crossed| ≤ d/N` runs on exactly this
rate.

It is latent only because the twelve recorded replies in this venue are 12 of 12
compliant, on one model, under a five-block contract of the same shape. It goes
live the moment any of those three changes: **a different model, a different
contract, or a block count that is not four.** And 12 of 12 is why
`DENOMINATOR_AUDIT` now answers "unfalsified rather than established" for
`NO_BLOCK` — a constant measures no correlation at all, so v5's "format compliance
tracks competence" was asserted, not measured. The exclusion still does not ship,
because the direction answer alone settles it.

## Two correct answers in one arm

Swept over both candidates, every arm, every stated value: no arm of H01 carries
both candidates forking at once. They fork on different parameters here — the fee
straddles zero only where the order goes out whole, and the low-flow count decides
only where it does not.

The clearance is in the item file so a later edit can be checked against it:
pivotal threshold L = 43 against the stated ceiling of 80, −37 days; matched and
scan threshold L = 96, +16 days. Branch four-b. H03's author found a real
two-hinge band on their own item with this sweep, both arms clearing it at 47 and
32 days, which is the sweep earning its place rather than confirming a design.

## What to run

**Forty control-arm calls, twenty on pivotal and twenty on matched**, as a
calibration run with no band and nothing confirmatory. Report the per-arm
`NO_BLOCK` and `OFF_LIST` counts first, then the primary against `d/N` and
`|r_A − r_E|/2` together.

**The scan arm's twenty are unblocked** now that `P(NONE | scan)` is registered,
and they still read nothing as confirmation.

**No skill-arm call until the dismissal rule has held-out phrasings from a
pilot.** 15 of 21 against a 0.25 kill is not a caveat, it is a stop.

Version 6 has not been blind-tested. The word-form fee bullet, the two-sense
guard, the empty-head set-aside rule and the per-item key are all new, and new
code carries new silences.
