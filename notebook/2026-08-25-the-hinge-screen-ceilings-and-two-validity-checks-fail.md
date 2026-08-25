# 2026-08-25 — The `hinge` screen ceilings, and two validity checks fail

40 unaided blind readings of `hinge` H01, 20 on the pivotal arm and 20 on the
matched arm, `sonnet`, dispatched at `c9f649a`. Zero failed calls, zero retries,
isolation receipt asserted on all 40. Notional cost $4.0639.

The crossed primary is **+0.850**, 95% bootstrap [+0.725, +0.975]. A blind
adjudicator shown the 40 `LEVERAGE` blocks with arms stripped agreed 36 of 40 and
puts it at **+0.950**, [+0.850, +1.000]. The registered ceiling kill is 0.70.
**It fires.**

Record and every raw reading:
[`results/track-h/2026-08-25-c9f649a-hinge-control-screen/`](../results/track-h/2026-08-25-c9f649a-hinge-control-screen/README.md).

## The finding is about the venue at least as much as the construct

Family A closed this morning at unaided J = 1.000 over 99 readings, across six
domains, two dial designs and both a scaffolded and a bare condition. The reading
taken from it was that a scenario compact enough to fit one prompt and answerable
by one number is not, for a current model, hard.

`hinge` is a different family, a different primary, and a different answer-key
shape. It elicits set membership rather than a scalar: name the single unsettled
detail that would put you on the other course. That was the half of the
generalisation the registration bet on, and it lands in the same place.

**Two of three families are now at ceiling on single-call scale.**

What that does not licence, stated before anyone quotes the number. Nothing here
tests volume, long context, delegation, or work carried across a conversation.
The failures the six procedures describe mostly do not happen inside one call. A
ceiling on a one-shot screen is evidence about the venue, and reading it as
evidence that the procedures are useless would be reading past what was measured.

## The dropout bound is vacuous, not passed

`d`, the difference in readable replies between the arms, came in at 0. Both arms
returned 20 readable of 20, with `NO_BLOCK` at 0 in each. So `d/N` = 0.000 and
the bound `|crossed| ≤ d/N` sits at zero.

The observed 0.850 is outside it, and outside it plus the coverage bound of
0.059. That is the right way to read the primary. It is the wrong way to read the
rule.

**`d = 0` means the `d/N` rule measured nothing here.** The run gives no evidence
either way about whether the bound works, and it must not be recorded as a guard
that has been validated. The bound was derived at v6 precisely because a `d` of 5
would push it above the kill threshold itself. This run never got near that, so
it never tested it.

## Two registered validity checks failed, and they rank with the primary

**`decoys_are_live`.** The check requires each of F_B and F_D to be named at
least once across both arms. Neither was named once in 40 readings. Re-checked
against the raw text: zero F_B or F_D accept phrases appear in any of the 40
`LEVERAGE` blocks.

**`fork_is_real`.** The check puts the minority course at or above 0.15 of
control-arm replies. The pivotal arm returned 20 of 20 `SIGN`, minority share
0.000. The matched arm split 10 and 10, share 0.500, and passes.

Neither failure touches the crossed primary. The primary reads a different block,
asks a different question, and discriminated cleanly by arm: F_A 16 of 20 in
pivotal, F_E 19 of 20 in matched, one swap in either direction. **What the
failures cost is that this item can no longer say anything about decoy
resistance, and that the pivotal arm is not sitting near its recommendation
threshold the way the design assumed.**

One qualification, from the records rather than from the scored block. Searching
the full response text, F_D accept phrases appear in `BASIS` in 10 of the 40
readings and in the free reasoning before the blocks in 14; F_B appears in the
free reasoning of 2. The decoys were considered and set aside, and they were
never chosen as the hinge. `decoys_are_live` reads the scored block, which is the
right thing for it to read, and the item is dead for decoy work either way.

## The prediction, scored honestly

