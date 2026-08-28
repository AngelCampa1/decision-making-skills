# 2026-08-27 — Prediction: the five-arm study, before the first call

Phase 3's registration. Nothing below has been run. The venue configuration, the
split, the arms, the denominators and the estimator are fixed here; what changes
afterwards changes with an amendment appended to this entry, not by editing it.

## What changed since the plan, and why

Three things, each forced by a measurement made today.

1. **The split holds out templates, not seeds.** Both Phase 2 winners wrote
   their training templates' decision rules into the skill — SkillOpt's under a
   heading reading "Examples from the training data:" — and a rule survives a
   change of seed intact. Fresh seeds over the same ten scenarios would have
   scored memorisation as generalisation.
   ([entry](2026-08-27-both-engines-wrote-the-answer-key-into-the-skill.md))
2. **Residency is pinned.** Two of 21 validation items answer deterministically
   to whether the model was freshly loaded, in antiphase across eleven
   consecutive passes. A search waits minutes on a hosted reflector, which
   crosses Ollama's five-minute default and evicts the model, so Phase 2 sampled
   both states in an order nobody chose.
   ([entry](2026-08-27-the-venue-is-deterministic-and-one-of-its-inputs-was-not-in-the-record.md))
3. **The window is stated rather than inherited.** Calls go through Ollama's
   native surface, the only one that accepts `num_ctx`.

## The configuration

| | |
| --- | --- |
| target | `ollama/qwen3:1.7b`, temperature 0 |
| surface | Ollama native `/api/chat` |
| context window | 16,384 |
| output cap | 4,096 |
| residency | `keep_alive: 60m` |
| reflector (searches only) | `nvbuild/openai/gpt-oss-20b` |

## The split

Passphrase **`evolution-study-v1`**, three templates of ten held out, ranked by
`sha256(passphrase:template_id)`. One passphrase was derived and it is the one
being used; no second was looked at.

**Held out from both searches:** `rel-001-vendor-outage`,
`rel-002-deploy-window`, `rel-009-flight-rebook`.

**Trained on:** `rel-003-oncall-escalate`, `rel-004-inventory-reorder`,
`rel-005-security-patch`, `rel-006-refund-request`, `rel-007-capacity-scale`,
`rel-008-contract-renew`, `rel-010-loan-review`.

Phase 2's winners are **not** the arms. Both saw all ten templates, so both
searches are re-run on the seven, and the frozen winners of those runs are what
the study tests.

## The arms

Five, at a matched token budget, all through the same builder:

| arm | body |
| --- | --- |
| `off` | none |
| `on` | `skills/decision-making/SKILL.md`, frontmatter stripped |
| `placebo` | `skills/decision-making/placebo.md`, token- and structure-matched |
| `candidate` (GEPA) | the frozen winner of the seven-template GEPA search |
| `candidate` (SkillOpt) | the frozen winner of the seven-template SkillOpt search |

The two candidate arms are told apart by `candidate_sha`, which is already a
column on every record.

## The test sets

Minted **after** both winners are frozen, from seeds at or above 10,000, which
neither search can reach — `assert_evolvable` refuses a holdout seed before the
call rather than after the number.

- **Unseen** — the three held-out templates at four holdout seeds: **336 items**.
- **Seen** — the seven trained templates at two holdout seeds: **392 items**.

## What will be computed, from what, over what, by what

> Per arm, accuracy is the number of items `scorers.answer.score_item` marks
> correct over all items in the set, one call per item. Each comparison is
> McNemar's exact test on the discordant pairs between that arm and `placebo`,
> item-matched, one-sided in the direction of the arm helping, computed by
> `stats.paired`, with `stats.multiplicity` applying Holm across the family of
> three. The unseen and seen sets are analysed separately and never pooled.

Family of three, each against `placebo`: `on`, GEPA's winner, SkillOpt's winner.
`off` is reported with an interval and is not in the family; it answers whether
any document helps, which is a different question from whether this one does.

## The bar, computed rather than chosen

Discordance measured today between `on` and `placebo` on the held-out templates
at validation seed 1000, 84 items: **0.250**. At Holm's worst-case α of 0.0167
and 80% power that gives a minimum detectable effect of

- **0.081 on the unseen set** (27 items of 336)
- **0.075 on the seen set** (29 items of 392)

The same 84 items put `off` at 0.595, `placebo` at 0.667 and `on` at 0.702.
**The seed skill's advantage over placebo is 0.036 — three items — and detecting
that would need about 1,700 pairs.** This study cannot resolve it and is not
designed to. It is powered for the effect an evolved skill would have to have to
be worth the search.

## Controls before the run

