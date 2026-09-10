# 2026-09-10 — The second evolution study: two passes, seven unseen, and neither winner beats a placebo

Registered in
[the prediction entry](2026-09-02-prediction-the-five-arm-study-run-again-with-the-bodies-kept.md)
with five methodological defects of the first run corrected:
both winning bodies committed and tracked, seven held-out templates rather than
three, each evolved winner paired with a structure- and word-count-matched placebo,
two interleaved passes across chunks of eight items, and Qwen's `/think` control token
stripped before scoring.

14,700 calls on `ollama/qwen3:1.7b` through Ollama's native `/api/chat` at a
16,384 context window, output capped at 4,096, temperature 0, `keep_alive: 60m`.
Local, notional cost \$0. Every call completed and accounted for.

## The result

At the pre-registered bar — Holm-adjusted item-unit q < 0.05 **and** template-unit
cluster sign-flip p < 0.0167 — **neither evolved winner beat its matched placebo
on either set.**

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

## The dual bar in action

The pre-registration required both the item-unit test and the cluster sign-flip
test to reject. This run is why:

1. **SkillOpt on unseen scenarios:** At the item unit, SkillOpt appears to score a
   decisive victory (+0.0918, 115 wins to 61 losses, Holm q = 0.000086). But at
   the template unit, `cluster_sign_flip` yields p = 0.0313, which fails the
   registered threshold of 0.0167. Its gains are concentrated in specific
   template structures rather than demonstrating uniform generalization.
2. **GEPA on seen scenarios:** At the item unit, GEPA clears Holm (q = 0.0280 < 0.05,
   43 wins to 23 losses). But at the template unit, p = 0.0781. It does not clear
   the cluster bar.

Both arms would have claimed significance under an unclustered item test. Neither
survives the template-unit clustering.

## The predictions, scored

1. **Both searches produce a winner that beats the seed skill on the 21-item validation pool.**
   **Met.** Both searches achieved score 1.0 on their validation sets.
2. **Both winners carry training content.**
   **Met.** Both winners committed to disk exhibit explicit training item content:
   - GEPA's winner (`f7589ca4`) quotes specific ticket identifiers (`ticket 40078`),
     warranty clauses (`Alder covers this model for 23 months`), and elapsed months (`22 months`)
     verbatim from training items.
   - SkillOpt's winner (`7a2e2784`) incorporates hardcoded worked examples with exact
     numerical cutoffs from training templates: Warranty (23/22 months), Shipping (4/10 days),
     and Loan Review (threshold 665, score 737), plus cache-tier scaling clauses.
3. **Neither winner beats its matched placebo on the unseen set at the registered bar.**
   **Met.** GEPA is -0.0561 behind its placebo (Holm q = 1.0000). SkillOpt achieves
   Holm q = 0.000086 at the item level but fails the template cluster sign-flip bar
   (p = 0.0313 > 0.0167).
4. **Neither winner beats its matched placebo on the seen set at the registered bar.**
   **Met.** SkillOpt achieves +0.0026 (Holm q = 1.0000). GEPA achieves Holm q = 0.0280
   at the item level but fails the cluster sign-flip test (p = 0.0781 > 0.0167).
5. **The per-winner placebos sit within 0.03 of the shared placebo on both sets.**
   **Falsified on one arm.** On the unseen set, `placebo-gepa` scored 0.7534 against
   `placebo` at 0.7143 (+0.0391 difference, exceeding the 0.03 band). On the seen
   set, both per-winner placebos were within 0.03 of the shared placebo (+0.0153 for
   `placebo-gepa`, +0.0026 for `placebo-skillopt`).
6. **`placebo` against `off` is within 0.03 on both sets.**
   **Falsified on both sets.** An empty prompt (`off`) outperformed the placebo by
   more than 0.03 on both sets:
   - Unseen: `off` 0.7500 vs `placebo` 0.7143 (-0.0357).
   - Seen: `off` 0.8673 vs `placebo` 0.8061 (-0.0612).
   Prompting with decision procedures or placebo text degraded baseline performance.
7. **Pass agreement is at least 0.98 identical on every arm, and the A/A agrees at the same rate.**
   **Met.** Agreement between pass 1 and pass 2 was **100% identical** across all 7 arms
   (588/588 unseen, 392/392 seen, p = 1.000). The A/A on the shared placebo was likewise
   **980 of 980 identical** (p = 1.000).
8. **The control token appears on fewer than 5% of readings and every one of them parses.**
   **Met.** A trailing `/think` or `/no_think` appeared in 48 of 6,860 calls (0.70%),
   and 48 of 48 parsed cleanly without error.

## The finding on prompting cost

Across both the unseen and seen test sets, having no prompt at all (`off`) scored
higher than the human-written skill (`on`):
- Unseen: `off` 0.7500 vs `on` 0.6803 (-0.0697 difference).
- Seen: `off` 0.8673 vs `on` 0.8061 (-0.0612 difference).

On this model (`ollama/qwen3:1.7b`), adding markdown procedures increased verbosity
and runaway generations (89 truncated calls in `on` vs 26 in `off`), degrading overall
accuracy. When evaluated strictly against matched placebos that control for document
length and structural formatting, prompt optimization yielded no statistically
generalizable gain across task templates.
