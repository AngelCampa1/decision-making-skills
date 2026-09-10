# 2026-09-10 — Prompt constant ablation confirms memorization collapse

784 calls on `ollama/qwen3:1.7b` at temperature 0, context window 16,384, output cap
4,096 across all 392 items of the seven seen templates (seeds 10989 and 10996).

## The question

In the second evolution study, both winning prompts committed to disk carried
verbatim constants from training items: GEPA (`f7589ca4`) quoted `ticket 40078`,
`23 months`, and `22 months` from `hrd-001-warranty-claim`, while SkillOpt
(`7a2e2784`) quoted exact numerical cutoffs for Loan Review (`threshold 665, score
737`), Warranty (`22 < 23`), and Shipping (`10 > 4`).

We tested whether the apparent advantage on seen templates was driven by verbatim
memorization of training numbers or by general procedural reasoning.

We created two ablated prompt variants preserving section hierarchy and token
length (within 1%) while replacing memorized constants and worked-example cutoffs
with generalized symbolic and algebraic rules:
- `datasets/ablations/gepa-ablated.md` (613 words vs 612 original, 25 sections)
- `datasets/ablations/skillopt-ablated.md` (1,735 words vs 1,723 original, 23 sections)

Both were scored item-for-item against the frozen study records from
`results/evolution-study/2026-09-03-e235b98-seven-unseen-v2/`.

## Results across 392 seen items

### GEPA: Original vs. Ablated

| arm | accuracy | delta vs orig | p (McNemar) | wins / losses |
| --- | --- | --- | --- | --- |
| `gepa` (original) | 0.8724 | — | — | — |
| `off` (unprompted) | 0.8673 | -0.0051 | — | — |
| `gepa-ablated` | 0.8597 | -0.0128 | 0.6201 | 30 / 35 |
| `placebo-gepa` | 0.8214 | -0.0510 | — | — |

Per-template breakdown (56 items per template):

| template | original | ablated | delta | placebo | off |
| --- | --- | --- | --- | --- | --- |
| `hrd-001-warranty-claim` | 0.9464 | 0.9643 | +0.0179 | 0.8036 | 0.9821 |
| `hrd-002-shipping-escalation` | 0.8036 | 0.5714 | **-0.2321** | 0.7321 | 0.6607 |
| `hrd-006-appeal-window` | 0.8929 | 0.9821 | +0.0893 | 0.8750 | 0.9464 |
| `rel-003-oncall-escalate` | 1.0000 | 1.0000 | +0.0000 | 1.0000 | 0.9464 |
| `rel-006-refund-request` | 0.6071 | 0.5714 | -0.0357 | 0.4643 | 0.6429 |
| `rel-007-capacity-scale` | 0.9464 | 1.0000 | +0.0536 | 1.0000 | 0.9821 |
| `rel-010-loan-review` | 0.9107 | 0.9286 | +0.0179 | 0.8750 | 0.9107 |

### SkillOpt: Original vs. Ablated

| arm | accuracy | delta vs orig | p (McNemar) | wins / losses |
| --- | --- | --- | --- | --- |
| `off` (unprompted) | 0.8673 | +0.0561 | — | — |
| `skillopt-ablated` | 0.8367 | +0.0255 | 0.2750 | 39 / 29 |
| `skillopt` (original) | 0.8112 | — | — | — |
| `placebo-skillopt` | 0.8087 | -0.0026 | — | — |

Per-template breakdown (56 items per template):

| template | original | ablated | delta | placebo | off |
| --- | --- | --- | --- | --- | --- |
| `hrd-001-warranty-claim` | 0.8214 | 0.8571 | +0.0357 | 0.8214 | 0.9821 |
| `hrd-002-shipping-escalation` | 0.8036 | 0.9464 | +0.1429 | 0.7500 | 0.6607 |
| `hrd-006-appeal-window` | 0.8929 | 0.9464 | +0.0536 | 0.7679 | 0.9464 |
| `rel-003-oncall-escalate` | 0.9286 | 0.9464 | +0.0179 | 0.9821 | 0.9464 |
| `rel-006-refund-request` | 0.3929 | 0.4107 | +0.0179 | 0.4821 | 0.6429 |
| `rel-007-capacity-scale` | 0.9107 | 0.9286 | +0.0179 | 1.0000 | 0.9821 |
| `rel-010-loan-review` | **0.9286** | **0.8214** | **-0.1071** | **0.8571** | **0.9107** |

## Findings

1. **The memorization collapse:** On `rel-010-loan-review`, where SkillOpt's
   winner hardcoded `threshold 665, score 737`, abstracting to generalized
   notation ($S \ge T$) caused accuracy to collapse from **0.9286 to 0.8214**
   ($-0.1071$, a 10.7 percentage point drop), falling below its matched placebo
   (0.8571).
2. **Accidental positive prior:** GEPA's winner hardcoded an unconditional
   positive recommendation (`ANSWER: honour_claim`). When regularized to balanced
   in-term/out-of-term logic, `hrd-002-shipping-escalation` dropped from **0.8036
   to 0.5714** ($-0.2321$, a 23.2 percentage point drop).
3. **The empty prompt remains unbested:** Across all 392 items, having no prompt
   at all (`off`: **0.8673**) outperformed original SkillOpt (**0.8112**),
   ablated SkillOpt (**0.8367**), and ablated GEPA (**0.8597**).
