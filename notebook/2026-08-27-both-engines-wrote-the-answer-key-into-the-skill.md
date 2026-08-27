# 2026-08-27 — Both engines wrote the answer key into the skill

Phase 2's result, against [the prediction registered before it](2026-08-26-prediction-two-engines-on-a-matched-budget.md)
and its two amendments. Target `ollama/qwen3:1.7b`, reflector
`nvbuild/openai/gpt-oss-20b`, 70 training items, 21 validation items, a 300-call
guard on each engine, an 8,192-token output cap.

Runs: `results/evolution/2026-08-27-7038a46-gepa-matched-20b` and
`...-skillopt-matched-20b`, both gitignored, both resumable from their
checkpoints.

## What the runs report

| | candidates | records | stopped by | winner chosen by | winner | seed, same run |
| --- | --- | --- | --- | --- | --- | --- |
| GEPA | 16 | 289 | the 300-call guard | our `_best_validated` | 20 / 21 | 17 / 21 |
| SkillOpt | 9 | 205 | the engine, after 9 steps | the engine, at step 1 | 21 / 21 | 18 / 21 |

SkillOpt's nine steps took 1,758 seconds and went accept 1, reject 7, skip 1 —
its winner arrived first and was never beaten. GEPA never got to declare one, so
`_best_validated` ranked the eight candidates that had been scored on the whole
validation pool and took the top. `winner.json` records that as
`"winner_source": "lineage (budget-stopped)"`, which is the point of the field.

## Do not believe those numbers, and now there is a number for why

The seed body has been scored again and again today, in runs and deliberately,
and has returned anywhere from **15 to 19 of 21** — four items of spread on a
body nobody edited, at temperature zero, one process at a time. That is
[its own entry](2026-08-27-one-skill-four-numbers-and-only-one-of-them-was-the-skills.md)
and until now it was an anecdote about numbers gathered under differing
conditions.

The two run checkpoints settle it, because they contain repeats nobody planned.
Resumption re-asked some candidates the same item twice, and every one of those
pairs is a controlled replicate: same body, same item, same model, same run.

**49 repeated pairs. 7 disagreed. A per-item flip rate of 14.3%, Wilson 95%
[7.1%, 26.7%].**

The seed skill on its own is the sharpest cut of it. Asked ten validation items
twice inside a run, it contradicted itself on five:

```
GEPA run       [True, False]  rel-004-inventory-reorder#v0-d1-late
               [True, False]  rel-005-security-patch#v0-d4-middle
SkillOpt run   [True, False]  rel-002-deploy-window#v0-d1-early
               [True, False]  rel-004-inventory-reorder#v0-d1-late
               [False, True]  rel-006-refund-request#v0-d4-middle
```

A 14.3% flip rate puts the standard deviation of a 21-item score at **1.2 items,
about 6 points**, with a 95% interval of 0.9 to 1.7 items. The observed 15-to-19
range across roughly ten draws is exactly what that predicts.

So: both winners are three items above their seed, and one measurement of a
21-item score carries ±1.2 items of noise before anything about the skill enters
into it. **The score gains are inside the instrument.** Nothing in the first
table separates an improved skill from a re-measurement.

## What the gain actually is, which does survive

The scorer distinguishes a wrong answer from an unreadable one, and that split
holds up where the total does not. Counted over every validation call each body
received, duplicates included:

| | calls | correct | wrong answer | no answer line | ran to the token cap |
| --- | --- | --- | --- | --- | --- |
| seed, GEPA run | 23 | 17 | 3 | 3 | 3 |
| GEPA winner | 28 | 26 | 2 | **0** | **0** |
| seed, SkillOpt run | 29 | 23 | 3 | 3 | 3 |
| SkillOpt winner | 29 | 29 | **0** | **0** | **0** |

**The format violations and the capped generations are the same records.** Every
unreadable answer is a generation that ran to all 8,192 tokens and never emitted
an answer line — a 1.7B model talking itself out of ever concluding. And they
land on the same three items in both runs:
`rel-006-refund-request#v0-d4-middle`, `rel-009-flight-rebook#v1-d1-middle`,
`rel-004-inventory-reorder#v0-d1-late`.

That is the part of the seed skill's failure that is *not* noise, and it is the
part both engines fixed. Prediction 3 holds. Half of the seed's failures were
runaway generations, both winners took them to zero, and it is the only piece of
either engine's gain that is bigger than the measurement error.

A real result and a small one: **an evolved skill stopped a 1.7B model from
rambling past its own answer.** That is not what these engines are sold as
doing.

## Both engines wrote the answer key in, by different routes

This is the finding, and it does not depend on a score.

