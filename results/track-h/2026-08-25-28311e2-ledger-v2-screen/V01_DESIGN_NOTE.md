# V01, a `ledger` triplet built under R-a and R-b, and what the repairs bought

**Audience:** the evaluating reader holding
`notebook/2026-08-25-prediction-can-a-ledger-item-be-repaired-off-the-ceiling.md`.

One triplet, `V01`, domain `archive_digitisation`, a county record office
digitising a court series. Files:

```
V01-thurlmere-images-weeks-base.yaml        expected_value 24
V01-thurlmere-images-weeks-governing.yaml   expected_value 18
V01-thurlmere-images-weeks-matched.yaml     expected_value 24
```

`set_version: 2`. These items are authored under R-a and R-b and are not
comparable with the v1 candidates, so the version refuses the comparison.

Five stations each carry two figures: a weekly capacity and a standing
commitment booked against it. Ten siblings, five of each, interleaved. The
answer is 144,000 images divided by the smallest netted figure. Every arm
divides exactly and the tolerance is 0.

| station | capacity | commitment | netted |
|---|---|---|---|
| preparation | 13,000 | 3,000 | 10,000 |
| imaging | 9,000 | 1,000 | 8,000 |
| text capture | 12,000 | 3,000 | 9,000 |
| cataloguing | 12,000 | 6,000 | **6,000** |
| quality control | 14,000 | 6,000 | 8,000 |

## R-a, indirect binding

The core block identifies the governed station by this property:

> whichever station has the least weekly capacity left once the standing
> commitments booked against it are taken off

No station is named anywhere in the core block. The five station names appear
only in the list of what an image passes through, symmetrically, three mentions
each.

The sibling that resolves the property is the second bullet:

> The cataloguing desk carries a standing commitment of 6,000 images a week to
> the Hallowfen parish registers, agreed on 2026-03-05 and running to
> 2029-03-05.

That bullet is what moves the cataloguing desk from joint-second on headline
capacity to lowest on netted capacity, and it is the only bullet that does. It
resolves the property only in company: reading it alone tells a reader nothing,
because 6,000 is also quality control's commitment and 12,000 is also text
capture's capacity.

**Neither column alone names the governed station.** The lowest capacity is the
imaging room at 9,000, unique and wrong. The largest commitment is 6,000, tied
between cataloguing and quality control, so it picks out nobody. Only the five
subtractions resolve it.

## R-b, multi-input rule

The rule sentence, occurring once, character for character:

> Weatherall Instrument Services runs every station for us; the finish date is
> set by whichever station has the least weekly capacity left once the standing
> commitments booked against it are taken off, and by nothing else.

It routes on two quantities, **weekly capacity** and **standing commitments**.
Both are named in the sentence, so neither column can be discarded by reading
it. The siblings it makes live, all ten:

| live because it carries a weekly capacity | live because it carries a standing commitment |
|---|---|
| preparation bench, 2026-02-09, 13,000 | cataloguing desk, 2026-03-05, 6,000 |
| imaging room, 2026-05-11, 9,000 | text capture station, 2026-01-13, 3,000 |
| quality control room, 2026-06-02, 14,000 | preparation bench, 2026-04-21, 3,000 |
| text capture station, 2026-07-07, 12,000 | quality control room, 2026-07-30, 6,000 |
| cataloguing desk, 2026-08-04, 12,000 | imaging room, 2026-08-12, 1,000 |

There is no inert padding. The one-sentence filter that killed seven siblings in
v1 has nothing to bite on, because every bullet carries one of the two inputs
the rule sentence names.

The two columns disagree about which station binds, and that disagreement is
what the item measures. A reader who routes on capacity alone finds the imaging
room and answers 16 in the base, 16 in the governing arm and 12 in the matched
arm: no movement where the answer moves, movement where it holds. That read is
integral too, so it does not announce itself as wrong. It is recorded in the
base key under `single_input_read`.

## Skeleton identity

```
Weatherall Instrument Services commissioned <MACHINE> at Ravensholt on
2026-08-21, and from 2026-08-25 it adds 3,000 images a week to <STATION>'s
capacity.
```

Governing substitutes `a second authority-file terminal` and `the cataloguing
desk`. Matched substitutes `a second overhead book scanner` and `the imaging
room`. Same dates, same magnitude, same position as the eleventh bullet, same
three-line wrap breaking at the same two points. Prompt-length delta from base
is 196 characters against 190, giving 3.1% on `max`.

Both inserts are 24 tokens. Both share exactly seven tokens with the rule
sentence, the same seven. That symmetry is not an accident of drafting: the
first draft named the contractor **Weatherall Imaging Systems**, which put the
token `imaging` in the rule sentence and a second copy of it in the matched
insert only. A token-based separability check would have shown the matched arm
with higher lexical overlap, and a model attending to the actor name would have
had a free signal pointing at the decoy. Renaming the contractor to something
sharing no token with any station closed it.

## Effective sibling width, per arm

Counted as: how many siblings must a reader resolve before the answer falls out.

