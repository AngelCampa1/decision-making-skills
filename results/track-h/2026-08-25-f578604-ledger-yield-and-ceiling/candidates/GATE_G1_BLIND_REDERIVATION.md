# G1: blind re-derivation

**Audience:** the dispatcher. The block under "The brief" is what a G1 instance
receives, verbatim and alone.

## What this gate is for

It caught `t01` and `t05`, and nothing else did. Both had a **governing** arm
that admitted a second defensible reading, which is worse than an ambiguous
matched arm: it depresses the probability of change on the arm where change is
scored as success, so it biases the primary toward zero and makes a null
unreadable.

## How it runs

**Nine calls per candidate: three arms times three independent instances.**

**One prompt per call.** An instance must not know that variants exist. An
instance shown all three arms reasons comparatively, hunting for the difference,
which is not what the model under test does. It would manufacture both the
movement and the non-movement.

**No arm labels anywhere**, including in any filename or header the instance can
see. The dispatcher unblinds afterwards.

**The instance sees the `prompt` block and nothing else.** Never `key`, never
`meta`, never `elicited` as a separate section. The prompt already ends with the
question and the answer-format sentence; handing over `elicited` separately
signals that this is an instrument rather than a situation.

## The asymmetry, which is the whole design

Requiring three blind instances to agree unanimously that the matched arm does
**not** move selects for items whose matched arm is easy. That drives specificity
to 1.0 and manufactures a ceiling on purpose, which is how five previous venues
here closed.

| arm | rule | why |
|---|---|---|
| base | unanimity **required** | an indeterminate base is noise, and the movement threshold is derived from it |
| governing | unanimity **required** | an ambiguous governing arm makes a null unreadable |
| matched | **recorded, never gated** | disagreement is either ambiguity, which is fatal, or difficulty, which is the point |

> **G1 does not cut. G1 produces a disagreement dossier. G2 adjudicates it.**
> A minority reading a competent professional could defensibly hold is
> *ambiguity*, and the item is cut. A minority reading no professional would
> defend is *difficulty*, and the item survives with that disagreement recorded
> as its measured difficulty.

## Dispositions the dispatcher applies

| observation | disposition |
|---|---|
| base: three disagree, or three agree on a value the key does not carry | **cut** — the base is under-specified, or the key is wrong |
| base: two of three | route the minority to G2 as an objection |
| governing: any disagreement | route to G2 as an objection, flagged disqualifier 15 |
| governing: unanimous and equal to base | **cut** — the governing fact does not govern |
| governing: unanimous, differing from base and from the key | **cut** — the key is wrong |
| matched: any pattern | **recorded, never gated.** Disagreements route to G2; the rate is the item's difficulty. |
| any arm: an instance volunteers a second defensible reading | route the **named fork** to G2 verbatim, whatever its answer line said |

That last row is where `t01` and `t05` live. The old pass caught them because a
reader happened to notice. This catches them because the brief asks for the fork
by name.

## The brief

> You are a licensed professional practising in the field this scenario belongs
> to. You are reading one person's situation and answering one factual question
> about it.
>
> Answer from the text in front of you and from ordinary professional knowledge
> of the field. There is no additional context, no earlier message, and nothing
> has been withheld from you as a test.
>
> Before your answer, show your arithmetic: every quantity you used, where in the
> text you got it, and the operation you applied. Where a step depends on a
> professional convention rather than on something stated in the text, name the
> convention.
>
> If the text admits more than one defensible reading that produces different
> numbers, say so explicitly, give the number for each reading, and then give the
> one you would act on. Do not pick one silently and do not average them.
>
> End your reply with exactly one line in this form and nothing after it:
>
> `ANSWER: <number> <unit>`
>
> The number is a bare numeral. Do not write a range, an interval, an
> approximation, or a second number on that line.