[`2026-08-25-prediction-will-families-b-and-c-ceiling-too.md`](2026-08-25-prediction-will-families-b-and-c-ceiling-too.md)
registered crossed 0.75 and expected the kill at 0.70 to fire.

Direction right. Kill right. **Point estimate low.** 0.75 sits at the very bottom
edge of the machine interval and outside the hand-adjudicated interval [+0.850,
+1.000]. The registration also wrote "I would not be surprised by 0.9", and that
hedge was the better half of the bet. Being right by hedge is a weaker thing than
having predicted it, and the point estimate is what was registered.

Prediction 4, that at least one of the three screens would be uninterpretable for
a reason that is not the model, is **partly borne out and stays open**. This
screen is interpretable for the ceiling question and uninterpretable for anything
about decoy resistance. Whether it resolves depends on `cascade` and `council`.

Predictions 2 and 3 are about those two instruments and are untouched by this
run.

## The adjudicated fraction confirms the v6 note's own claim

1 of 40 = **0.025** against a kill of 0.25, one `ADJUDICATE_NO_CLAUSE` and zero
`ADJUDICATE_MULTI`.

The v6 note measured 15 of 21 procedure-following phrasings routing to
adjudication, which is 0.71 against that same kill, and blocked the skill arm on
it. The note scoped the block to the skill arm on the ground that the control
register behaves differently. **It does.** 0.025 on 40 fresh control-arm readings
is that claim confirmed on data the note did not have, and the block stays
exactly where it was put.

## Two defects in the instrument, neither in the model

The CLI returns two `modelUsage` keys: a one-turn `--model sonnet` call under
`ISOLATION_FLAGS` returns `claude-haiku-4-5-20251001` alongside
`claude-sonnet-4-6`, because the CLI spends a haiku call of its own. Taking the
first key records the wrong tier. The answering model here is taken off the
assistant event and asserted to be sonnet on every reading.

The scorer lost four hits and the blind adjudicator found all four. Every
disagreement is the machine losing a hit and none manufactured a swap, which is
the direction the v6 note predicted. The magnitude is not: the residue cost 0.100
of the denominator on this run.

## What this was and was not

One item, two arms, twenty readings each. A screen, and never an estimate. The
interval is over readings of this item and not over items.

The 40 calls were dispatched directly rather than through
`scripts/run_triggers.py`, so there is no checkpoint and nothing here belongs in
[`SCORECARD.md`](../SCORECARD.md). It is a screen that decides where the next
calls point, and it decides that clearly: `council` is now carrying the track
alongside a `cascade` adjudication that needs judges.

## Appended later the same day: `cascade` closes too, and it is three of three

The section above says two of three families are at ceiling. **It is three.**
`cascade` came in at **J = +1.000**, [+0.772, +1.000], over 40 blind readings,
format-violation gap 0.000, adjudication coverage 1.000 with zero movement. That
run lands from another lane and its record is not in the repository yet.

Family A at unaided J = 1.000 over 99 readings, `hinge` at +0.950
hand-adjudicated, `cascade` at +1.000. Three independent constructs, six domains,
three answer-key shapes, all at ceiling on single-call scale. The limit stated
above is unchanged and now applies to all three: nothing here tests volume, long
context, delegation, or work carried across a conversation.

**And a correction to how the adjudication above should be read.** `cascade`'s
three blind judges had mean pairwise rationale similarity of 0.806 and wrote
identical opening text on 17 of 40 cases, which is what three samples of one
model at default sampling look like. A separate lane is now measuring whether
`scripts/adjudicate.py` behaves the same way.

That does not reach the 36 of 40 above, and the reason is worth stating rather
than assuming. This run's adjudication was **one blind pass** over the 40
arm-stripped `LEVERAGE` blocks, compared against the machine scorer. It is a
scorer-versus-adjudicator comparison, not a between-judge agreement statistic,
so there was never an independence assumption in it to violate. The +0.950 stands
as what it was: one careful re-read of the same 40 blocks, agreeing with the
scorer on 36 and finding four hits the scorer had dropped.
