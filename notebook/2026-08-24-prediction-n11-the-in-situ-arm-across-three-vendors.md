# 2026-08-24 — prediction: N11, the in-situ arm across three vendors

Registered **before the first call of the arm**, and committed before it is
launched. What was already run, and therefore already seen, is declared below
rather than left for a reader to notice.

## Why this run exists

[Track N9](2026-08-19-prediction-n9-does-position-move-firing.md) asked whether
a skill description fires when it is offered to a live coding agent rather than
to a model under a replaced system prompt. It is
[void](../results/decision-making/2026-08-19-505b236-n9-in-situ-void/README.md):
516 calls discarded at a 0.8643 parse rate, 70 responses carrying no `fire` key
and no JSON at all, the model answering as Claude Code instead of emitting the
contract. So the harness still has no measurement of how the shipped description
behaves in the venue anybody uses, and that blocks every future L and M claim.

The Antigravity CLI is that venue by construction. It has no `--system-prompt`
and no `--tools`, every call arrives inside roughly fourteen thousand tokens of
agent scaffold with 57 tools live, and `--json-schema` carries the verdict out of
band in `structured_output` where the prose around it cannot corrupt it.

## What runs

Three arms, one per vendor, on answer key **v6**:

| arm | calls |
|---|---|
| `agy/gemini-3.7-flash-low` | 330 × 2 = 660 |
| `agy/gpt-oss-120b-medium` | 330 × 2 = 660 |
| `agy/claude-sonnet-4-6` | 330 × 2 = 660 |
| **bridge**: `haiku` via `claude -p`, `--in-situ` | 330 × 2 = 660 |
| **total** | **2,640**, of which 1,980 are not on the Claude subscription |

`--contract schema` on every agy arm. Model ids are pinned; `UNPINNED_ALIASES`
refuses `auto`, `pro` and `flash`, and `--effort` is never passed because the
level is already baked into the id.

## What was already seen, declared

A canary ran band `s` at one repeat on `agy/gemini-3.7-flash-low` before this was
written: **90 calls, parse rate 1.0000, zero unparseable**, recall 30/30,
FPR 9/60 = 0.1500, accuracy 0.9000, and `council` and `hinge` both appearing
among the routed positives. It was run to size the wave and to check the schema
contract against a real v6 item, and it did both.

**Those 90 rows are not part of any arm.** They were written before `status` and
`num_turns` reached the checkpoint, so they carry 22 fields where the arm's rows
will carry more, and a checkpoint holding two record shapes is the kind of thing
that is discovered late. The file is kept as canary evidence and the arm starts
clean.

What this costs: predictions 1, 3 and 4 below are informed by band `s` on one of
the four arms. Band `s` is one of four strata, `gemini-3.7-flash-low` is one of
four arms, and one repeat is half of two. **The registered primary is scored on
bands `m`, `l` and `xl`**, which nothing has seen, and band `s` on that one arm
is reported separately and marked. The other three arms are unseen entirely.

## What will be computed, from which records, over which denominator

- **Per arm:** `trigger_arms.summarise` over 660 parsed records — accuracy,
  precision, recall, FPR.
- **Parse rate:** `parse_rate_over_all_repeats`, over every call the arm was
  asked to make, which is the denominator that counts a missing row as
  unparseable.
- **Intervals:** `bootstrap_rate` clustered on `triple`, because the three items
  of a triple share a scenario.
- **Within arm:** `bootstrap_rate_difference` for `s`+`m` against `l`+`xl`.
- **Routing:** `routing_by_procedure` under both the `first` and `any` rules.

**No p-value is offered anywhere in this run, and that is a property of the
guards rather than a choice.** `models_comparable` refuses to pool records
carrying different model stamps, so the three vendors cannot be paired against
each other and none of them can be paired against the bridge. The four arms are
reported side by side with intervals. A reader who wants a test between two
venues needs a design that holds the model fixed, and this is not it.

## Two open questions, settled here rather than at analysis time

**An `ERROR`-status call carrying a valid verdict is scored.** One was observed
on 2026-08-21: a permission check failed against a path unrelated to the item,
and `structured_output` arrived anyway. The answer is present and the failure is
on an axis the measurement does not depend on, so discarding it would discard
data on an irrelevant criterion. **Guard:** if `ERROR` status exceeds 5% of any
arm's calls, that arm's rates are reported with the rate stated beside them,
because at that level the venue is doing something systematic and the reader
needs to see it. This is only registrable because `status` now reaches the
record; until today the provider carried the distinction and the runner dropped
it.

**The void floor is 0.90 over all repeats**, which is the coded floor and no
other number. N9 registered 0.95 against a 0.90 floor and never had to reconcile
them because every reading there sat below both. Prediction 1 registers 0.99 as
the substantive band, so the void condition and the finding are separate
instruments and neither is standing in for the other. An arm landing between 0.90
and 0.99 is published **and** falsifies prediction 1, which is the correct
behaviour.

## Predictions

**1. Every agy arm parses at 0.99 or better.** The canary read 1.0000 on 90
calls. Schema enforcement either carries the contract out of band or it does
not; 0.95 would leave room for a real problem to pass.

**2. The bridge arm parses below 0.99, and this is the control that makes
prediction 1 mean anything.** The bridge is N9's design at v6: the contract
travels inside an appended system prompt rather than out of band. If it parses
cleanly too, then N9's void was something about v4 or about that day rather than
about where the contract travels, and the schema fix is not what fixed it. **I
would rather learn that from this arm than assume it.**

**3. Every agy arm has a higher FPR than the same description reaches in the
isolated venue.** The N10 arms are the comparison and the comparison is visual,
per the guards. In situ the description competes with a scaffold that already has
a job. The canary's band-`s` FPR was 0.1500 against isolated v4 FPRs between
0.0756 and 0.0988. Direction registered, magnitude not.

**4. `council` and `hinge` are routed to at a nonzero rate on every agy arm.**
Partly seen on one arm at one band. It is registered because the interesting
failure is an arm that fires correctly and never once selects either of the two
procedures added at v5, and that failure is invisible unless it is named first.

**5. Between-vendor agreement is lower than within-vendor between-repeat
agreement, in all three vendor pairs.** Per item, the share of repeats an arm
fired on; agreement is the mean absolute difference of those shares. Descriptive,
with intervals and no test. If the three vendors agree with each other about as
well as one vendor agrees with itself, then firing is a property of the item and
the venue rather than of the model, which would be a larger result than anything
else in this run.

## Where I expect to be wrong

**Prediction 2 is the one I am least sure of and it carries the most.** N9's
failure was diagnosed as the model answering as Claude Code, which is an identity
effect specific to a Claude model inside the Claude CLI. The bridge is exactly
that configuration again, so the mechanism should reproduce. But N9 ran on v4 and
the 72 items added at v5 are not in its record at all, and the parse rate is a
property of how a model reacts to items as much as of where the contract sits.

**Prediction 3 has an uninteresting way to be met.** An in-situ arm that fires on
almost everything scores a high FPR and a perfect recall, and that is not the
description discriminating badly, it is an agent being agreeable. The check is
whether recall and FPR move together across the four arms. If every arm has both
near the top, the venue is not measuring the description at all, and that is
worth saying plainly rather than reporting as an FPR result.

**Prediction 5 assumes the three vendors are three draws from the same
question.** They are three different models inside one scaffold, and
`agy/claude-sonnet-4-6` is a frontier model where `agy/gemini-3.7-flash-low` is
the cheapest thing the binary serves. A spread that tracks capability rather than
vendor would be the honest reading, and this run cannot separate the two.
