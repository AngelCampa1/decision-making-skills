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

---

## Appended the same day: the concurrency claim above is wrong

The table at the top of this entry rests on two serial runs agreeing at 15 of 21,
and reads the overlapping run's 17 of 21 as the cost of sharing the server. Both
halves of that are wrong, and the second one only looked right because of the
first.

**The agreement was a coincidence.** After both matched runs finished I scored
the seed body again, serially, with nothing else running and the lock free. Two
back-to-back replicates:

```
replicate 1: 18/21 = 0.8571
replicate 2: 19/21 = 0.9048
```

They disagree with each other. Three more immediately after gave 19, 19, 19.
The same body, the same 21 items, the same model, temperature zero, one process.

Every measurement of `edc3ee70` on record today:

| | score |
| --- | --- |
| GEPA, 2026-08-26, reflector 120b | 15 / 21 |
| SkillOpt, first matched-20b run | 15 / 21 |
| SkillOpt, overlapping a live run | 17 / 21 |
| GEPA, clean matched run | 17 / 21 |
| SkillOpt, clean matched run | 17 / 21 |
| standalone replicate 1 | 18 / 21 |
| standalone replicates 2-5 | 19 / 21 |

**Range: 15 to 19 of 21.** Four items, nineteen points, on a body nobody
touched.

So the overlapping run's 17 is not evidence about concurrency. It is the middle
of the distribution, and both clean runs landed on exactly the same number. The
2026-08-19 falsifier's finding stands on its own evidence and is not
re-confirmed here; this entry cannot separate a concurrency effect from the
run-to-run spread, because the spread is bigger than the effect it claimed.

**The mojibake claim goes the same way.** 18 of 21 for the corrupted body is
inside the clean body's own range. That the corrupted skill "scored three items
better" was a comparison against a number that happens to be the bottom of the
distribution. What the earlier entry could legitimately claim is narrower: a run
scoring 0.857 tells you nothing about the skill, whether the skill was corrupted
or not.

## What is actually true, and it is worse

**This venue is not deterministic, serially, at temperature zero.** Two calls,
one after another, same prompt, different answers. The recent replicates cluster
at 19 while the in-run measurements cluster at 15-17, which looks like drift in
server state rather than symmetric noise — the standalone replicates make
back-to-back calls, and a run interleaves them with hosted reflector calls, so
the server sits idle between batches. That is a hypothesis, not a finding.

The consequence does not depend on the mechanism:

**Both engines' Phase 2 results are inside the noise.** GEPA's winner scored
20/21 against the seed's 17/21 *in the same run*. SkillOpt's scored 21/21
against the same 17/21. Three and four items — and the seed body alone moves
four items across runs. Neither gain is distinguishable from re-measuring the
seed skill.

Prediction 2 asked for ≥ 3 points and both engines cleared it by a wide margin.
**It stays as registered and it is reported as met, and it should not be
believed**, because the bar it set is under the instrument's own resolution.
Registering a bar before a run does not make it measurable.

**Every number in this study needs repeats.** Phase 3 was designed with paired
statistics on a frozen holdout, which is right, and it was going to run each arm
once, which is not. An arm measured once here carries ±2 items of noise on 21,
and the effects being tested are that size. The holdout has to be scored with
repeats per item, and the pre-registration has to name how many and how they are
combined, computed from the variance being measured now rather than guessed.

This is the study's own thesis arriving uninvited. The surveyed engines report
single-run point estimates on fixed splits, and this instrument was about to do
the same thing while measuring them for it.
