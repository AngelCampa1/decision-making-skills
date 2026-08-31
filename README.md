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

A set of decision procedures an AI coding agent can load on demand, and the evaluation harness
built to find out whether they actually work.

Two things live here.

**An agent skill for decisions.** It works out what is *hard* about the choice
before it answers, then runs one of six procedures built for that specific
difficulty. Paste in the whole thread and ask what to do about Tuesday:

```text
LEDGER
  1. the Lisbon forecast — decides what to pack
  2. the Tuesday flight — decides when

SET ASIDE
  - the rain in Paraguay — your trip does not touch it

THEREFORE
  pack for Lisbon
```

That is `ledger.md`, the one for when too much context arrived and you cannot
see which fact decides it. The other five handle advice that is generically
right and may be wrong for you; consequences you did not price; timing; several
positions that are each defensible; and a missing fact that may or may not
matter.

**And `decision_evals`, the harness built to find out whether any of that
helps.** It relabels its own answer key with a blind panel of three model
instances and reports their agreement chance-corrected. It stamps an answer-key
version into every record and refuses, in code, to compare arms across a version
boundary. It pins MCP empty at every call, because a connector present in one
arm and absent in another is a confound. And it refuses to publish a result
whose prediction cannot be shown by git ancestry to predate its data. Nineteen
runs are published under those rules, raw transcripts included.

What they have found so far is about *firing*: whether a skill switches on when
it should. Rewriting the skill's description five different ways changed which
mistakes it made, trading missed decisions against unwanted interruptions, and
never changed how well it told the two apart. Then the harness was pointed at
its own test set, and a rule as crude as *fire if the question is long* scored
close to the real thing. That finding retired the test set and paid for the
rebuilt one every result since has run on.

One of those runs was aimed at this repository's own argument. A published
result says that a large skill library crowds out the right skill, and this
README used to cite it as the reason the skill ships as one entry instead of
four. The run found nothing of the kind at four entries, so the citation was
retired from the claim it was supporting and the four-entry arm turned out to
route better.

No skill here carries a verdict yet, so [`SCORECARD.md`](SCORECARD.md) is empty
and [`docs/STATUS.md`](docs/STATUS.md) is the ledger of every run on record.
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) draws how the skill, the harness,
the datasets and the gate fit together.
The skill is free, installs in one line, and comes out again in one line.

## The skill

One skill, `decision-making`. Its router asks a single question, *what is hard
here?*, and the answer selects one of six procedures. It reads only that one.

| What is hard | Procedure | What it produces |
| --- | --- | --- |
| A pile of context arrived and it is unclear which fact decides it | [`ledger.md`](skills/decision-making/ledger.md) | what bears on it, what was set aside, and why |
| The advice may be generically right and wrong for this person | [`fit.md`](skills/decision-making/fit.md) | the generic answer, and the facts that would overturn it |
| The action looks fine and the worry is what it starts, or what it spends | [`cascade.md`](skills/decision-making/cascade.md) | the chain, what it forecloses, and the order |
| The direction is settled and the question is when | [`timing.md`](skills/decision-making/timing.md) | the undo price, the real deadline, what waiting buys |
| Several positions are each defensible, and whichever was argued first has the advantage | [`council.md`](skills/decision-making/council.md) | the case for each, argued fairly, and which one survives |
| Something needed to answer is missing, and it is unclear whether asking for it is worth the wait | [`hinge.md`](skills/decision-making/hinge.md) | which gaps would change the answer, and the answer now or the one question to ask |

The six exist because agents fail at decisions in separable ways. Everything
retrieved gets weighted roughly equally, so an agent told it is raining in
Paraguay while planning a trip to Lisbon will suggest a raincoat. Stated
confidence drifts from observed frequency. A one-way door and a trivially
reversible choice draw the same deliberation budget.

Where more than one applies they run in the order ledger, fit, cascade, timing,
because each supplies an input to the next. `council.md` and `hinge.md` sit
outside that chain and each runs alone. Two more files are control arms:
[`placebo.md`](skills/decision-making/placebo.md) is matched to the router and
[`placebo-council.md`](skills/decision-making/placebo-council.md) to
`council.md`. They ship alongside because a skill that only beats nothing has
not been measured against the thing that would fake it.

### Install

