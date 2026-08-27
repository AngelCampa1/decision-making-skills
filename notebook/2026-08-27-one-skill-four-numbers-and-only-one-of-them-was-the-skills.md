# 2026-08-27 — One skill, four numbers, and only one of them was the skill's

Not a planned experiment. Four separate accidents produced four measurements of
the *same* seed body, on the *same* 21 validation items, against the same model
at temperature zero, within a few hours of each other.

| condition | score | items |
| --- | --- | --- |
| GEPA, serial | 0.7143 | 15 / 21 |
| SkillOpt, serial | 0.7143 | 15 / 21 |
| SkillOpt, overlapping a live GEPA run | **0.8095** | 17 / 21 |
| SkillOpt, body mojibaked by a locale | **0.8571** | 18 / 21 |

The first two are the same number. That is the control, and it was not designed:
two engines, two processes, hours apart, both scoring `edc3ee70` through the
same scorer. **This venue is deterministic when it is left alone.**

Which makes the other two rows measurements rather than noise.

## Concurrency is worth two items here

The third row is a run that started while another search was still calling the
same local server. Two callers, one batching server, and the seed skill picked
up two extra correct answers.

This repository already had that finding: on 2026-08-19 a falsifier asked the
same forty items twice under concurrency and got a different answer to **every
one** — 0 of 40 agreement, McNemar p < 0.0001 — which is why
`runner.CONCURRENCY_UNSAFE` names the `ollama` prefix. What that run could not
show is which of the two conditions was right, because it had no serial control
taken with the same body on the same day. This one does: 15 of 21, twice,
serially, and 17 of 21 when shared.

It is not a claim that concurrency *helps*. Two items on 21 is one direction of
a perturbation that has no reason to have a direction. It is a claim that
**sharing the server moves the number**, and that anything measured across a
window where a second process was running is not measuring the skill.

## The locale is worth three

The fourth row is the run whose trainer read a UTF-8 skill as `cp1252`. Eight
typographic characters became twenty-four, and the resulting body — 3,444
characters of a skill nobody wrote — scored three items better than the real
one. That has [its own entry](2026-08-27-the-engine-that-could-not-run-and-the-number-it-produced-anyway.md).

## What this does to the study's headline question

The study asks whether an evolved skill beats a placebo on fresh items, and
plans to answer it with paired statistics on a frozen holdout. Good. But
Phase 2's per-candidate numbers are single runs on 21 items, and this table is
the scale bar for them:

- corrupting the skill: **+14.3 points**
- letting another process share the GPU: **+9.5 points**
- the bar Prediction 2 set for "an engine improved the skill": **+3 points**

Two things with no decision content in them clear that bar by three to five
times. Any Phase 2 gain under about ten points says nothing on its own, and
should be read as "the search produced a candidate worth testing properly"
rather than as a result.

**This is the argument for the whole study, arrived at sideways.** Every engine
surveyed reports single-run point estimates on a fixed split with no repeats and
no intervals. On this corpus, at this denominator, that practice cannot
distinguish a better skill from a corrupted one, and cannot distinguish either
from a busy GPU.

## What was thrown away

Three run directories are contaminated and none of their records may be used:

- `2026-08-27-1fb88b4-skillopt-matched-20b` — 58 records, no `json_repair`, so
  an unknown number of analyst edits were dropped silently.
- `2026-08-27-90a8d31-gepa-matched-20b` — 60 records, overlapped by the run
  below for an unknown part of its life. `RunRecord` carries no timestamp, so
  **which** records fall inside the overlap cannot be recovered. That is the
  reason the whole directory goes rather than the affected part of it.
- `2026-08-27-51a26cd-skillopt-matched-20b` — 24 records, the overlapping run.

They stay on disk, gitignored, because the 0.8095 in the third one is the
measurement above.

## The guard

A rule in `AGENTS.md` did not stop this and neither did a shell loop written to
serialise the two runs — twice, in one session, by somebody who knew the rule
and had already made the mistake once that day. The second time, the loop misread
a process list and launched the next engine into a live run.

So it is checked by the code that makes the calls now. `evolution/solo.py` takes
a lock for the run's target model when that model is on `CONCURRENCY_UNSAFE`,
and a second `de evolve` against it refuses to start and says what is already
running. A hosted endpoint is not locked: it fans out by design and two runs
against it are two runs. A lock whose process has died is not a holder, because
a guard that a killed run leaves permanently armed becomes the problem it was
meant to solve.

**`RunRecord` should carry a timestamp.** It would have turned "discard the
directory" into "discard eleven records". Noted here rather than fixed, because
adding a field to the record schema mid-study changes the golden files and every
resume key, and that is a change to make deliberately between runs.