**GEPA stopped being a decision skill.** Its winner is titled *"Travel-Connection
Decision Assistant Instruction Set"* and opens: *"You are a short-form decision
aid for airline-travel connectivity questions."* Its domain section is
`rel-009-flight-rebook` and nothing else — slack time, minimum legal connection
time, "rebooking forfeits slack protection" — and it names the template's two
option strings, `wait_at_gate` and `rebook_now`. It closes with a worked example
whose arithmetic is wrong: *"32 min slack < 94 min MLCT? No"*.

**A single template's specialisation scored 20 of 21 across ten templates.** The
domain content cannot be what earned that. The format sections were.

**SkillOpt kept the skill and stapled the answer key to it.** Its winner is the
seed body, structure intact, plus two appended sections. One of them is headed,
in the engine's own words:

> **Examples from the training data:**
> - Renew vs. renegotiate: usage = 199/436 ≈ 45.6 % < 61 % → renegotiate.
> - File SLA claim: downtime = 11 h > 9 h → file claim.
> - Scale cache: forecast peak = 1749; required capacity = 1749 × 1.25 = 2186. Since current 2034 < 2186, scale up.
> - Escalate alert: affected rate = 17 % > 8 % → escalated.
> - Approve refund: delivery 27 days ago; window 42 days → in window → approve.

Every one of those numbers is in the training pool, and I went and checked rather
than assuming: `199`, `436`, `61`, `11`, `9`, `1749`, `2034`, `17`, `8`, `27`,
`42` all appear in the 70 items the search was given. Five templates transcribed
with their values and their verdicts. A second appended section names three more
— reorder before stock runs out, patch at a severity threshold, deploy when the
smoke test fits — bringing it to eight of ten.

The two winners memorised **near-disjoint** sets. GEPA took `rel-009` and
abandoned the rest; SkillOpt took the other eight and left `rel-009` alone.
Their union is the corpus.

## The predictions

1. **Both engines explore at least three candidates.** Met: 16 and 9.
2. **A winner beats the seed by ≥ 3 points.** Met by both, by a wide margin,
   **and it should not be believed.** The bar was set at half the noise. It
   stays as registered and it is reported as met, because registering a bar
   before a run does not make it measurable and deleting it afterwards would be
   worse.
3. **Format violations fall.** Met, and it is the only part of the gain the
   instrument can see.
4. **Neither winner generalises.** Not tested yet; that is Phase 3.
5. *(Registered in the reflector amendment)* **The two winners share memorised
   content.** Met on the substance, wrong on the mechanism: both memorised,
   heavily, but on almost disjoint templates rather than the same ones. A second
   reflector produced memorisation again, which is what makes this a claim about
   the setup rather than about one run.

## What this does to Phase 3

**The holdout as planned is not a control.** Fresh seeds over the same ten
templates redraw the numbers and leave the rules standing, and rules are what
both winners took:

- SkillOpt's winner carries `usage < threshold → renegotiate` for eight
  templates. New values do not touch it. It transfers at full strength and would
  score as generalisation.
- GEPA's winner transfers for `rel-009` and is otherwise a format instruction,
  which also transfers.

**The split has to hold out templates.** That means re-running both searches on
a template subset, because both winners have now seen all ten.

**And no arm may be scored once.** An arm measured once here carries ±1.2 items
on 21, and every effect in this entry is that size or smaller. The
pre-registration has to name a repeat count and a combining rule, computed from
the 14.3% flip rate above rather than guessed, and it has to be written before
the holdout is minted.

## Two defects found while reading the checkpoints

Recorded here, not yet fixed:

- **`winner.json` reports the wrong score for a budget-stopped run.** The
  selection is right — `_best_validated` ranks only candidates scored on all 21
  and refuses partial passes — but `_freeze` then writes the score off the
  *lineage* record, which for GEPA is the three-item minibatch the candidate was
  first seen on. GEPA's winner therefore reads `"score": 1.0, "n_items": 3` when
  the basis for choosing it was 20 of 21. A study that quoted that field would
  quote a number selection never used.
- **`_best_validated` silently keeps the last of a repeated pair.** It builds
  one answer per item and a re-asked item overwrites, so a candidate whose
  repeats disagree gets a score that depends on record order. It is the reason
  the seed reads 15 of 21 from the checkpoint and 17 of 21 from the lineage of
  the same run. Harmless while the ranking is over whole passes; not harmless
  once repeats are deliberate, which Phase 3 makes them.

---

## Appended the same day: both defects fixed, and one artefact left alone

`_best_validated` now counts every answer a candidate gave rather than the last
one, and returns a `Validated` carrying `correct`, `calls` and `items` so the
score and the basis for it travel together. `_freeze` writes that score, and a
new `n_calls` field says how many answers it is over. Two tests pin the
behaviour that was wrong, and one pins that a partial pass is still refused —
counting repeats must not let three answers to one item pass as a full pass.