The skills carry only the six portable frontmatter fields of the
[Agent Skills standard](https://agentskills.io), so they need no conversion.

```bash
# Cross-tool: Codex, Cursor, Copilot, Gemini CLI, Cline, Amp, OpenCode
cp -r .agents/skills/* ~/.agents/skills/
```

```bash
# Claude Code, project-scoped
cp -r skills/* .claude/skills/
```

There is also a Claude Code plugin, and it currently ships nothing. A skill is
copied into `plugin/skills/` only once a confirmation run gives it a verdict.
Copying from `skills/` is the way to use this today.

## How it works

`decision_evals` does four things: it holds the answer key, it runs arms against
it, it scores them, and it refuses to publish what it cannot trace.

**The answer key.** [`datasets/`](datasets/) is the golden dataset:
parameterised scenario templates with *computed* ground truth, plus third-party
corpora pinned by SHA-256 and downloaded by `de fetch`. The key carries a
version stamped into every record, and `label_versions_comparable` refuses a
comparison that spans a version boundary. That guard exists because one correct
label move once raised recall on every arm on disk without a single call being
re-made.

**Relabelling it, blind.** The maintainer's labels do not get the last word on
themselves. [`scripts/adjudicate.py`](scripts/adjudicate.py) runs a blind
three-judge panel on every turn:

- Three independent model instances judge each turn, and none sees the
  maintainer's label or the other two.
- A verdict needs a majority, checked against a kill threshold fixed before
  the run.
- Agreement is reported chance-corrected, with Fleiss' kappa and
  Krippendorff's alpha beside raw agreement, because on this class balance
  two judges that have learned nothing still agree most of the time.
- Primary metrics stay deterministic. A judge never produces one.

**The arms.** A confirmation run is a within-item comparison with four arms on
the same items: **off** (the ablation), **on**, **placebo** (token- and
structure-matched filler), and **cot** (plain "think step by step"). The placebo
is what makes the design worth running. A skill that beats *off* and ties
*placebo* is a length effect, and a skill that ties *cot* is an expensive way to
say "think". [`scripts/run_triggers.py`](scripts/run_triggers.py) is the runner
behind every trigger call on record, and it pins MCP empty at every call with
`--strict-mcp-config`. The full lockdown is in
[`docs/HARNESS_DISCLOSURE.md`](docs/HARNESS_DISCLOSURE.md).

**The scorers.** Firing accuracy is the selection question, the same shape as
tool selection in a function-calling evaluation, and
[`evals/src/decision_evals/scorers/bfcl.py`](evals/src/decision_evals/scorers/bfcl.py)
scores a call the way BFCL's checker does, matching name and arguments after a
JSON parse. Calibration goes through the Murphy decomposition, so a skill that
improves Brier by hedging every forecast toward the base rate is caught by the
resolution term. The statistics are exact and resampling-based instead of
CLT-based, because at these item counts the normal approximation is unreliable,
and the resampling unit is the template, since items from one template are
correlated.

**The record each run leaves.**
[`evals/src/decision_evals/telemetry.py`](evals/src/decision_evals/telemetry.py)
pins the GenAI OpenTelemetry semantic-convention attribute names, adopted as
names without taking the dependency, so a record written here reads in a tool
that has never seen this repository.
[`evals/src/decision_evals/orchestrator.py`](evals/src/decision_evals/orchestrator.py)
runs a scripted fan-out of sub-agents with a per-node record. Every published
run ships its raw transcripts under [`results/`](results/) and is indexed with
its answer key and its prediction in
[`docs/RUN_INDEX.md`](docs/RUN_INDEX.md).

**Pre-registration.** A dated prediction goes into [`notebook/`](notebook/)
before the run. `de check` enforces it and refuses a published run whose README
does not name a prediction whose first commit is a git ancestor of the run's
commit. Two runs predate the rule and are baselined by name in
[`results/provenance-baseline.txt`](results/provenance-baseline.txt), a list
that may only shrink.

[`docs/METHODS.md`](docs/METHODS.md) is the full account: nine sections, each
naming the technique, the failure it defends against, the code that implements
it, and whether it has actually run.

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

## Where the evidence stands

Every caveat, in one place.

The verdict badge above is not a formality: `decision-making` and all six
procedures are `UNTESTED` and ship as `experimental`. [`SCORECARD.md`](SCORECARD.md)
is the file that changes that, and it is empty.

Every trigger number on record measures whether a skill *fires*, which is
upstream of whether it helps. Firing decides whether a skill is worth having
installed at all, and it is the question this instrument was built for. The one
venue built to ask the other question closed instead: Family A, the scalar
triplet behind `ledger`, `timing` and `fit`, hit an unaided ceiling of J = 1.000
over 99 blind readings, so there was no headroom left for a procedure to add.

**One run has since asked the downstream question.** The five-arm study of
2026-08-27 put the shipped skill against an empty prompt and a token- and
structure-matched placebo over 728 items. It scored below the placebo on both
item sets, and neither difference is significant. That run carries no verdict:
its target is a 1.7B local model, `arenas.py` registers that tier as `dev`, and
a `dev` run moves nothing on [`SCORECARD.md`](SCORECARD.md). So the answer
exists, and it is scoped to one small model.

Every trigger call on record compares variants of the skill's *description*, and
none of them used the placebo or `cot` arm. The `confirm` arena has still never
run, and it is the arena a verdict comes from.

Two of the twenty published runs measure something other than a skill. One is
void, refused on parse rate before any prediction was scored, which is the first
registered void condition here to fire on its own. The other is the five-arm
study, which is about the tooling that writes skills.

The description arms measure the shipped description in a proxy venue. N10 ran
the shipped six-procedure wording against five variants on answer key v6, all of
it through one isolated call per case. Nothing on record says how that
description behaves in situ, where it sits among other skills with the model
mid-task: N9 was the run that asked and it is void. That qualifies every finding
above and needs a new arm and a new pre-registration to close.

The corpus behind the earlier results was largely solvable without a model, a
finding this harness produced about its own instrument. It scopes to answer-key
version 2 and the runs above it. The rebuild at version 4 is far harder to
shortcut, the two keys are never mixed, and
[`SCORECARD.md`](SCORECARD.md) carries both figures with the arms measured
against them. The live key has since moved to version 6, by addition and by
rewriting three asks; no shortcut figure has been computed against it.

The hash-locked pre-registration refusal is built, tested, and has fired twice
with no confirmation run behind it. Both firings were on refactoring: the lock
pins the whole of `scripts/run_triggers.py`, so an ordinary harness commit
invalidates it, and the remedy each time was a new version rather than an edited
hash. `de confirm` reaches the module from the console script, so
`[tool.decision-evals.unwired]` is now empty. What has never run is the
`confirm` arena itself, which still refuses for want of a holdout.

**Landed 2026-08-27: neither skill-evolution engine beat a placebo.** Two
automated prompt optimizers, GEPA and SkillOpt, each evolved a skill on a
matched budget. Both winners had written the answer key into their own bodies:
one transcribed a training template's rule, the other appended worked examples
whose numbers trace back to the training pool. Tested against a placebo on a
holdout minted after both were frozen, no arm rejects on either item set after
Holm. GEPA's winner scores 0.628 on unseen scenarios against 0.685 for **no
skill at all**, the only arm in the study worse than an empty prompt. The A/A
control returned 728 of 728 items identical, so every difference between arms is
one the prompts caused.
[The run](results/evolution-study/2026-08-27-53b4965-five-arm/README.md).

Two findings from the same line of work cut into the instrument rather than the
engines. Accuracy on a two-option key adds discrimination to response bias, and
separating them found **three of ten templates measuring nothing** on the target
model, which takes a 728-item run down to 504 items of signal. And no
verdict-bearing replication can be built on this corpus today, because every
hosted model measured so far solves it with an empty prompt; nine harder
templates were authored and every one either ceilings or answers one-sidedly.

[`docs/STATUS.md`](docs/STATUS.md) is the ledger: every run, what it showed,
which measurements turned out to be broken, and which tracks are untouched.
[`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) covers what is wrong with the
harness, the statistics, the datasets and the judges.

## Development

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --group dev
```

That is the whole install. Run the full gate, which is lint, types, tests,
coverage floors and the repository-integrity checks:

```bash
uv run de check
```

`de check` makes no model calls and is fully deterministic, so the same command
runs unchanged in [`.github/workflows/check.yml`](.github/workflows/check.yml)
on every push and pull request. It is bound to `pre-commit` as a fast subset and
to `pre-push` in full. Running it in CI as well as locally is not redundant:
local tells you the working tree passes, CI tells you the *commit* passes, and a
gate that has only ever run on the machine it was written on has only ever been
asked about that machine.

The full gate is 22 steps. Eleven of them check the method instead of the
code:

| Step | Refuses |
| --- | --- |
| trigger sets | a skill with no trigger set, or a trigger set naming a skill that no longer exists |
| run provenance | a published run that does not state its answer-key version, or whose prediction cannot be shown to predate its data |
| integrity wiring | a module with a coverage floor that no entry point can reach |
| decision register | a change to the answer key or the shipped skill with no entry in [`docs/DECISIONS.md`](docs/DECISIONS.md) |
| label corrections | a version the answer key has reached that no line of [`datasets/triggers/corrections.jsonl`](datasets/triggers/corrections.jsonl) accounts for |
| documentation | a `de` command, path, or component that this README names and the repository does not have, a document under `docs/` that [`docs/README.md`](docs/README.md) does not list, and a living document that names no audience |
| citations | a claim carrying an arXiv identifier, or a `\cite` key in `paper/`, whose entry in [`paper/refs.bib`](paper/refs.bib) has no quote behind it |
| generated regions | a table a document derives from the repository that is no longer what it derives from, and a renderer no document uses |
| document drift | a living document with no review on record, or one more than ten commits past the last one |
| published claims | a measured number, on the website or in a document, that no longer matches the sentence it came from |
| site | a published build older than the documents it publishes, naming the files that moved |

Merging to `main` publishes the site through
[`.github/workflows/deploy-site.yml`](.github/workflows/deploy-site.yml).
Nothing on a developer machine can publish. `de check` is offline by design and
cannot see the live site, so that question is answered on demand:

```bash
uv run de deployed
```

It fetches what the site says about its own origin and compares that against
`origin/main`. Exit 0 means the live site is a build of the current `main`, 1
means it is behind, and 2 means the question could not be answered, which is
deliberately distinct from 0.

Editing any document the site renders makes the published build stale, so the
loop is edit, rebuild, commit both:

```bash
uv run de sync && uv run de site
```

`de site` needs Node and npm on `PATH`, because the site is an Astro project.
The gate that demands you run it does not.

Two commands keep the documents honest. `de sync` rewrites the tables and
figures the documents derive from the repository, and `de drift` lists the
documents whose subject has moved since anyone recorded reading them.

The rest: `de index` regenerates
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
