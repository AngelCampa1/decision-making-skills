# 2026-09-02 — GEPA selected on the valset, our lineage recorded the minibatch, and the winner quotes one training item

The GEPA search for the re-run froze at 15:15. Its winner is committed, and it
answers two questions the first run could not: one the
[2026-08-31 audit](2026-08-31-the-paper-described-a-search-we-did-not-run-and-a-test-that-could-not-fail.md)
raised and left open, and one the
[registration](2026-09-02-prediction-the-five-arm-study-run-again-with-the-bodies-kept.md)
registered as prediction 2.

No study call has been made. Nothing here reads on the study's outcome.

## The search

`de evolve --engine gepa`, target `ollama/qwen3:1.7b`, reflector
`nvbuild/openai/gpt-oss-20b`, the seven training templates, 70 training items
at seed 0, 21 validation items at seed 1000, 300 target calls, 57 minutes. The
run directory is
`results/evolution/2026-09-02-4dcd13f-gepa-seven-template-v2/`, committed at
`a07d1aa` with `winner.md`, `winner.json`, `lineage.jsonl`, `run.json` and
`search.log`.

## The acceptance claim was our logging, not GEPA's rule

The first run's write-up said GEPA accepted its winner on three items. The
audit found the claim rested on `evolution/adapter.py`, which appends each
candidate to the lineage once with the first score it was given, and for GEPA
that first score is a minibatch. It could not be settled: the search records
were gone.

They are here now, and they settle it.

`winner.json` records `score 1.0` over `n_items 3`. The search log records
what the engine did with the same body, at iteration 4:

> Iteration 4: Val aggregate for new program: 0.9523809523809523
>
> Iteration 4: Best program as per aggregate score on valset: 1

The log lists individual scores for all 21 validation items on that
candidate, twenty at 1.0 and item 16 at 0.0. The proposal text at iteration 4
is byte-identical to `winner.md` and hashes to
`f7589ca49b4dda93`, the `candidate_sha` in `winner.json`.

**GEPA evaluated its winner on the full 21-item validation pool and selected
it on that aggregate.** The three-item score is the minibatch the candidate
was first seen on, which is what our adapter stored. The claim as the first
write-up made it is wrong, the mechanism the audit proposed is right, and the
paper's contribution 4 should say so plainly rather than hedge.

`run.py:584` already carries the comment describing this hazard, and
`_freeze` falls back to the lineage score when the engine hands back no
score. Reading `winner.json`'s `score` and `n_items` as the acceptance
denominator is the defect. What the field means is the first score recorded,
and it should be named that way.

## Prediction 2, confirmed for GEPA, with the item named

The winner is titled "New Decision-Making Instruction for Warranty Claims"
and reads in part:

> **Warranty period**: 23 months (standard) – *source: "Alder covers this
> model for 23 months from the date of purchase."*

> **Purchase date / age**: 22 months ago – *source: "The unit on ticket 40078
> was purchased 22 months ago."*

Ticket 40078 appears in exactly one record of the search, item
`hrd-001-warranty-claim#v0-d4-early` at seed 0, a training item whose expected
answer is `honour_claim`. In `datasets/templates-hard/hrd-001-warranty-claim.yaml`
the ticket number is `{int: [10000, 99999]}`, the term is `{int: [12, 60]}`
and the age is `{int: [1, 72]}`, each drawn per item. None of the three is a
property of the rule, and the template states all of them in the prompt of
every item.

So the engine wrote one training item into the skill, ticket number included,
and its acceptance rule could not tell: the body scored 20 of 21 on the
validation pool, because twenty of those items are answerable from the prompt
whatever the document says.

This is the third and fourth instance of the behaviour across two engines,
counting the first run's two. It is now recorded with the body committed and
the source item named, which the first run could not do.

## What is not settled

Whether the winner beats a placebo matched to it. That is the study, it has
not run, and the registration predicts it does not.