- **A/A.** `placebo` scored a second time over both sets, with everything held
  identical. A significant difference means the residency pin did not hold and
  the study is void.
- **Falsifier against a known-good case.** `off` already returns 0.595 on these
  items, so a non-zero score is reachable and the scorer reads the same object in
  every arm.
- **Residency recorded per pass**, so the pin is checked rather than asserted.

## Call count

728 items per arm × 5 arms = **3,640 calls**, plus 728 for the A/A = **4,368**,
about 9 hours of wall clock on this machine. Local, notional cost $0, guarded by
call count and clock. The two searches that produce the winners are budgeted
separately at 300 target calls each.

## The predictions

1. **Both searches produce a winner that beats its seed on the seven training
   templates.** Phase 2's did, twice, and nothing about narrowing the corpus
   makes that harder.
2. **Both winners again write training-template content into the skill.** Two
   engines and two reflectors have now done this; a third instance would make it
   a property of the setup rather than of a run.
3. **Neither winner beats `placebo` on the unseen set at the registered bar.**
   This is the study's headline and the one I expect to be right about. The
   effect the engines produce is a fit to the scenarios they saw.
4. **At least one winner beats `placebo` on the seen set.** Memorised rules
   transfer across seeds, so the seen set should show the gain the unseen set
   does not. If both sets come out the same way, that is informative in either
   direction and it is the comparison this design exists to make.
5. **`placebo` beats `off` on both sets.** It did on the calibration items,
   0.667 against 0.595, and a document-shaped prompt helping a 1.7B model is the
   least surprising thing here. It is registered because it is the reason the
   placebo arm exists: a skill measured only against `off` would take credit for
   this.
6. **The A/A passes** — no significant difference between two scorings of
   `placebo` — and 19 of 21 items or better hold constant, matching what the
   residency probe found once the model stopped being evicted.

Predictions 3 and 4 are the study. The rest are checks that it measured what it
says it measured.

---

## Amendment, before the first call: the pool sizes

The registration above fixed the split and the arms and said nothing about how
many items each search draws. Recording the choice as a choice rather than
letting it arrive as a default.

**Training pool 70 items, validation pool 21**, the same two numbers Phase 2
used. They are matched between the two engines, which is the comparison that has
to hold; they are not matched to Phase 2's per-template density, because seven
templates into 70 is ten items each against Phase 2's seven.

What would have measured it instead: a headroom sweep over pool size, which
costs a search per point and answers a question this study is not asking.

---

## Amendment, mid-run: the corpus has no memorisable threshold

Written while the study was running, after 143 of 4,368 calls. What had been
read at that point was one partial count for the `off` arm and nothing else: no
comparison, no second arm, no test. The predictions above stay exactly as
written and will be scored as written.

Reading the two frozen winners against the templates they were searched on
turned up something the registration should have checked and did not.

Both winners hard-code a threshold. GEPA's carries a rules table:

> | Contract renewal | 61 % utilisation of *paid seats* | `Utilisation = ActiveSeats / PaidSeats` | If `Utilisation ≥ 0.61` → **renew** else **renegotiate** |

SkillOpt's carries 63% for the same template, with the arithmetic
`213/300 = 0.71` beside it. Two engines, two different constants, one rule.

Neither constant is a property of the rule. In
`datasets/templates/rel-008-contract-renew.yaml` the floor is
`utilisation_floor: {int: [60, 95]}`, drawn fresh for every item, 36 values
wide. Then the Background of every item states it outright:

> Policy is to renegotiate whenever utilisation falls below
> {utilisation_floor}% of paid seats.

All ten templates are built this way. Every `decide.expr` in the corpus compares
two quantities that are both drawn per item, and every threshold among them
appears in the prompt. There is no constant anywhere in this corpus worth
learning.

**This breaks the mechanism prediction 4 rests on.** That prediction said
memorised rules transfer across seeds, so the seen set should show a gain the
unseen set does not. Memorised *constants* do not transfer across seeds here,
because a fresh seed redraws the threshold. On this corpus, holding out
templates and holding out seeds are the same test against a memorised constant.

Prediction 4 therefore has no mechanism behind it that I can name, and it was
registered with one. It stays, it will be scored, and if it misses, this is why.

Prediction 3 gains what prediction 4 loses. An arm asserting
`Utilisation ≥ 0.61` contradicts a fact its own prompt states, for 35 of the 36
floors it could face. An edit like that can lose items the placebo wins, on both
sets.

What this does not change: the split, the arms, the denominators, the estimator,
the bar, or any prediction. A corpus with nothing memorisable is a harder test
of these engines. A search that writes a constant into the skill anyway is
exactly the behaviour worth measuring.
