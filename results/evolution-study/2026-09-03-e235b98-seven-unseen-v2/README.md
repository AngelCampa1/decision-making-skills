# Seven arms across two passes on a 14-template holdout: the five-arm re-run

**Answer key:** `datasets/templates/` v1, fourteen templates across `datasets/templates/`
and `datasets/templates-hard/` with ground truth computed by the generator.
Corpus identity is the fingerprint rather than a label-set version: unseen `2633c1eab15c`,
seen `0d0f3f002024`, both recorded in `run.json`.

Prediction: [`notebook/2026-09-02-prediction-the-five-arm-study-run-again-with-the-bodies-kept.md`](../../../notebook/2026-09-02-prediction-the-five-arm-study-run-again-with-the-bodies-kept.md)

Outcome: [`notebook/2026-09-10-the-second-evolution-study-two-passes-seven-unseen-and-neither-winner-beats-a-placebo.md`](../../../notebook/2026-09-10-the-second-evolution-study-two-passes-seven-unseen-and-neither-winner-beats-a-placebo.md)

## What was run

14,700 calls on `ollama/qwen3:1.7b`, Ollama's native `/api/chat` at a 16,384
context window, output capped at 4,096, temperature 0, `keep_alive: 60m`. Local,
notional cost \$0.

Seven arms, all through `solvers.arms.build_arm`, told apart by label and `candidate_sha`:

| arm | body | compared against |
| --- | --- | --- |
| `off` | none | reported outside the family |
| `on` | `skills/decision-making/SKILL.md`, frontmatter stripped | `placebo` |
| `placebo` | `skills/decision-making/placebo.md` | |
| `gepa` | frozen winner of 2026-09-02 GEPA search (`f7589ca4...`) | `placebo-gepa` |
| `placebo-gepa` | `datasets/placebos/placebo-gepa.md`, matched to `gepa` | |
| `skillopt` | frozen winner of 2026-09-02 SkillOpt search (`7a2e2784...`) | `placebo-skillopt` |
| `placebo-skillopt` | `datasets/placebos/placebo-skillopt.md`, matched to `skillopt` | |

Templates were split by `sha256("evolution-study-v2:<template_id>")`. Seven unseen
templates held out from both searches, seven trained templates. Two passes of
chunks of 8 items, plus an A/A pass on the shared placebo.

## Results

**Unseen: seven held-out templates, three holdout seeds, 588 items.**

| arm | accuracy | vs control | control arm | wins / losses | McNemar p | Holm q | cluster p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `skillopt` | 0.8044 | +0.0918 | `placebo-skillopt` | 115 / 61 | 0.000029 | 0.000086 | 0.0313 |
| `placebo-gepa` | 0.7534 | | | | | | |
| `off` | 0.7500 | | | | | | |
| `placebo` | 0.7143 | | | | | | |
| `placebo-skillopt` | 0.7126 | | | | | | |
| `gepa` | 0.6973 | -0.0561 | `placebo-gepa` | 82 / 115 | 0.9924 | 1.0000 | 0.9453 |
| `on` | 0.6803 | -0.0340 | `placebo` | 64 / 84 | 0.9580 | 1.0000 | 0.8047 |

**Seen: seven trained templates, two holdout seeds, 392 items.**

| arm | accuracy | vs control | control arm | wins / losses | McNemar p | Holm q | cluster p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `gepa` | 0.8724 | +0.0510 | `placebo-gepa` | 43 / 23 | 0.0093 | 0.0280 | 0.0781 |
| `off` | 0.8673 | | | | | | |
| `placebo-gepa` | 0.8214 | | | | | | |
| `skillopt` | 0.8112 | +0.0026 | `placebo-skillopt` | 43 / 42 | 0.5000 | 1.0000 | 0.5000 |
| `placebo-skillopt` | 0.8087 | | | | | | |
| `placebo` | 0.8061 | | | | | | |
| `on` | 0.8061 | +0.0000 | `placebo` | 42 / 42 | 0.5434 | 1.0000 | 0.5391 |

**No arm rejects at the pre-registered bar.** The bar requires both Holm-adjusted
item-unit q < 0.05 and template-unit cluster sign-flip p < 0.0167. SkillOpt on unseen
scenarios clears the item unit (Holm q = 0.000086) but fails cluster sign-flip (p = 0.0313).
GEPA on seen scenarios clears the item unit (Holm q = 0.0280) but fails cluster
sign-flip (p = 0.0781).

## Controls

- **Pass 1 vs Pass 2 agreement:** 588 of 588 identical on unseen (1.0000), 392 of 392
  identical on seen (1.0000), across all seven arms.
- **A/A pass:** 980 of 980 identical (1.0000) on the shared placebo.
- **Control tokens:** 48 of 6,860 calls (0.70%) contained `/think` or `/no_think`;
  all 48 parsed cleanly.
