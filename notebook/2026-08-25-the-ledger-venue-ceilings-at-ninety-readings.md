# 2026-08-25 — `ledger` ceilings, and ninety readings say so before the corpus was built

Registered in
[`2026-08-25-prediction-the-quality-venue-and-the-tau-rule.md`](2026-08-25-prediction-the-quality-venue-and-the-tau-rule.md).
This entry reports the yield probe and a control arm that was not in the plan
until the probe made it cheap.

**Not a published run.** These 90 calls went through `lite` sub-agents on Sonnet,
not through `scripts/run_triggers.py`. No checkpoint, no `total_cost_usd`, no
provenance record, and nothing here belongs in `SCORECARD.md`. It is a probe, and
it decides where the next real run points.

## What was asked

Five `ledger` triplets, authored in parallel in five domains, K = 10 siblings
each. The kill: **fewer than 3 of 5 surviving blind re-derivation and an
adversarial review means the volume dial does not solve the yield problem.**

## What came back

| triplet | domain | verdict |
|---|---|---|
| L01 | veterinary referral scheduling | **cut** — the governing arm's obstacle is remediable |
| L02 | textile finishing throughput | survives |
| L03 | land registration | survives |
| L04 | seed certification | pending an independent second review |
| L05 | cask cellar stock | **cut** — triviality, and disqualifier 14 |

L01 died the way two items died in the previous pass, which is worth naming
because it is now three for three. Its governing insert said a records office was
shut. A records office is administrative and a referral is signed by a
veterinary surgeon, so the competent adviser answers *ring the vet, have her sign
it, post it directly* — and lands on the base value. Disqualifiers 15 and 12 fire
through one sentence: the arm that must move does not, the better reasoner is the
one who fails to move it, and the primary is biased toward zero by a defect in
the item rather than by anything about the model.

The registered protocol grants a repair round to G3 and none to G1 or G2, so L01
is cut rather than patched. Its three named repairs are design rules for the next
pass instead.

## The number that matters, and it is not the yield

G1 pays for three blind re-derivations of every arm. That is 45 readings, and
they are also the control arm the plan was going to buy separately in Phase 3.

**Fifteen arms. Fifteen unanimous. Fifteen equal to the key.** Sensitivity 1.000,
specificity 1.000, J = 1.000.

That number alone proves nothing about the ceiling, and reading it as if it did
was the first thing to get right. G1's brief demands the arithmetic step by step
and tells the reader to declare a second defensible reading if one exists — which
is close to what `ledger` itself instructs and nothing like an unaided model. So
J = 1.000 there bounds the **treated** arm. It says the items are solvable and
the keys are right. It says nothing about headroom, and an unaided reader given
less help could have done worse, which would have meant *more* room for the skill
rather than less.

So the same fifteen prompts were run again with the format contract held
identical and the reasoning scaffold deleted — no professional framing, no demand
for arithmetic, no warning that a fork might exist. 45 more readings.

```
g1-verdicts.jsonl      45 readings  15/15 arms unanimous  15/15 equal to key
off-verdicts.jsonl     45 readings  15/15 arms unanimous  15/15 equal to key
```

**Unaided J = 1.000.** The registered kill is unaided J at or above 0.70. It
fires, and `ledger` closes.

## Why it closed, which the reviewers reached independently

Three adversarial reviewers, working on different items and unable to see each
other, all arrived at the same objection and none of them was asked to look for
it.

One counted the effective ledger width at **1-of-2** rather than 1-of-10: of ten
siblings, five were past events that cannot start a forward count, and of the
five forward-dated documents only two came from bodies that could satisfy the
rule. Another found **three of ten** siblings doing arithmetic work and seven
inert, scoring the item on one name lookup and one subtract-and-divide. A third
found **six of ten** written pre-closed by a terminating clause — *was
discharged*, *was withdrawn*, *went unconditional*, *holds it ready to lodge* —
leaving three bullets carrying a live condition, and put effective K at 3 or 4
against an advertised 10.