| arm | width | why |
|---|---|---|
| base | **10 of 10** | the minimum over five netted figures needs all five capacities and all five commitments. A reader who has done four pairs cannot conclude anything about the fifth. |
| governing | **10 of 10**, plus the insert | the insert lifts cataloguing to 9,000, so the new minimum is somewhere else and every other pair has to be in hand to find it. It lands on a tie at 8,000 between imaging and quality control, which cannot be reached without both. |
| matched | **10 of 10**, plus the insert | the insert lifts imaging to 11,000. Confirming that 6,000 still binds means confirming that nothing else fell below it, which is the whole table again. |

Three independent readers, one per arm, each given only the prompt text and
nothing else, reported the same count unprompted and named no bullet they could
have dropped.

**This falsifies registered prediction 3 on its upper bound.** The band was
"above 3 and stay below 10", and the design deliberately left no inert sibling,
so 10 was the ceiling and it was reached. v1's counts were 1-of-2, 3-of-10 and
3-or-4-of-10.

## Blind re-derivation

Three readers, one arm each, no scaffold beyond a request to show working, no
sight of the key or of each other.

```
base       24    matched key
governing  18    matched key
matched    24    matched key, and equal to the base value
```

The matched arm lands exactly on the base value, so there is no governing
matched fact and the item is not cut.

It also went 3 for 3 first time, unaided, with working that reproduced the
intended derivation line for line and no reader volunteering a second reading.
Three readings is a screen and not the probe, and the request for working sits
closer to the G1 brief than to the bare condition. Read with those limits, it is
still the first evidence bearing on registered prediction 1, and it points the
way the prediction bet against.

## Registered prediction 4: did R-a and R-b collapse into `fit`?

**No.** Prediction 4 fires if the repairs can only be satisfied by making the
matched fact subtle. This matched fact is the loudest bullet in the file. It
adds capacity to the station carrying the lowest headline capacity of the five,
which is the station a reader scanning one column would name as the bottleneck.
Nothing about it is hedged or buried. Its harmlessness
lives in a second stated number in a bullet of the same register as the other
nine, which is `ledger`'s mechanism working as designed, and the item never
reaches for `fit`'s neutraliser-subtlety. Authoring cost was one pass with no
recut.

Building it showed something the ruling does not capture.

**What R-b bought was not more siblings. It was a second column that contradicts
the first.** Width went from L02's 6 useful bullets to 10, and on the evidence
above that extra retrieval cost a competent reader nothing. What the two-input
rule adds is a wrong answer that is available, integral, and reachable by
exactly the one-pass scan the v1 reviewers described. If `V01` ever separates
readers, it will separate them there, and the credit belongs to the
contradiction rather than to K = 10.

That has a consequence for the track. The reviewers said volume buys retrieval
and not discrimination. R-a and R-b were proposed as repairs to the binding
structure, and building them out shows that the only difficulty either one
actually manufactures is a trap: a plausible cheaper reading that a careless
reader takes. A trap is a real thing to measure. It is not the volume dial.
If the ninety-reading ceiling survives this item, the reading available is that
`ledger`'s dial was never the one under test.

## Salience: seven of eight closed

**Dimension 4, same alarm, is the one not fully closed.** Read on their own the
two inserts raise interchangeable alarms: another machine went in last week, it
adds three thousand a week, the series will be done sooner. Read against the
capacity column they diverge, and the matched insert is the louder of the two,
because the imaging room carries the lowest headline figure and the cataloguing
desk does not.

The asymmetry runs against the answer rather than with it. It makes the
non-governing fact look more important, so it cannot be used to separate the
arms correctly. It is a trap and not a leak, and a reader who exploits it scores
zero on both treated arms. Repairing it means giving the cataloguing desk the
lowest headline capacity as well, which deletes the disagreement between the two
columns and with it R-b. Recorded in `key.salience_match` rather than repaired.

Dimensions 1, 2, 3, 5, 6, 7 and 8 are closed, with the arithmetic for 5 and the
token counts for 8 written into the matched file.

## Checks run

- The rule sentence occurs once in each of the three prompts, character for
  character once the wrap is collapsed.
- All three arms divide exactly. Rounding convention and tolerance 0 recorded in
  every file.
- Neither `18` nor `24` appears anywhere in any prompt as a standalone numeral
  or as a word, and no date carries `-18`, `-24` or the year 2024. This is the
  leak that cost L05 its readings and the leak that cost L04 its answer.
- Ten preconditions enumerated in the matched file against disqualifier 10,
  including the two the physical setting invites: starvation of the binding
  station, and drain after it. Both are foreclosed by one base sentence, and
  foreclosed identically in both arms.
- Disqualifier 11 computed rather than asserted. The matched correction is
  exactly zero. Under the single-input misreading it is 6 weeks away from where
  the governing fact lands the answer.
- Disqualifier 15 checked on the governing arm: commencement on the stated
  today, an uplift to the input the rule names first, silence about the input it
  names second, and a tie in a minimum that is still one number.
- Every commitment runs to a 2029 date, past the 2027-02-09 end of the longest
  horizon, so no netted figure changes part-way through in any arm.
- Personas, bodies, collections and the contractor are invented.
