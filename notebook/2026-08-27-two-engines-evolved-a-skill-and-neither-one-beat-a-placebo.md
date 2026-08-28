# 2026-08-27 — Two engines evolved a skill, and neither one beat a placebo

Registered in
[the prediction entry](2026-08-27-prediction-the-five-arm-study-before-the-first-call.md)
before the first call, with an
[amendment written mid-run](2026-08-27-prediction-the-five-arm-study-before-the-first-call.md)
after 143 of 4,368 calls and before any comparison was read.

4,368 calls on `ollama/qwen3:1.7b` through Ollama's native surface at a 16,384
window, `keep_alive: 60m`, temperature 0. Local, notional cost $0.

## The result

Nothing beat the placebo. Not the seed skill, not GEPA's winner, not SkillOpt's,
on either set, at the registered bar.

**Unseen: three held-out templates, four holdout seeds, 336 items.**

| arm | accuracy | vs placebo | wins / losses | p | Holm |
| --- | --- | --- | --- | --- | --- |
| skillopt | 0.7054 | +0.0179 | 49 / 43 | 0.3012 | 0.9036 |
| placebo | 0.6875 | | | | |
| off | 0.6845 | | | | |
| on | 0.6786 | -0.0089 | 46 / 49 | 0.6591 | 1.0000 |
| gepa | 0.6280 | -0.0595 | 49 / 69 | 0.9736 | 1.0000 |

**Seen: seven trained templates, two holdout seeds, 392 items.**

| arm | accuracy | vs placebo | wins / losses | p | Holm |
| --- | --- | --- | --- | --- | --- |
| skillopt | 0.8087 | +0.0408 | 42 / 26 | 0.0341 | 0.1022 |
| gepa | 0.7730 | +0.0051 | 37 / 35 | 0.4531 | 0.9063 |
| placebo | 0.7679 | | | | |
| on | 0.7398 | -0.0281 | 26 / 37 | 0.9350 | 0.9350 |
| off | 0.7168 | | | | |

SkillOpt's winner is the closest thing to a result in the study: +0.041 on the
seen set, raw p = 0.034. Holm over the registered family of three takes it to
0.102 and it does not reject. Reporting the raw number as a finding is the
practice this study was built to test, so it is reported here as what it is.

## The predictions, scored

1. **Both searches produce a winner that beats its seed on the seven training
   templates.** Met for SkillOpt, unanswerable for GEPA, and the reason is the
   finding below. SkillOpt scored all nine of its candidates on all 21
   validation items: seed 18 of 21, winner 21 of 21. GEPA scored gen0 on 21 and
   **every candidate after it on three**, so its winner's 1.000 is three items
   out of three and its seed's 0.762 is 16 out of 21. Those two numbers do not
   compare, and the prediction assumed they would.
2. **Both winners again write training-template content into the skill.** Met
   for this pair, and the wider count is worth having: of the six frozen winners
   on disk, **three carry constants lifted from single training items** and three
   carry none. The three are GEPA's seven-template winner (37%, 61%, 2818, 2032),
   SkillOpt's seven-template winner (63%, 213/300) and SkillOpt's matched 20b run
   (199/436, 61%, 1749, 2186, under a heading naming the training data). Two
   engines, two corpora. So this is a common failure of these searches rather
   than a certain one, and the prediction was right about the pair it named while
   being stronger than the record supports as a general claim.
3. **Neither winner beats `placebo` on the unseen set at the registered bar.**
   Met. GEPA at -0.060 adjusted 1.000, SkillOpt at +0.018 adjusted 0.904.
4. **At least one winner beats `placebo` on the seen set.** Missed, and missed
   for the reason the mid-run amendment gave: there is no memorisable constant
   in this corpus to transfer.
5. **`placebo` beats `off` on both sets.** Missed as written. It holds on the
   seen set, 0.7679 against 0.7168, 44 wins to 24, p = 0.010. On the unseen set
   it is 0.6875 against 0.6845, 49 wins to 48, p = 0.500, which is nothing.
6. **The A/A passes, and 19 of 21 items or better hold constant.** Met, and by
   a wider margin than the bar asked for. The placebo was scored a second time
   over all 728 items into its own checkpoint, and **728 of 728 came back
   identical**. Zero disagreements, both passes at 0.7308, p = 1.000. The bar
   was 90.5% constant and the run returned 100%.

Two of six missed, one partly answerable. All are recorded above as they were
registered and none has been rewritten.

The A/A is the number that makes the rest of the table mean anything. Two
scorings of one body under identical conditions disagreed on nothing, so the
differences between arms are differences the prompts caused. Yesterday that was
not true: the same body scored 15 to 19 of 21 across a day, because Ollama
evicted the model between passes and two items answered to whether it had just
been loaded. Pinning `keep_alive: 60m` closed it, and this is the evidence.

## What GEPA's winner did

It scored **0.6280 on the unseen set, below `off` at 0.6845**. An evolved skill
that loses 59 items to an empty prompt and wins 40 is worse than no document at
all, and it is the only arm in the study that is.

The body says why. It carries a rules table asserting renewal at 61% utilisation
and capacity headroom at 37%, with a worked example using 2818 and 2032. Those
are values from single training items. `utilisation_floor` is drawn per item
from `{int: [60, 95]}` and stated in every item's Background, so an arm carrying
61% contradicts a fact its own prompt supplies, on almost every item it meets.

GEPA's winner was also never scored on the validation pool. `lineage.jsonl`
records 12 candidates: gen0 on 21 items, and gen1 through gen11 on three each.
`winner.json` closes it with `score = 1.0, n_items = 3, winner_source = engine`.
The search ran to completion, so the engine's own acceptance rule chose, and it
chose a body whose entire evidence is three items answered correctly.

SkillOpt scored all nine of its candidates on all 21. Its winner is the one
candidate that took 21 of 21.

Neither is a defect in this harness. `_best_validated` exists and would have
picked a body scored on the whole pool, and it is deliberately used only when a
search is budget-stopped. An engine's acceptance rule is part of what the engine
is, and the study tests what an engine hands you. What it hands you, in GEPA's
case, is a skill selected on three items that then loses to an empty prompt on
336.

## What the control arm found that the design did not

The placebo helps on the seen set and does nothing on the unseen set. The
placebo has no training history, so that gap cannot be memorisation. It is a
difference between the template sets themselves.

Which means **the unseen/seen contrast confounds "held out" with "different
scenarios"**, and the study cannot separate them. Any gap between the two sets
in this run has at least two available explanations and this design does not
choose between them. The placebo demonstrated that about the design from inside
the design, which is the argument for carrying one.

What would fix it: the same templates split by seed as well as by template, so a
set difference and a holdout difference can be told apart. That is another run.

## What this does not claim

`arenas.py` registers `ollama` as `dev`, and a `dev` run emits **no verdict**.
This result is scoped to one 1.7B model under these controls and does not move
anything on `SCORECARD.md`.

That limit was tested rather than assumed. A screen-tier run on NVIDIA Build
would carry a verdict, and every model that key can reach solves this corpus with
an empty prompt, so none of them can host it.
([entry](2026-08-27-the-verdict-tier-is-reachable-and-the-corpus-is-not-hard-enough-for-it.md))

The honest summary is narrow and worth stating plainly: on one small local model,
against a length- and structure-matched placebo, with item-matched paired tests
and a correction over the registered family, two skill-evolution engines produced
no gain that survives, and one produced a skill measurably worse than no skill on
scenarios it had not seen.