That is the finding. **Volume buys retrieval load, not decision difficulty.** A
reader must scan all ten siblings to know which is slowest or which body is the
registered practice, so the retrieval is real. But once scanned, no discrimination
is required: the siblings that could matter are separable from the ones that
cannot by type, in one pass, with no domain reasoning. `ledger` was built on the
hypothesis that difficulty could be bought from a dimension carrying no label.
Volume carries no label — that part held, and the matched labels survived every
attack. It just does not buy difficulty.

One reviewer also found the leak that the discriminator cannot see: **"the tied
beer" is a definite description resolving to exactly one name.** Lexical overlap
with the rule sentence reads 0.0 while referential overlap is 1.0, and
`scripts/separability.py` is token-based, so it will report clean. The same shape
appears as "her own practice" in L01. Any future corpus needs a referential
overlap feature or this class of leak is invisible by construction.

## What this costs and what it saves

The plan budgeted roughly 3,100 calls for the corpus factory and 800 more for
Phase 3 control arms before this question got an answer. It cost **90**, because
G1's blind readings are a control arm that someone already paid for and nobody
had thought to read that way.

The generalisation is worth keeping: **a gate that reads every arm blind has
already measured the unaided ceiling, whatever else it was built to do.** Read it
before authoring the corpus, not after.

## Where I was wrong

I expected the yield kill to be the decision point and wrote the state file to
treat it that way. It was not. Yield came in at 2 cut, 2 survived, 1 pending —
genuinely close to the 3-of-5 line and genuinely uncertain — and it stopped
mattering the moment the control arm read 1.000, because a stratum with no
headroom does not become worth building by authoring it more successfully. The
kill I registered on yield was answering a cheaper question than the one on the
table.

I also expected the ceiling argument to run through the items being *badly
authored*. It does not. L02 and L03 survived adversarial reviews that raised eight
and six objections respectively and made none of them stick. The items are sound.
The construct is what ceilings.

## What happens next, and it is already registered

Families A, B and C were made independent for exactly this. A kill closes a
stratum, not the track.

- **Family A** drops to `timing`, whose difficulty comes from category rather
  than volume — a different dial, with pass-two evidence behind it and no
  measurement yet. It gets the same 90-call control-arm probe **before** any
  corpus is authored. If it ceilings too, Family A closes entirely and that is a
  result about scalar elicitation rather than about three constructs.
- **Families B and C** carry the track, and both pilots killed their own
  registered primary on first contact.

  **`cascade`.** The primary was P(named as foreclosed | genuine foreclosure)
  less P(named | matched effect). One blind instance per arm: the foreclosing arm
  named the planted target and two more besides, the effect-only arm returned
  *keep the £12,600 grant without repaying it*. The structural reason is not
  about this item and not about n: the block asks what the writer can do today and
  cannot do afterwards, and **doing without something is an ability**, so any
  effect that touches the actor supports a *keep* or *avoid* phrasing. Step 2's
  effect/foreclosure partition is real as advice and unreadable by a membership
  scorer. The repair was already in the file — one target read across both arms,
  scoring correctly on the same two responses.

  **`council`.** 12 genuine blind calls found that **flip rate cannot be the
  primary**, because a true tie item coin-flips within a single ordering, leaving
  no floor for a cross-order rate to clear. Second-position rate replaces it, with
  a null of exactly 0.5 for any model at any noise level given balanced
  orderings. On the first call of the asymmetric item the model computed the
  £15,500 headroom against a £212,000 machine, wrote the figure down, and
  recommended the facility that cannot pay for it.

  **Neither pilot's rates are a measurement.** One and two observations per arm
  are not J, and nothing above should be read as one. What the pilots bought is
  the two design arguments, which stand independent of n and would each have
  invalidated a corpus authored on the registered primary.

The three instruments were not a hedge that happened to pay off. They were the
reason a kill on the largest one did not stop anything — and the two pilots are
the reason the next corpus will be authored against a primary that survives
contact rather than one that reads well on paper.
