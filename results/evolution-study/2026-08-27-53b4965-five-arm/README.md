# Five arms on a frozen holdout: does an evolved skill beat a placebo?

**Answer key:** `datasets/templates/` v1, ten reliability templates with ground
truth computed by the generator. Corpus identity is the fingerprint rather than
a label-set version: unseen `a9889750c762`, seen `bb95bfe63c1b`, both recorded
in `run.json`.

Prediction: [`notebook/2026-08-27-prediction-the-five-arm-study-before-the-first-call.md`](../../../notebook/2026-08-27-prediction-the-five-arm-study-before-the-first-call.md),
first committed at `e882eff`, with an amendment appended mid-run after 143 of
4,368 calls and before any comparison was read.

Write-up: [`notebook/2026-08-27-two-engines-evolved-a-skill-and-neither-one-beat-a-placebo.md`](../../../notebook/2026-08-27-two-engines-evolved-a-skill-and-neither-one-beat-a-placebo.md)

## What was run

4,368 calls on `ollama/qwen3:1.7b`, Ollama's native `/api/chat` at a 16,384
context window, output capped at 4,096, temperature 0, `keep_alive: 60m`. Local,
notional cost $0.

**Two commits name this run.** `run.json` records `git_sha 98229a1`, which is the
commit the calls were actually made at and is left as it was written. The branch
was then rebased onto `main`, which replayed that commit as `53b4965` with the
same study code, and the directory carries the second because that is the one a
reader can check the prediction against. The prediction's first commit,
`e882eff`, is an ancestor of `53b4965`.

Five arms, all through `solvers/arms.build_arm`, told
apart by `candidate_sha`:

| arm | body |
| --- | --- |
| `off` | none |
| `on` | `skills/decision-making/SKILL.md` |
| `placebo` | `skills/decision-making/placebo.md`, word-count- and structure-matched |
| `gepa` | GEPA's seven-template winner, `candidate_sha 54f99040...`; body never committed and unrecoverable |
| `skillopt` | SkillOpt's seven-template winner, `candidate_sha 80d7187a...`; same |

Templates were split by `sha256("evolution-study-v1:<template_id>")`. Both
searches saw only the seven trained templates; both test sets were minted after
both winners were frozen, from seeds at or above 10,000, which
`assert_evolvable` refuses to hand a search.

## What was computed

Per arm, accuracy is the count `scorers.answer.score_item` marks correct over
all items in the set, one call per item. Each comparison is McNemar's exact test
on the discordant pairs between that arm and `placebo`, item-matched, one-sided
in the direction of the arm helping, with Holm applied across the registered
family of three. The two sets are analysed separately and never pooled. `off` is
reported outside the family: it answers whether any document helps, which is not
the question the family asks.

## Results

**Unseen: three held-out templates, four holdout seeds, 336 items.**

| arm | accuracy | effect vs placebo | wins / losses | p | Holm |
| --- | --- | --- | --- | --- | --- |
| `skillopt` | 0.7054 | +0.0179 | 49 / 43 | 0.3012 | 0.9036 |
| `placebo` | 0.6875 | | | | |
| `off` | 0.6845 | | | | |
| `on` | 0.6786 | -0.0089 | 46 / 49 | 0.6591 | 1.0000 |
| `gepa` | 0.6280 | -0.0595 | 49 / 69 | 0.9736 | 1.0000 |

**Seen: seven trained templates, two holdout seeds, 392 items.**

| arm | accuracy | effect vs placebo | wins / losses | p | Holm |
| --- | --- | --- | --- | --- | --- |
| `skillopt` | 0.8087 | +0.0408 | 42 / 26 | 0.0341 | 0.1022 |
| `gepa` | 0.7730 | +0.0051 | 37 / 35 | 0.4531 | 0.9063 |
| `placebo` | 0.7679 | | | | |
| `on` | 0.7398 | -0.0281 | 26 / 37 | 0.9350 | 0.9350 |
| `off` | 0.7168 | | | | |

**No arm rejects on either set.** SkillOpt's winner is the study's best showing
at +0.041 on the seen set, raw p = 0.034, which Holm takes to 0.102.

## Controls

