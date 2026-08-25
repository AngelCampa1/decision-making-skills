# Track H — the `ledger` v2 screen: both repairs applied, and the ceiling held

**2026-08-25.** 1 triplet × 3 arms × 3 instances = **9 blind `claude -p` calls**,
`sonnet`, 0 unparseable. Code at `28311e2`.

**Answer key:** `V01-thurlmere-images-weeks-*.yaml` v2, the `set_version: 2`
stamped in each. No comparison with v1's key is available or attempted.

Prediction: [`notebook/2026-08-25-prediction-can-a-ledger-item-be-repaired-off-the-ceiling.md`](../../../notebook/2026-08-25-prediction-can-a-ledger-item-be-repaired-off-the-ceiling.md),
committed before the item was authored.

**Not a published run.** Sub-agent calls, no checkpoint, no `total_cost_usd`,
nothing for [`SCORECARD.md`](../../../SCORECARD.md). It is a nine-call screen
deciding whether to spend the next two hundred authoring calls.

## The result

```
  base       key  24  read [24, 24, 24]  unanimous True  equal-to-key True
  treatment  key  18  read [18, 18, 18]  unanimous True  equal-to-key True
  control    key  24  read [24, 24, 24]  unanimous True  equal-to-key True

  sensitivity   1.000    specificity   1.000    unaided J   1.000
```

The registered kill: *if the unaided arm reads 3 of 3 unanimous and equal to key,
**Family A closes entirely***, and the finding is about scalar elicitation rather
than about one construct.

**It fires.**

## What the item did differently, and it was not a token effort

Both repairs the L04 review named, applied together, with skeleton identity
preserved:

**R-a, indirect binding.** The core block names no station. It identifies the
governed one by a property — *"whichever station has the least weekly capacity
left once the standing commitments booked against it are taken off"* — and the
sibling that resolves it is a 6,000-a-week commitment that moves the cataloguing
desk from joint-second on headline capacity to lowest on netted capacity. That
bullet read alone says nothing: 6,000 is also quality control's commitment, and
12,000 is also text capture's capacity.

**R-b, multi-input rule.** The rule routes on weekly capacity **and** standing
commitments, so all ten siblings are live. Neither column alone identifies the
station: lowest headline capacity is the imaging room, which is unique and
wrong; largest commitment is a tie. Only the five subtractions resolve it.

**The single-column read is available, integral, and wrong.** It gives 16/16/12 —
no movement where the answer moves, movement where it holds — and being a whole
number it does not announce itself as a mistake.

Verified independently of the author: insert length deltas 196 and 190,
`|a−b|/max = 0.031`; both inserts the same three-line skeleton differing in the
object and the station; the rule sentence occurs exactly once in the base under
whitespace normalisation.

**Sibling width came in at 10 of 10 in every arm** — every bullet load-bearing,
no inert padding, three blind readers naming no bullet they could have dropped.
Against v1's counts of 1-of-2, 3-of-10 and 3-or-4-of-10.

And the readers did the work. Every one of the nine wrote out all five
subtractions. They were not pattern-matching past the structure; they went
through it, and it cost them nothing.

## Predictions, scored

| # | registered | outcome |
|---|---|---|
| 1 | the unaided arm will **not** be unanimous on all three arms | **wrong.** 3 of 3, and 9 of 9 readings |
| 2 | if it fails, it fails on the matched arm | **untested** — conditional on 1 |
| 3 | effective sibling width rises above 3 and stays **below 10** | **wrong on the upper bound.** 10 of 10 |
| 4 | if the repairs can only be met by making the matched fact subtle, they have collapsed into `fit` | **held.** The matched fact is the loudest bullet in the file; its harmlessness sits in a second stated number in a bullet of the same register as the other nine. One authoring pass, no recut. |

Two of four wrong, and both in the direction that flattered the repair.

## What actually closes here

Prediction 4 holding is what makes this decisive rather than inconclusive. The
repairs did **not** cheat by importing `fit`'s mechanism. They were satisfied
honestly, the item got structurally harder by every measure anyone proposed, and
the unaided model did not notice.

The registration's own "where I expect to be wrong" named this outcome:

> there is a real chance it does not come from the binding structure either, but
> from something simpler that neither the reviewers nor I have named: that a
> scenario compact enough to fit one prompt and answerable by one number is, for
> a current model, not hard.

The v2 author reached the same place from the other side, before the screen ran:

> what R-b bought was not more siblings, it was a second column that contradicts
> the first. […] If the ceiling survives this item, the reading available is that
> `ledger`'s dial was never the one under test.

It survived. Across v1 and v2 that is **18 arms and 99 blind readings, every arm
unanimous and every arm equal to key**, spanning six domains, two dial designs
and both a scaffolded and a bare condition.

## The honest limit

**One triplet, three instances, is a screen and not an estimate**, and the
registration said so before it ran. It cannot support a claim about the
population of `ledger` items. What it can do — and what it was budgeted to do —
is decide whether to spend the next two hundred authoring calls, and it decides
that clearly.

The narrower thing it cannot rule out: everything measured here is single-call
scale. Nothing has tested whether these procedures help at volume, over long
context, or across delegation, and this result is not evidence about those.

## Files

| file | what |
|---|---|
| `V01-thurlmere-images-weeks-*.yaml` | the triplet, keys included |
| `V01_DESIGN_NOTE.md` | the author's account of R-a, R-b, the per-arm sibling count, and the salience dimension left open |
| `screen/` | the three prompts as each reader received them, one per directory, plus the manifest the readers never saw |
| `screen-verdicts.jsonl` | the nine readings |
