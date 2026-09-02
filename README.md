<div align="center">

<picture class="gh-only">
  <source media="(prefers-color-scheme: dark)" srcset="site/public/lockup-dark.png">
  <img src="site/public/lockup-light.png" alt="decision-making-skills" width="440">
</picture>

[![Check](https://github.com/AngelCampa1/decision-making-skills/actions/workflows/check.yml/badge.svg)](https://github.com/AngelCampa1/decision-making-skills/actions/workflows/check.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange.svg)](docs/STATUS.md)
[![Verdict](https://img.shields.io/badge/verdict-UNTESTED-lightgrey.svg)](SCORECARD.md)

</div>

**Audience:** the cold reader.

An evaluation harness for agent skills, the `SKILL.md` files a coding agent
loads, with pre-registration enforced by git ancestry and a placebo arm, and
the record of what it found: its own decision corpus could not fail.

- **There was nothing to measure.** Every single-prompt decision scenario
  authored here with an answer key was solved by the model without the skill,
  the scalar scenarios at Youden's J = 1.000 over 99 blind readings
  ([`docs/STATUS.md`](docs/STATUS.md)).
- **The optimisers memorised, and neither beat a placebo.** Two automated
  skill-evolution engines each produced a winner carrying constants lifted from
  single training items, the first score the lineage recorded for one winner
  was over three items, and neither beat a word-count-matched placebo over
  728 items after Holm
  ([the run](results/evolution-study/2026-08-27-53b4965-five-arm/README.md)).
- **The harness caught <!-- de:fact broken-measurements -->eleven<!-- /de:fact -->
  of its own measurements broken before they became results**, and the guard
  each one forced is recorded beside it
  ([`docs/STATUS.md`](docs/STATUS.md)).

[**The write-up**](docs/WHAT_WE_FOUND.md) ·
[Architecture](docs/ARCHITECTURE.md) ·
[v1.0.0 release](https://github.com/AngelCampa1/decision-making-skills/releases/tag/v1.0.0)

Twenty runs are published, raw transcripts included, indexed in
[`docs/RUN_INDEX.md`](docs/RUN_INDEX.md); two predate the provenance rule and
are baselined there. No skill here carries a verdict.
The skills ship as experimental, the finding is the product, and
[`SCORECARD.md`](SCORECARD.md) says what would change that.

## What broke, and what now refuses it

Every rule in this repository exists because the failure it prevents already
happened here. The dated record behind each row is a section of
[`docs/WHY_THESE_RULES.md`](docs/WHY_THESE_RULES.md).

| What broke | What now refuses it |
| --- | --- |
| One turn moved from the positives to the negatives and recall rose 3 to 5 points on four of the five arms on disk, with no call re-made ([record](docs/WHY_THESE_RULES.md#the-answer-key-move-that-earned-five-points)) | `label_versions_comparable` refuses a comparison across answer-key versions, and every record carries `set_version` |
| A module with a 100% coverage floor was called by nothing, twice, and a tested function nothing invoked made it three ([record](docs/WHY_THESE_RULES.md#why-a-coverage-floor-is-not-a-wiring-check)) | The `integrity wiring` step refuses a floored module no entry point can reach |
| Answer key v5 was 78% adjudicated for a day and the gate stayed green ([record](docs/WHY_THESE_RULES.md#why-an-unadjudicated-answer-key-is-refused)) | The `label adjudication` step refuses a trigger set carrying an item with no three-judge blind record |
| The README told readers to run two commands that did not exist and advertised a directory that did not either ([record](docs/WHY_THESE_RULES.md#why-documentation-is-gated-mechanically)) | The `documentation` step refuses a command, path or component a document names and the repository does not have |
| `main`'s tip imported a module that was never committed, and every local gate passed because the file was on disk ([record](docs/WHY_THESE_RULES.md#why-the-gate-runs-in-ci-too)) | The same gate runs in CI on a clean checkout |
| Four false enumerations shipped in one document with every path in them correct ([record](docs/WHY_THESE_RULES.md#documents-stopped-writing-what-the-repository-already-knows)) | `de sync` writes the tables from live objects and the `generated regions` step refuses one that is stale |
| The drift sweep's own bullet said "Nothing checks this" ([record](docs/WHY_THESE_RULES.md#why-the-drift-sweep-has-a-worklist)) | The `document drift` step refuses a living document more than ten commits past its last recorded reading |
| A dollar cap on a venue that bills nothing could never fire ([record](docs/WHY_THESE_RULES.md#why-there-are-no-dollars)) | `BudgetLedger` refuses to be built for a free venue with neither a call cap nor a clock cap |

## How this was built

The maintainer wrote the contract and reviewed what came back. AI coding agents
did the rest, running for hours or days at a time under
[`docs/AUTONOMOUS_WORK_ORDER.md`](docs/AUTONOMOUS_WORK_ORDER.md), which carries
the five standing rules, the sub-agent and adversarial-review method, and the
landing sequence, with the incident behind each rule in
[`docs/WHY_THESE_RULES.md`](docs/WHY_THESE_RULES.md). The agents' failures are
in the record beside the model's:

- [The gate had never run on a clean clone](notebook/2026-08-19-the-gate-had-never-run-on-a-clean-clone.md),
  and `main` did not import there.
- [Two worktrees deleted](notebook/2026-08-19-two-worktrees-deleted-by-an-rm-that-was-in-the-wrong-directory.md)
  by an `rm` whose shell was not where the agent believed it was.
- [A watcher polled for a file for seven and a half hours](notebook/2026-08-27-gepa-found-the-answer-key-and-wrote-it-into-the-skill.md)
  after the crash that guaranteed it would never appear.
- [`main` was red in CI for three commits](notebook/2026-08-28-main-was-red-in-ci-for-three-commits-and-the-local-gate-could-not-see-it.md)
  while every local gate was green.
- [Fourteen truth cycles and not one prose review](notebook/2026-08-31-fourteen-truth-cycles-and-not-one-prose-review-is-how-a-paper-gets-this-way.md)
  produced a paper that was locally true and unreadable.

## Use the harness as a library

`decision_evals` installs with `uv sync --group dev`. The refusals are plain
functions, and the arithmetic that should run before a study runs without one.

```python
"""Four refusals and three statistics, using the harness as a library."""

from decision_evals.budget import BudgetError, BudgetLedger
from decision_evals.prereg import (
    Preregistration,
    PreregistrationError,
    RepoState,
    assert_runnable,
    sha256_text,
)
from decision_evals.stats import cluster_sign_flip, mcnemar_exact, minimum_detectable_effect
from decision_evals.trigger_arms import label_versions_comparable

skill, analysis = "# a skill body\n", "def analyse(records): ...\n"
prereg = Preregistration(
    skill="decision-making",
    version=1,
    hypothesis="the skill beats a placebo",
    primary_metric="accuracy",
    n_items=336,
    minimum_detectable_effect=0.081,
    alpha=0.05,
    guards=["placebo"],
    stopping_rule="fixed N, no interim look",
    budget_usd=10.0,
    skill_sha256=sha256_text(skill),
    analysis_script_sha256=sha256_text(analysis),
)
repo = RepoState(committed_and_clean=True, is_ancestor_of_head=False, precedes_results=True)
try:
    assert_runnable(
        prereg,
        repo=repo,
        skill_body=skill,
        analysis_source=analysis,
        baseline_accuracy=0.55,
        projected_cost_usd=1.0,
    )
except PreregistrationError as refusal:
    print("prereg:", refusal)
try:
    BudgetLedger(limit_usd=5.0, bills=False)  # a local model: total_cost_usd reads 0
except BudgetError as refusal:
    print("budget:", refusal)
control = [1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0]
treatment = [1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0]
print("mcnemar p:", round(mcnemar_exact(control, treatment).p_value, 4))
print(
    "mde at design effect 2:",
    round(minimum_detectable_effect(336, 0.25, design_effect=2.0).effect, 4),
)
flip = cluster_sign_flip(
    [t - c for c, t in zip(control, treatment)], ["a"] * 4 + ["b"] * 4 + ["c"] * 4
)
print("sign-flip floor with 3 clusters:", flip.floor, "could reject:", flip.could_reject)
print("versions:", label_versions_comparable([{"set_version": 4}], [{"set_version": 6}]))
```

Run as written it prints two refusals, a McNemar p of 0.0625 on twelve pairs,
a minimum detectable effect of 0.0953 for 336 pairs at a design effect of 2,
a sign-test floor of 0.125 that `could_reject` reads as `False`, and the
sentence that refuses to compare answer-key version 4 against version 6.

## The skill

One skill, `decision-making`, nine markdown files and no runtime. Its router
asks what is *hard* about the choice and reads one of six procedures:
[`ledger.md`](skills/decision-making/ledger.md) when a pile of context arrived
and it is unclear which fact decides it, [`fit.md`](skills/decision-making/fit.md)
when the advice may be generically right and wrong for this person,
[`cascade.md`](skills/decision-making/cascade.md) when the worry is what an
action starts or spends, [`timing.md`](skills/decision-making/timing.md) when
the question is when, [`council.md`](skills/decision-making/council.md) when
several positions are each defensible, and
[`hinge.md`](skills/decision-making/hinge.md) when a missing fact may or may
not matter. Two more files are control arms:
[`placebo.md`](skills/decision-making/placebo.md) is matched to the router and
[`placebo-council.md`](skills/decision-making/placebo-council.md) to
`council.md`.

The description in `SKILL.md` is the measured artefact, and it changes only as
a new arm with an entry in [`docs/DECISIONS.md`](docs/DECISIONS.md). The skills
carry only the six portable frontmatter fields of the
[Agent Skills standard](https://agentskills.io), so they need no conversion:

```bash
# Cross-tool: Codex, Cursor, Copilot, Gemini CLI, Cline, Amp, OpenCode
cp -r .agents/skills/* ~/.agents/skills/
# Claude Code, project-scoped
cp -r skills/* .claude/skills/
```

The Claude Code plugin ships nothing until a confirmation run gives a skill a
verdict. Copying from `skills/` is the way to use it today.

## What's actually here

| Component | Purpose |
| --- | --- |
| `skills/` | The skills, authored to the [Agent Skills](https://agentskills.io) six-field standard so they work in Claude Code, Codex, Cursor, Copilot, Gemini CLI, Cline, Amp and OpenCode without conversion. Mirrored byte-for-byte by `de mirror` |
| `plugin/` | The Claude Code plugin. A skill is copied here once a confirmation run gives it a verdict |
| `evals/` | `decision_evals`, the evaluation harness. Paired experiments, exact tests, cluster-aware resampling, and chance-corrected inter-rater reliability |
| `datasets/` | The answer key: parameterised scenario templates with *computed* ground truth, the trigger corpus, and the SHA-256 lockfile for the third-party corpus `de fetch` downloads |
| `preregistration/` | The contract a confirmation run is bound to, one file per skill per version: hypothesis, primary metric, item count, minimum detectable effect, alpha, guards, stopping rule, and a SHA-256 lock on both the skill body and the analysis code. `de confirm` refuses a run that does not match |
| `results/` | Published run records: raw transcripts and a README per run |
| `notebook/` | Append-only research log. Predictions go in *before* runs |
| `docs/` | Protocol, status, the research programme, related work, limitations, and what was rejected. Start at [`docs/README.md`](docs/README.md), or [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the pieces fit |
| `paper/` | The write-up, in LaTeX: *Do Automated Skill Optimisers Survive a Placebo Control?* Complete, and unsubmitted. Every number about our own runs is written into it by `de figures` from `results/`, never typed. What is still open, including three boxes that need someone outside this repository, is [`paper/CHECKLIST.md`](paper/CHECKLIST.md). CC-BY-4.0, unlike the rest of the tree |
| `scripts/` | Standalone analysis and runners, including `run_triggers.py`, the script behind every trigger call on record |
| `tests/` | Unit, integration, property and golden tests |
| `site/` | The website. It renders the markdown already in this repository in place, so no second copy of a document can disagree with the first |

## Development

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --group dev
uv run de check
```

`de check` is the whole gate: lint, types, tests, coverage floors and the
repository-integrity checks. It makes no model calls and is fully
deterministic, so the same command runs unchanged in
[`.github/workflows/check.yml`](.github/workflows/check.yml) on every push and
pull request, bound to `pre-commit` as a fast subset and to `pre-push` in full.
Local tells you the working tree passes; CI tells you the *commit* passes, and
the first time the two were compared they disagreed in four places. The steps,
in order, written by `de sync` from `gate_steps()`:

<!-- de:generated de-check-steps -->
| # | Step | `--fast` |
| --- | --- | --- |
| 1 | git identity | runs |
| 2 | ruff check | runs |
| 3 | ruff format | runs |
| 4 | mypy | runs |
| 5 | mypy (linux) | runs |
| 6 | skill lint | runs |
| 7 | trigger sets | runs |
| 8 | tailoring corpus | runs |
| 9 | plugin manifests | runs |
| 10 | citations | runs |
| 11 | run provenance | runs |
| 12 | integrity wiring | runs |
| 13 | decision register | runs |
| 14 | label corrections | runs |
| 15 | label adjudication | runs |
| 16 | checkpoint label versions | runs |
| 17 | documentation | runs |
| 18 | published claims | runs |
| 19 | generated regions | runs |
| 20 | site | skipped |
| 21 | document drift | skipped |
| 22 | pytest | skipped |
| 23 | coverage floors | skipped |
<!-- /de:generated -->

Merging to `main` publishes the site through
[`.github/workflows/deploy-site.yml`](.github/workflows/deploy-site.yml).
Nothing on a developer machine can publish. `de check` is offline and cannot
see the live site, so that question is answered on demand: `uv run de deployed`
exits 0 when the live site is a build of the current `main`, 1 when it is
behind, and 2 when it could not tell, which is deliberately distinct from 0.

Editing any document the site renders makes the published build stale, so the
loop is edit, rebuild, commit both:

```bash
uv run de sync && uv run de site
```

`de site` needs Node and npm on `PATH`, because the site is an Astro project.
`de sync` rewrites the tables the documents derive from the repository, and
`de drift` lists the documents whose subject has moved since anyone recorded
reading them. The rest: `de index` regenerates
[`docs/RUN_INDEX.md`](docs/RUN_INDEX.md), `de mirror` regenerates the cross-tool
skill copies, `de lint` checks skill frontmatter and the promotion gate,
`de power` prints a minimum-detectable-effect table, `de rescore` re-grades an
existing checkpoint against a newer answer key without re-making a single call,
and `de fetch` downloads the hash-pinned third-party corpora.

> **Note:** if `uv` was installed with `pip install uv`, its executable may not
> be on `PATH`. On Windows it lands in
> `%APPDATA%\Python\Python313\Scripts`. Add that directory to `PATH`, or invoke
> it as `python -m uv`.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The short version: run `de check`
before believing anything works, put predictions in the notebook before runs,
and never edit a notebook entry after the fact. Append a correction instead.
Prose goes through the standard in [`docs/VOICE.md`](docs/VOICE.md).

Think a published number is wrong? [Open a dispute against
it](.github/ISSUE_TEMPLATE/dispute-a-result.md). The template is pre-populated
with the specific ways a measurement here has already failed, so pointing at
the right one is most of the report.

## License

Apache-2.0. See [LICENSE](LICENSE).
