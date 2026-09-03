# A thinking model spent its whole budget reasoning, and the record said the format was wrong

**2026-09-03.** Reading the first records of a live evolution study turned up a
zero nobody could read. `ollama/qwen3:1.7b` returns its chain in `thinking` and
its answer in `content`, and when the output cap falls inside the chain Ollama
answers with `content` as the empty string, `thinking` full, and `done_reason`
`length`. The record kept the empty `content`, the scorer found no answer line,
the row scored zero with `zero_cause: "format_violation"`, and nothing in the
row said the budget is what ended it.

## What was measured, and by whom

**Verified against the live server**, quoted in the work order this session was
given: with `num_predict: 120`, `content` length 0, `thinking` length 470,
`done_reason` `length`, `eval_count` 120. That is the reply shape, and it is
what the new tests assert against a fake.

**Reported and not re-derived here.** In the first 42 calls of a 14,700-call
study, 6 rows carried an `output_tokens` count at the cap against an empty
`response`, and four of the six were the arm whose document makes the model
reason longest. This session could not open those records: they sit under a
`results/evolution/` path it was instructed not to read outside its own
worktree, because the study is paused there waiting on this fix. So the figures
are second-hand, they are the motivation rather than the evidence, and the first
independent reading of that checkpoint should either confirm them or correct
this entry.

**One number does not cohere, and it is left open rather than resolved.** The
work order gives `output_tokens` 4,096 against a 4,096 cap. `assert_cap_fits` in
`evals/src/decision_evals/evolution/venues.py` refuses `max_tokens` plus a
2,048-token prompt allowance above the window, so a 4,096 cap needs a window of
at least 6,144 and 4,096 cannot be both. Two readings, with different fixes:
4,096 was the cap, and the window was wider; or 4,096 was the window, in which
case `num_predict` was `-1`, there was no output cap at all, and `num_ctx` is
the knob rather than `max_tokens`. Whoever reads the study's request manifest
should settle it, because the second reading changes what to do about the six
rows even though it does not change whether the row is auditable.

## What changed

Both response paths in `providers/openai_compatible.py` now record the stop
reason: `parse_native` already read `done_reason`, and `parse_completion` now
reads `finish_reason` into the same `status` field. Neither merges reasoning
into the answer text, so `parse_answer` sees exactly what it saw before and a
parsed answer scores identically.

`RunRecord` gains `reasoning` and `stop_reason`, both empty where nothing was
recorded, and `RECORD_SCHEMA_VERSION` moves 2 to 3. `reasoning` is stored whole:
on the rows this exists for it is the entire generation, so a checkpoint now
grows with a search's output tokens rather than with its answers. That cost is
accepted because a truncated row's chain is the only evidence the row has.

`zero_cause` gains `output_truncated`, set when the parse found no answer line
at all and the stop reason names the cap. **The boundary is `no_answer_line` and
nothing wider**, so a reply that wrote an off-menu answer line and then ran to
the cap keeps its `format_violation`: it reached an answer line, and Qwen3's 87
`ANSWER: monitor /think` rows are exactly that shape on this venue. The price is
that a reply cut off mid-option reads as a format violation, and no field
separates the two.

The two functions that turn a cause into a sentence for a reflector,
`adapter._feedback` and `skillopt_env._why`, both got a truncation branch. Their
own docstrings say they exist so that a reflector is not pointed at the wrong
half of a skill, and without the branch a truncated row arrived as "the reply
did not end with a parseable line" on the arm that reasons longest.

## What this does not do

**No committed record is relabelled.** A row written before today carries an
empty stop reason, so its cause cannot be re-derived, and the adapter's
re-scoring reproduces the `format_violation` it was scored with. A checkpoint
that spans this change holds both labels for one physical failure. A study
resuming into its existing checkpoint will therefore carry six rows the old way
and every later truncation the new way, which is a reason to start the
checkpoint again rather than a reason to keep the old rows and hope.

**The Claude Code venue is untouched**, and it is the venue every published
trigger run used. Its result event carries a `subtype`, `success` in this
repository's own fixture, and `parse_result` does not read it, so a truncated
reply there is still an unexplained `format_violation`.

**`max_tokens` in `_CAP_REASONS` is a forward guard and not a measurement.** No
backend wired into this harness emits it; it is the Anthropic Messages API's
spelling, kept because a second venue arriving is the moment nobody re-reads
that set. The whole-field match beside it is likewise untested against a live
value: `agy` puts `SUCCESS` and `ERROR` in the same field and reaches
`scripts/run_triggers.py` rather than a `Score`.

## Choices recorded as choices

- **`stop_reason` collides with an existing name.** `evolution/run.py` and
  `evolution/study.py` use it for why a *search* stopped and write it into a run
  manifest, so a manifest reading `budget exhausted` will sit beside rows
  reading `length`. Kept anyway: it is what Ollama, the OpenAI-compatible
  surface and the Anthropic API all call this, and the alternative was a name no
  reader would recognise. The field comment says so.
- **One schema counter for four record types.** `ShardedRecord`, `NodeRecord`
  and the elicitation record stamp `RECORD_SCHEMA_VERSION` too and gained no
  columns, so v2 and v3 of those three are identical in shape. The number says
  which release wrote a row, not which columns are present.

## Found by reading, again

Nothing here was caught by a gate, and the shape is one this repository has
recorded before: a provider parsed a field, the record discarded it, and every
step went green. `parse_native` had been reading `thinking` and `done_reason`
for weeks while `RunRecord` dropped both. No gate compares what a provider
returns against what a record keeps, so this is another clean run, a full
checkpoint, and a number measuring the wrong object.
