# 2026-09-02 — Prediction: the five-arm study, run again, with the bodies kept

The second registration of the evolution study. Nothing below has been run
except the screen this entry is built on, which made no skill call. The venue,
the split, the arms, the denominators, the estimator and the bar are fixed here.
What changes afterwards changes with an amendment appended to this entry.

The first run is
[registered](2026-08-27-prediction-the-five-arm-study-before-the-first-call.md),
[published](../results/evolution-study/2026-08-27-53b4965-five-arm/README.md)
and [written up](2026-08-27-two-engines-evolved-a-skill-and-neither-one-beat-a-placebo.md).
Its defects, found by the audit of 2026-08-31 and the truth review of 2026-09-01,
are the reason for this one. Each is named below with what replaces it.

## What changed since the first run, and why

1. **The bodies are committed.** Both winners of the first run are gone:
   `results/evolution/` was ignored, nothing was committed, and a content-hash
   search of the machine found neither. The `.gitignore` now re-includes
   `winner.md`, `winner.json`, `lineage.jsonl`, `run.json` and `search.log` per
   search directory (commit `80ab63b`), and the searches this entry registers
   are committed the moment they freeze.
2. **Seven unseen templates, not three.** With three held-out clusters a
   one-sided sign-flip test cannot return a p below 2^-3 = 0.125, so the
   first run's unseen primaries could never have rejected at the template
   unit. Seven clusters floor the test at 2^-7 = 0.0078, under the Holm
   worst-case threshold of 0.0167.
3. **Two passes per arm, arms interleaved by item.** The first run made one
   pass per arm and ran the arms in blocks, so a venue drift during one block
   would have read as an arm effect. `de study --passes 2 --chunk 8` now runs
   every arm over each chunk of eight items before moving on, and scores each
   arm twice (commit `80ab63b`).
4. **Each winner gets its own placebo.** The first run's single placebo was
   matched to the seed skill, and SkillOpt's winner was 2.59 times its length.
   Each evolved winner here is compared against a placebo matched to it on
   word count within 15%, heading count and fence count, checked by
   `solvers.arms.check_placebo_match` before the run starts.
5. **The scorer strips the control token.** `qwen3:1.7b` echoes `/think`
   after its answer, and the first run's scorer refused 87 such answers, 84 of
   them correct. `scorers.answer.parse_answer` now strips it (commit
   `f686981`). The screen below saw 22 echoes in 532 calls, every one parsed.
6. **The venue is a different machine.** Apple M5, 16 GB, macOS 26.4.1,
   Ollama 0.33.2, `qwen3:1.7b` digest `8f68893c685c`. The first run's machine
   was not this one and its Ollama version is not in that run's record. The
   screen below is the calibration for this venue; nothing from the first
   run's per-template readings is carried across.
7. **The reflector waits on a rate limit.** The first run's GEPA search hung
   for hours on HTTP 429 from NVIDIA Build. A 429 now maps to
   `RateLimitedError`, the reflector retries on a ten-attempt schedule, and
   the breaker stops the search through a path GEPA cannot swallow (commits
   `c3aafa9`, `680ea43`).

## The configuration

| | |
| --- | --- |
| target | `ollama/qwen3:1.7b`, temperature 0, one worker |
| surface | Ollama native `/api/chat` |
| context window | 16,384 |
| output cap | 4,096 |
| residency | `keep_alive: 60m` |
| reflector (searches only) | `nvbuild/openai/gpt-oss-20b` |
| corpus | `datasets/templates` and `datasets/templates-hard`, nineteen templates |
| study code | `de study` at `28ddfab` or later |

## The screen this design is computed from

`scripts/screen_templates.py`, the `off` arm, 28 items per template at seed
10000, 532 calls, 9.9 s per call on average and 7.5 s at the median. Accuracy,
parse rate and informedness J over parsed rows, two-option templates all:

