# 2026-08-27 — The engine that could not run, and the number it produced anyway

SkillOpt's half of [the matched-budget prediction](2026-08-26-prediction-two-engines-on-a-matched-budget.md).
It has not produced a result yet. It produced five defects. One of them had
already reached a number I wrote down, and one of them does not crash.

## The number

The run reported this and then died:

```
[baseline result] selection hard=0.8571 soft=0.8571 gate[hard]=0.8571
```

0.857 for the seed skill on the 21 validation items. GEPA measured the same seed
skill on the same 21 items at **0.714**. Same body, same target, same
temperature, same scorer.

The cause: SkillOpt's trainer opens the seed skill with `open(path)` and no
encoding, so it decodes by locale, and this machine's locale is `cp1252`. The
skill's eight typographic characters — five em-dashes and three arrows — came
back as twenty-four. 3,428 characters became 3,444, `edc3ee70` became
`15eb7d53`, and every one of the run's 29 records is filed under a body that is
not the skill.

**The baseline was a real measurement of a corrupted prompt.** Nothing raised,
nothing looked wrong, and the two numbers sat in the same table describing what
I believed was one body.

## What that says about 21 items

Eight characters of mojibake moved the score by 14.3 points — three items out of
21. Whatever else that is, it is not a measurement of the corruption: it is what
noise looks like at this denominator. The engines being compared here report
single-run point estimates on fixed splits with no repeats and no intervals, and
this is the cleanest demonstration of the problem I am likely to get, because
the perturbation was an accident and the direction was not chosen.

It also means **Prediction 2's bar of "≥ 3 points" is inside the noise**, which
was already said when it was registered and is now measured rather than
asserted.

## A correction

I first attributed the gap to line endings. `write_text` had translated the
body to CRLF on the way to disk, the file was 3,503 bytes where the body was
3,428, and that was a real difference in a place the study depends on. It was
also not the cause: Python's universal-newline read translates it back, and both
runs did start from `edc3ee70`. The CRLF is fixed anyway, because which end
normalises is not something this code gets to assume.

## The first four, in the order they fired

**One was mine.** `EnvAdapter` declares four abstract methods. Implement exactly
those and the inherited reflection step raises `AttributeError` on
`analyst_workers`, eleven hundred lines into the trainer, after a baseline pass
and a training rollout have been spent. The four attributes it reads are set by
every built-in adapter's `__init__` and by the `_template`, and by nothing in
the abstract base — a contract carried entirely by the example. `DecisionEnv`
now mirrors them off the config in `setup`, which the trainer calls with the
same dictionary it reads its own copies from, so the environment cannot reflect
on a budget the trainer is not using.

**One was the locale**, described above. `PYTHONUTF8=1` fixes it, and so it also
fixes the `UnicodeEncodeError` the trainer hit printing `→` to a cp1252 console.
An environment variable is a poor guard, so `write_seed` now performs the
engine's own read — `path.open()`, no encoding, exactly what the trainer does —
and refuses when it does not get the body back.

**One was cosmetic and is fixed anyway**: the CRLF above.

**One is upstream, and it is the interesting one.**

## SkillOpt 0.2.0 cannot complete one optimisation step as published

`skillopt.prompts.load_prompt` reads 43 prompts off disk. **No built
distribution contains them.** The 0.2.0 wheel and the 0.2.0 sdist on PyPI ship
zero non-Python files between them, and a build from the `v0.2.0` git tag ships
none either. The cause is in the project's own `pyproject.toml`: it declares
`[tool.setuptools.packages.find]` and no `package-data`, so setuptools takes the
modules and leaves the data.

The reflection step is the second thing every optimisation step does. So
`pip install skillopt` produces an engine that raises `FileNotFoundError` before
finishing one step — for ALFWorld and its other five benchmarks exactly as much
as for anything written here.

The Python is fine. All 87 modules are byte-identical between the wheel and the
tag once line endings are normalised, which is how I know the tag is the same
code and not a later state.

The 43 files are now vendored under `datasets/vendor/skillopt-prompts/`, pinned
by commit and by a SHA-256 each in `datasets/vendor/skillopt_prompts.lock.json`,
and restored into the installed package before a run. Each run writes down which
of them it had to repair.

**Writing replacement prompts was the alternative and it was not close.** The
prompts are the reflection strategy, the reflection strategy is what SkillOpt
is, and a SkillOpt whose analyst prompt I wrote would not have been SkillOpt.
The vendored files are copies, and the gate refuses an edited one.

## And a fifth, found only because the fourth was fixed

With the prompts restored, the search ran its whole loop for the first time: two
steps, reflection, acceptance, a final summary. It proposed nothing.

```
[analyst] 1/1 minibatch_succ_000 (2 trajs) → 0 edits
[2/6 done] failure_patches=0 success_patches=0
[skip] no usable patches — skill unchanged
steps=2 accept=0 reject=0 skip=2
total tokens: 0 (prompt=0 completion=0 calls=0)
```

`reflect_s: 0.0`. The optimizer was never called.

The reflection step does not read the results the rollout returns. It reads each
item's transcript back off disk, from
`<out_dir>/predictions/<id>/conversation.json`, and when it finds none it
returns before making a call. Writing those files is the other half of the
rollout contract, and `EnvAdapter` documents the half that is a return value:
the abstract method's docstring specifies `id`, `hard` and `soft`, and says
nothing about a directory. Every built-in environment writes them, which is
again a contract carried by the examples.

**This is the worst of the five**, because it is the only one that does not
crash. A search missing its transcripts completes, exits zero, writes a
`best_skill.md`, and reports a best score — having proposed not one edit. Every
line of its log reads like a search that had nothing to improve. Had the four
crashes not happened first, this run would have produced a clean SkillOpt result
of "no change from seed", and I would have had a plausible story about a
stricter acceptance gate to explain it.

`rollout` now writes the exchange — the rendered problem, the reply, and the
scorer's verdict as `role: system`, which is how the engine's own environments
hand grading back. Wrong items carry a `fail_reason` naming the cause, because
an unreadable answer and a confidently wrong one call for different edits.

## What still stands

**GEPA's result is untouched.** It takes the seed as a string and the body never
crosses a filesystem, so `edc3ee70` is what it searched from. The memorisation
finding in [the entry before this one](2026-08-27-gepa-found-the-answer-key-and-wrote-it-into-the-skill.md)
is unaffected.

**SkillOpt has no result yet.** Its 29 records are of a body that was not the
skill and are not comparable with anything. The matched-budget run starts again
from the beginning, at the registered 261 target calls.

## The thing I keep learning

Every one of these produced output that looked like a result. The
`AttributeError` came after a printed baseline. The mojibake printed a score.
The missing prompts came after a rollout reported `hard=1.0000`. None of them
was a silent failure in the sense of producing nothing — they were silent in the
sense of producing something plausible first, and a run that dies after printing
a number leaves the number behind.