- **A/A.** The placebo was scored a second time over all 728 items into
  `records-aa.jsonl`, a separate checkpoint so resume could not skip the pass
  and report perfect agreement by construction. **728 of 728 items came back
  identical**, both passes at 0.7308, p = 1.000. That bounds the venue drift
  this design is exposed to; it does not license reading every difference in
  the tables above as prompt-caused, because the pass repeats one arm and the
  arms ran in blocks.
- **Falsifier.** `off` returns 0.702 over the 728 items, so a non-zero score was
  reachable in every arm and the scorer reads the same object in each.
- **Residency.** Pinned at 60 minutes, sent on every request rather than
  assumed, after a probe found two items answering deterministically to whether
  the model had just been loaded. It is not written into `run.json`, so a
  replicator reads it from the provider source.

## What this does not claim

`arenas.py` registers `ollama` as `dev`, and a `dev` run emits **no verdict**.
Nothing here moves `SCORECARD.md`. The result is scoped to one 1.7B model under
these controls.

That limit was measured rather than assumed: every one of the seven NVIDIA
Build models in `nvbuild-ceiling-screen.json` solves the corpus with an empty
prompt, the weakest at 0.933 against 0.702 for this study's target, so no
NVIDIA Build venue can host this study as the corpus currently stands. The
other screen-tier backends, `claude_code` and `antigravity`, were not screened. An eighth model returned inside
budget and is recorded in the notebook entry but not in the file; we report the
file's count, because a record edited to match a write-up is not a record. The
three registered models that never returned are larger than models already
answering at 1.000, which is an expectation rather than a reading.
[`notebook/2026-08-27-the-verdict-tier-is-reachable-and-the-corpus-is-not-hard-enough-for-it.md`](../../../notebook/2026-08-27-the-verdict-tier-is-reachable-and-the-corpus-is-not-hard-enough-for-it.md)

The design also has a confound the write-up states in full: `placebo` helps on
the seen set and does nothing on the unseen set, and `placebo` has no training
history, so the two sets differ in ways that are not about being held out.

## Files

One file per arm, 728 records each, both item sets together. Which set a record
belongs to is its `seed`, and `run.json` lists the seeds for each.

- `records-off.jsonl`, `records-on.jsonl`, `records-placebo.jsonl`,
  `records-gepa.jsonl`, `records-skillopt.jsonl` — 3,640 records in total
- `records-aa.jsonl` — 728 records, the placebo's second pass, in its own
  checkpoint so resume could not skip it
- `analysis.json` — per-set accuracy, the comparisons, the A/A
- `run.json` — the manifest: arms, shas, seeds, templates, corpus fingerprints
- `nvbuild-ceiling-screen.json` — the no-skill screen behind the verdict-tier
  limit above, one row per NVIDIA Build model, accuracy over answered calls

Every number in the tables above recomputes from these files through
`decision_evals.evolution.study.analyse`.

## Corrections

Appended 2026-08-31, during the pre-submission audit of `paper/`. The text above
was corrected in place and each change is recorded here, because a provenance
artifact that quietly disagrees with the records beside it is worse than one
that says where it was wrong.

- The prediction's first commit read `0b379af`, which is not a valid object.
  It is `e882eff`, which this file already gave correctly sixteen lines later.
- Three surfaces said the placebo is matched on **tokens**. Nothing in this
  repository has ever counted tokens: `check_placebo_match` compares word counts
  within 15%. `docs/PROTOCOL.md` carries the same correction.
- The A/A paragraph said every difference between arms is a difference the
  prompts caused. The A/A bounds the venue confound and does not remove it: the
  pass repeats one arm, and the arms ran in blocks.
- Residency was described as "recorded per pass". It is sent on every request
  and is not in `run.json`. `docs/HARNESS_DISCLOSURE.md` carries the same
  correction.
- The screen was described as eight of eleven reachable models.
  `nvbuild-ceiling-screen.json` holds seven rows; the eighth is in the notebook
  entry and not in the committed file.

Appended 2026-08-31, second pass.

- The arm table gave both evolved winners as "frozen winner of
  `results/evolution/2026-08-27-...`". Neither directory exists, neither sha
  resolves, and `.gitignore:79` excludes `results/evolution/`, so neither ever
  could have been committed. The cells now give the content hash, which is what
  is actually on record.
- The screen paragraph said no screen-tier venue can host this study. The screen
  covered NVIDIA Build only; `claude_code` and `antigravity` are registered at
  that tier and were never screened. Scoped.