| template | accuracy | parse | J | class |
| --- | --- | --- | --- | --- |
| `hrd-001-warranty-claim` | 0.964 | 1.000 | +0.929 | ceiling |
| `hrd-002-shipping-escalation` | 0.750 | 1.000 | +0.500 | room |
| `hrd-003-deposit-notice` | 0.714 | 0.857 | +0.664 | room |
| `hrd-004-sample-retention` | 0.536 | 1.000 | +0.071 | chance |
| `hrd-005-customs-clearance` | 0.893 | 1.000 | +0.786 | room |
| `hrd-006-appeal-window` | 0.964 | 1.000 | +0.929 | ceiling |
| `hrd-007-pension-vesting` | 0.464 | 0.964 | -0.049 | chance |
| `hrd-008-deposit-notice-costed` | 0.750 | 0.929 | +0.615 | room |
| `hrd-009-shipping-escalation-reversed` | 0.536 | 0.893 | +0.208 | chance |
| `rel-001-vendor-outage` | 0.714 | 0.857 | +0.600 | room |
| `rel-002-deploy-window` | 0.714 | 1.000 | +0.429 | room |
| `rel-003-oncall-escalate` | 0.964 | 1.000 | +0.929 | ceiling |
| `rel-004-inventory-reorder` | 0.607 | 1.000 | +0.214 | chance |
| `rel-005-security-patch` | 0.679 | 1.000 | +0.357 | room |
| `rel-006-refund-request` | 0.750 | 1.000 | +0.500 | room |
| `rel-007-capacity-scale` | 1.000 | 1.000 | +1.000 | ceiling |
| `rel-008-contract-renew` | 0.679 | 1.000 | +0.357 | room |
| `rel-009-flight-rebook` | 0.464 | 0.893 | +0.038 | chance |
| `rel-010-loan-review` | 0.964 | 1.000 | +0.929 | ceiling |

Overall 0.742 over 532. The screen directory is a working file under
`results/screens/` and is not committed; the table above is its `summary.json`
in full, and the records carry `template_id`, `seed`, `item_id`, `expected`,
`parsed` and `duration_ms` per row.

**Classes, by a rule fixed before the table was read.** A template with J
below 0.3 is *chance*: the model is not deciding on it, the criterion the
[2026-08-28 entry](2026-08-28-three-of-ten-templates-carry-no-signal-and-the-arms-advantage-is-not-discrimination.md)
set. A template at accuracy 0.95 or above is *ceiling*: there is no room for
any document to help. The rest have *room*. Five, five and nine.

Twenty-eight items put a 95% interval about ±0.17 wide on each accuracy, so a
template near a boundary could sit on the other side of it. The rule is
applied to the reading, once, and the boundary cases stay where they fell.

## The split

**Chance templates run in neither set.** They would add clusters that carry no
signal to whichever side they landed on.

**The unseen set is the seven room templates ranked lowest by
`sha256("evolution-study-v2:<template_id>")`**, the same derivation
`evolution.holdout.template_split` makes, applied to the nine. One rule sat on
top of it: `hrd-008-deposit-notice-costed` is `hrd-003-deposit-notice` with two
cost facts added and nothing else changed, so a search that trains on one has
seen the other, and the pair goes to the same side whichever member is drawn
first. The rule did not bind: both were in the lowest seven.

**Unseen, held out from both searches:** `hrd-003-deposit-notice`,
`hrd-005-customs-clearance`, `hrd-008-deposit-notice-costed`,
`rel-001-vendor-outage`, `rel-002-deploy-window`, `rel-005-security-patch`,
`rel-008-contract-renew`.

**Trained on:** the two remaining room templates,
`hrd-002-shipping-escalation` and `rel-006-refund-request`, and the five at
ceiling, `hrd-001-warranty-claim`, `hrd-006-appeal-window`,
`rel-003-oncall-escalate`, `rel-007-capacity-scale`, `rel-010-loan-review`.

That is a hard training set for a search: five of its seven templates leave
an empty prompt nothing to improve, and `hrd-002` is the one the
[policy-selection entry](2026-08-28-policy-selection-is-the-lever-and-it-costs-the-small-model.md)
found one-sided. It is what the derivation produced, and a search that writes
training content into its winner anyway is the behaviour under test.

One passphrase was derived and it is the one being used. No second was looked
at.

## The arms

Seven, at a matched token budget, all through `solvers.arms.build_arm`, told
apart by label and `candidate_sha`:

