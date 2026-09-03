# Failure taxonomy

**Audience:** the evaluating reader.

**What this is.** The codes this repository scores failures against, built
bottom-up from real traces per the Husain/Shankar loop and seeded with
Harness-Bench's five categories as a citable prior to confirm or refute. The
taxonomy determines the metrics, not the other way round.

Corpus read so far: 280 control-arm traces, Haiku, on the pre-rebuild
single-turn corpus (`results/evidence-ledger/2026-08-10-baseline-corpus/`).
Saturation is not reached, and not close. 15 zeros is a thin sample, and 14 of
them came from two variants of one template. Everything below is provisional.

## The headline finding

Fifteen of fifteen zeros were item defects, not agent failures.

Every one was labelled `agent_wrong` automatically, because that is what the
scorer assigns to a parseable answer that does not match ground truth. Every one
turned out, on reading, to be a case where the model's answer was defensible and
the ground truth was not.

Reporting the automatic label would have produced a 5% agent error rate that did
not exist. `agent_wrong` is therefore provisional until somebody reads the
trace, and `item_defect` is now its own cause rather than a fold into
`verifier_defect`. The parser and the comparison were correct in all fifteen
cases, and the fixes are completely different.

The general point, which is not specific to this corpus: at low difficulty,
benchmark defects dominate the zeros. You cannot build a failure taxonomy for
the *agent* until the corpus is hard enough to produce agent failures, and
attempting one earlier produces a taxonomy of your own mistakes wearing the
model's name.

## Running out of output budget is its own code

`output_truncated`, added 2026-09-03, holds the reply the output cap stopped
before it reached an answer line. It is the fourth cause the scorer assigns
without anyone reading a trace, and it comes out of a live evolution run rather
than out of the 280 traces coded above.

A thinking model returns its chain in one field and its answer in another. When
the cap falls inside the chain, the answer field comes back empty and the
backend's stop reason reads `length`. Labelled `format_violation`, that row
says the model could not follow the output contract; what happened is that the
run gave it too few tokens to reach one.

Read off the first 42 calls of a 14,700-call study: 6 rows carried an
output-token count at the run's cap and an empty response. **Four of the six
were the one arm whose document makes the model reason longest.** Truncation is
therefore arm-dependent, and it moves comparisons instead of moving every arm
together, which is the shape the control-token defect already had. An arm can
lose on budget and be read as an arm that cannot follow a format.

Those figures were reported to the session that wrote this code and are not
re-derived here, because the run's records sit outside the tree it could read.
[`notebook/2026-09-03-a-thinking-model-spent-its-whole-budget-reasoning.md`](../notebook/2026-09-03-a-thinking-model-spent-its-whole-budget-reasoning.md)
carries them with that provenance attached, and carries the one number that
does not yet cohere: 4,096 both as the cap and as the window a cap has to fit
inside.

Two columns are what make it a reading rather than an inference. The record
carries the backend's own stop reason and the full reasoning text, so a zero
beside an empty response says how the budget was spent and what ended the
generation. Neither reached the record before, which is why those six rows were
found by somebody reading a live run and not by a gate. Ollama's native surface
had been reporting both to the provider for weeks; the record dropped them, and
a field a provider parses and a record discards is invisible to every gate here.

**The code is `no_answer_line` and nothing wider.** A reply that wrote a
complete answer line naming something off the menu keeps its `format_violation`
however it stopped, because it reached an answer line and the cap fell after it.
The 87 `ANSWER: monitor /think` rows are that shape, on this venue, on a verbose
thinking model. The cost of the narrow rule is that a reply cut off mid-option
reads as a format violation, and no field separates those two readings.

**No committed record is relabelled.** A row written before the change carries
an empty stop reason, so its cause cannot be re-derived and it keeps the
`format_violation` it was scored with. One checkpoint that spans the change
therefore holds both labels for one physical failure, which is the same rule the
control-token defect follows and needs saying out loud for anyone counting
causes over a study that resumed.

## Item defects, open-coded

Three sub-kinds, each found by a real run rather than by a test, and each with a
different fix. That last part is the reason they are separate codes.

| Code | What it is | Fix |
| --- | --- | --- |
| `ambiguous-threshold` | The item sits on or beside a knife edge, and the sentence stating the rule has more than one reading. `outage_h == sla_h == 11` against "only after 11 continuous hours". | Sampling margin: reject any binding where a ±1 nudge flips the answer. |
| `unstated-rule` | The item gives the quantities but never states what decides the question, so the model supplies a reasonable rule of its own. rel-009 gave a delay and a slack and left "is 20 minutes enough to make a connection" to judgement about real airports. | Add the policy fact. Every other template had one. |
| `ungoverned-scenario` | The stated rule is silent about the situation the sampling produced. rel-008 drew 155 seats in use against a 116-seat quote; the utilisation rule addresses under-use and says nothing about a shortfall. | Cross-variable `constraints`, excluding the scenario at build time. |

No single guard catches all three. What caught them was running the control arm
and reading the failures, which is the job the clean-room gate has and the reason
it is computed on the control arm only.

## A coded signal that did not survive checking

Coding all 280 responses for *appeals to real-world considerations beyond the
stated facts* ("in practice", "prudent", "risk of", "typical") looked like a
strong predictor: 28 occurrences, 13 of them wrong, against a base rate of 5.4%.
An 8.6× lift.

It does not hold. 19 of the 28 appeals are in rel-009, the template with no
stated rule. Outside rel-008 and rel-009 the code appears 8 times and predicts
zero failures. The appeal is a symptom of an item that failed to state its rule,
not an independent failure mode. The model reaches for outside knowledge
precisely when the item did not supply the rule, which is reasonable behaviour.

This is the confound the axial-coding step exists to catch, and it would have
gone into the paper as a finding if the pass had stopped at the correlation.

## Harness-Bench's five categories, against this data

| Category | Status here |
| --- | --- |
| Output-contract violations | **Zero observed.** 280/280 parsed, no format violations in any stratum. Not evidence the guard is unnecessary: the format contract is in every arm, and this is the control arm, which is the easiest case for it. |
| Tool / recovery failures | **Not applicable.** The harness runs with `--tools ""`. |
| Evidence / grounding gaps | **Zero observed**, but this corpus cannot produce them: every fact needed is in the prompt and there is nothing to retrieve. |
| Artifact-commitment failures | **Not applicable** to a single-answer task. |
| State / continuation issues | **Not applicable** to a single-turn task. |

Four of five are structurally unreachable in this venue. That is itself an
argument for the accumulation venue described in
[`ACCUMULATION_VENUE.md`](ACCUMULATION_VENUE.md), where state, continuation and
grounding become reachable, and a reason not to claim this taxonomy generalises.

## What this changes about the metrics

- Somebody reads every zero before it is counted. The automatic cause is a
  triage label, not a result. A run that reports agent error without a trace
  read is reporting its own defect rate.
- `item_defect` counts are reported separately and never enter the numerator or
  denominator of an accuracy comparison. An item that should not exist is not
  evidence about an arm.
- Format integrity stays a guard rather than a metric. Nothing here suggests it
  is at risk, and a guard that has never fired is still worth keeping when the
  treatment arms are the ones that could break it.
- No agent-failure metric is finalised yet, because nobody has observed an agent
  failure. Any taxonomy of how the model fails at ranking has to wait for a
  corpus that can make it fail.