**The two run directories are not being regenerated.** They are the record of
what happened, and `results/evolution/2026-08-27-7038a46-gepa-matched-20b/winner.json`
still reads `"score": 1.0, "n_items": 3`. The number selection was actually made
on is **20 of 21**, computed above from that run's own checkpoint, and it is
stated here rather than written back over the artefact. Anything downstream
reads the checkpoint.

---

## Appended the same day: the unreadable answers were the harness, not the skill

Two more measurements landed after the entry above, and together they take the
"format compliance is the real gain" reading apart.

### The venue is deterministic when nothing else is happening

Ten back-to-back passes of the seed body over the same 21 items, one process,
nothing else running:

```
18, 19, 19, 19, 19, 19, 19, 19, 19, 19
```

One item flipped, on the first pass only. Across 189 adjacent call pairs, **one
disagreement**: 0.53%, Wilson 95% [0.09%, 2.9%], against 14.3% [7.1%, 26.7%]
from repeats inside the two runs. The intervals do not come close to
overlapping.

The two items the seed gets wrong every time are
`rel-005-security-patch#v0-d4-early` and `rel-009-flight-rebook#v1-d1-middle`,
and they are wrong the same way ten times running. That is the part of a score
that means something here.

So the flip rate above is not a property of the venue. It is a property of the
conditions calls are made under, and **no number measured under one condition
transfers to another.** Record-gap does not explain it either: the in-run
disagreements happen at gaps of 4 and 8 records as readily as at 21.

### The unreadable answers walked off the end of the context window

`GET /api/ps` reports the loaded model's `context_length` as **4096**. The runs
sent `max_tokens: 8192`. Those two numbers are not compatible, and the records
say what happens when they meet:

| | n | max prompt + output |
| --- | --- | --- |
| readable answers | 478 | **3,861** |
| unreadable answers | 16 | output alone reached 8,192 |

**Not one readable answer in 478 ever crossed 4,096 total tokens.** Every long
unreadable one is past it — 5,488 and 8,192 output tokens on top of a
thousand-token prompt. Past the window ollama shifts the context, the system
prompt and the question go out of it, and the model cannot emit an answer line
because it no longer has the question. It then talks until the cap.

That is a cliff, not a gradient. And the 8,192 cap added on 2026-08-26 to stop a
40,960-token runaway sits *above* the cliff, so it truncates the failure rather
than preventing it.

### What this retracts

**The format violations were a misconfigured venue.** The section above credits
both engines with taking them to zero and calls it the only part of the gain the
instrument can see. The mechanism is smaller than that: a shorter, more directive
skill gets the model to its answer in fewer tokens, which keeps it on the near
side of a 4,096-token cliff the harness should never have let it approach. Real,
reproducible, and a workaround for a defect rather than a decision-quality gain.

Two of the sixteen unreadable answers are under the cliff, at 522 and 2,973
output tokens. Those are genuine format failures. Fourteen are the harness.

### What Phase 3 has to settle first

- **Give the venue a context window the cap fits inside**, and record which.
  Ollama's OpenAI-compatible endpoint takes no `num_ctx`, so this is a change of
  venue configuration, and it makes runs on either side of it incomparable. It
  belongs in the pre-registration rather than in a quiet fix.
- **Refuse a cap above the window.** A harness that sends `max_tokens` larger
  than the model's context is asking for an answer it has arranged not to be
  able to read.
- **Measure the flip rate under the study's own conditions.** Neither 14.3% nor
  0.7% is the number Phase 3 gets to use.

### The window cannot be widened from the endpoint the study uses

Checked directly, because the guard above only refuses a run and the study still
has to run one.

`POST /api/chat` with `options.num_ctx: 16384` loads the model at 16,384 and
`/api/ps` confirms it. No server restart, no environment variable, nothing on
the machine outside this repository changes. Then one call to
`/v1/chat/completions` — the OpenAI-compatible endpoint every model call in this
study goes through — and `/api/ps` reads **4,096** again.

```
resident:                          {'qwen3:1.7b': 16384}
after an OpenAI-endpoint call:     {'qwen3:1.7b': 4096}
```

The OpenAI surface takes no `num_ctx` and reloads the model at the server
default on every request, so pre-loading a wider instance buys nothing. The
window is a property of the request, and only the native surface accepts it.

**So Phase 3's target calls go through `/api/chat` with an explicit `num_ctx`,
or they run at 4,096 forever.** Which is a change of venue configuration, which
makes every number on either side of it incomparable, which is why it is written
here before the run rather than fixed quietly during one.