| arm | body | compared against |
| --- | --- | --- |
| `off` | none | reported outside the family |
| `on` | `skills/decision-making/SKILL.md`, frontmatter stripped | `placebo` |
| `placebo` | `skills/decision-making/placebo.md` | |
| `gepa` | the frozen winner of the seven-template GEPA search | `placebo-gepa` |
| `placebo-gepa` | a placebo matched to `gepa`'s winner | |
| `skillopt` | the frozen winner of the seven-template SkillOpt search | `placebo-skillopt` |
| `placebo-skillopt` | a placebo matched to `skillopt`'s winner | |

The two per-winner placebos are written after the winners freeze and before
any study call, by the same method as `placebo.md`: prose about deciding that
carries no rule, no threshold and no scenario, at the winner's word count
within 15% and its heading and fence counts exactly. `check_placebo_match`
refuses the run otherwise. All three placebo bodies are committed beside the
winners.

## The searches

Two, on the seven training templates only, each with the settings of the first
run: 70 training items from seeds 0 and 1, 21 validation items from seed 1000,
300 target calls for GEPA and SkillOpt's own loop of about 261, context window
16,384, output cap 4,096, reflector `nvbuild/openai/gpt-oss-20b`. Each writes
`winner.md`, `winner.json`, `lineage.jsonl`, `run.json` and `search.log` under
`results/evolution/`, and each is committed as soon as it freezes.

`assert_evolvable` refuses a holdout seed before the call is made, so no search
can reach the test sets.

## The test sets

Minted after both winners are frozen, from seeds derived from the passphrase
and at or above 10,000.

- **Unseen** — the seven held-out templates at three holdout seeds
  (10104, 10552, 10996): **588 items**.
- **Seen** — the seven trained templates at two holdout seeds
  (10104, 10552): **392 items**.

Twenty-eight items per template per seed, as in the first run.

## What will be computed, from what, over what, by what

> Per arm, accuracy is the number of pass-1 items `scorers.answer.score_item`
> marks correct over all items in the set, one call per item. Each registered
> comparison is McNemar's exact test on the discordant pairs between an arm and
> its control named in the table above, item-matched, one-sided in the
> direction of the arm helping, computed by `stats.paired.mcnemar_exact`, with
> `stats.multiplicity.holm` across the family of three. Beside each, the
> cluster sign-flip test of `stats.cluster.cluster_sign_flip` over the per-item
> differences with the template as the cluster, one-sided, uncorrected. The
> unseen and seen sets are analysed separately and never pooled. Pass 2 is
> never in a registered comparison; it measures the instrument.

**The family of three:** `on` against `placebo`, `gepa` against
`placebo-gepa`, `skillopt` against `placebo-skillopt`.

**The bar for "beats its control":** Holm-adjusted item-unit q below 0.05
*and* template-unit p below 0.0167. Both. The first run registered the item
unit alone and its re-read then split the two, one rejecting and the other
not; that split is not a finding, it is the design being asked a question it
could answer two ways. With seven clusters the template unit can reach 0.0078,
so the bar is reachable on both sets.

**Reported outside the family, secondary, uncorrected:** each winner against
the shared `placebo`, each per-winner placebo against the shared `placebo`,
and `placebo` against `off`. These answer whether length and shape help by
themselves, which is a question about the control, not about the winner.

## The bar, computed rather than chosen

The discordance rate between an arm and its control on this venue is not
measured; the first run read 0.250 on 84 calibration items and 0.25 to 0.30 is
carried as the prior, stated as such. At Holm's worst-case α of 0.0167, 80%
power, one-sided, `stats.power.minimum_detectable_effect`:

| set | pairs | discordance | design effect 1.0 | design effect 2.0 |
| --- | --- | --- | --- | --- |
| unseen | 588 | 0.25 | 0.061 | 0.086 |
| unseen | 588 | 0.30 | 0.067 | 0.094 |
| seen | 392 | 0.25 | 0.075 | 0.105 |
| seen | 392 | 0.30 | 0.082 | 0.115 |

The design effect the protocol carries is about 2.0, so the honest minimum
detectable effect is the right-hand column: about nine points on the unseen
set and ten on the seen. The largest gain the first run observed was 0.041.
This study is powered for the effect an evolved skill would need to be worth
the search, and not for the seed skill's three-item edge, which would still
need about 1,700 pairs.

**Floors.** Seven clusters on each set: 2^-7 = 0.0078 for the template-unit
test, one-sided. Reachable under 0.0167 on both sets.

## Controls before the run

- **Falsifier against a known-good case.** `off` scored 0.742 over the 532
  screen items, and every template in either set carries signal, so a
  non-zero score is reachable in every arm and the scorer reads the same object
  in each.
- **Pass agreement, per arm.** Each arm's pass 2 is compared with its pass 1
  item by item, two-sided exact McNemar, in the `passes` block of
  `analysis.json`. This is the like-for-like repeat and the number to quote
  for instrument noise. A pass agreement below 0.95 identical on any arm means
  the residency pin did not hold and the study is void.
- **A/A on the shared placebo.** Kept from the first run, in
  `records-aa.jsonl`, with one caveat written down now: `de study` runs the
  A/A as one arm-major block after the interleaved passes, so it repeats one
  arm under a different ordering and is not the like-for-like repeat.
- **Placebo match.** `check_placebo_match` on all three placebo bodies,
  recorded in `run.json`.
- **Control token.** The count of readings whose answer line carried
  `/think` or `/no_think`, per arm, and the count of `unlisted_option` among
  them. The screen read 22 of 532 and 0.
- **Ancestry.** This entry's first commit is an ancestor of the commit that
  runs the searches and of the commit that runs the study, and the run README
  names both.

## Call count

980 items per arm × 7 arms × 2 passes = **13,720 calls**, plus 980 for the A/A
= **14,700**, at 7.5 to 9.9 s per call about 30 to 40 hours of wall clock on
this machine, resumable, guarded by `--max-calls 16000` and
`--max-seconds 172800`. Local, notional cost $0. The two searches are budgeted
separately at 300 target calls each plus reflector calls on a free tier.

## The predictions

1. **Both searches produce a winner that beats the seed skill on the
   21-item validation pool.** Both did in the first run; five ceiling templates
   in the training set make the margin smaller, not the direction.
2. **Both winners carry training content**: a constant, a threshold, a
   worked example or a scenario-specific rule that appears in a training
   item and in no template's fixed text. This is the prediction the bodies
   exist to settle, and it can be checked value by value against the 70
   training items this time. About three in four.
3. **Neither winner beats its matched placebo on the unseen set at the
   registered bar.** The study's headline, and the one I expect to be right
   about. An effect fitted to seven scenarios does not move seven others.
4. **Neither winner beats its matched placebo on the seen set at the
   registered bar.** The first run's amendment found no memorisable constant
   in this corpus, because every threshold is drawn per item and stated in
   the prompt, and the re-read's one seen-set rejection did not survive the
   template unit. If one does reject here, the arm that does it is the one
   whose body carries a rule rather than a constant, and that is checkable.
5. **The per-winner placebos sit within 0.03 of the shared placebo on both
   sets.** Length and shape do not help this model by themselves. If they do,
   the first run's placebo was the wrong control and this design says by how
   much.
6. **`placebo` against `off` is within 0.03 on both sets.** The first run's
   re-read took the placebo's seen-set advantage from 44/24 to 21/24 once the
   token was stripped; what remained was noise.
7. **Pass agreement is at least 0.98 identical on every arm**, and the A/A
   agrees at the same rate. One worker, pinned residency, temperature 0.
8. **The control token appears on fewer than 5% of readings and every one of
   them parses.**

Predictions 3 and 4 are the study. Prediction 2 is what the committed bodies
buy. The rest are checks that it measured what it says it measured.

## What is not predicted

The GEPA acceptance question. The first run's write-up said GEPA accepted its
winner on three items, and the audit found the claim rested on a lineage that
records each candidate once with its first score, which for GEPA is a
minibatch. This run keeps the lineage and the search log, so the score the
engine returned its winner on and the denominator it was computed over can be
read rather than inferred. It is recorded as a check, and the answer goes in
the write-up whichever way it falls.
