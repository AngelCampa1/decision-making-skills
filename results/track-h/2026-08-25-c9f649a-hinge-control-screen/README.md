# Track H — the `hinge` control screen: a second family at ceiling, and two validity checks down

**Audience:** whoever reads this number next, and whoever is briefed to break it.

**Answer key:** `H01v3-nettlefold-flour-contract-*.yaml` v3, matching the
`set_version: 3` stamped into all 40 rows of `readings.jsonl`. `item_version` is
6 in the same rows. The key covers **H01 only**; H02 and H03 have their own keys
and are scored by their own author's battery.

Prediction: [`notebook/2026-08-25-prediction-will-families-b-and-c-ceiling-too.md`](../../../notebook/2026-08-25-prediction-will-families-b-and-c-ceiling-too.md),
prediction 1, first committed at `cf7a3f8` and an ancestor of this run's commit.

Outcome: [`notebook/2026-08-25-the-hinge-screen-ceilings-and-two-validity-checks-fail.md`](../../../notebook/2026-08-25-the-hinge-screen-ceilings-and-two-validity-checks-fail.md).

**Repo commit at run time:** `c9f649a`. Nothing in the repository was edited by
the run.

**Not a published run.** The 40 calls were dispatched directly rather than
through `scripts/run_triggers.py`, so there is no checkpoint and nothing here
belongs in [`SCORECARD.md`](../../../SCORECARD.md). It is a screen that decides
where the next calls point.

## What ran

40 calls, `sonnet`, 20 per arm (`pivotal`, `matched`), unaided: the item's own
framing and format contract as the system prompt, the brief as the user turn,
and nothing else. No skill, no procedure, no reasoning scaffold, no hint that
anything was being compared. Zero failed calls, zero retries.

Notional cost $4.0639 on a Max subscription, which is a burn meter and never an
expense.

## How the blindness was made structural

`key` and `meta` are popped from the loaded YAML before a byte is rendered.
`verify_run.py` re-reads the emitted files from a process that writes nothing and
confirms zero `KEY_WORDS`. Accept-list phrases do appear in the brief and must,
because an accept list is how the brief names its own facts, so that count is
printed and never failed on.

Prompts and manifest are staged and renamed as one directory, so a crash leaves
no readable plan instead of prompts nobody can attribute. Each arm has its own
hash-named directory, one leaf per reading, manifest at the plan root outside
both. Reading ids are opaque and shuffled under seed 20260825.

Every call got a fresh temp working directory, because the auto-memory path is
keyed on cwd. The prompt went in on stdin. `ISOLATION_FLAGS` were copied verbatim
from the repository provider and checked against it at startup. The isolation
receipt was asserted per call and holds on all 40: 0 tools, 0 skills, 0 slash
commands, 0 MCP servers.

## Two defects found in the instrument, not in the model

**The CLI returns two `modelUsage` keys.** A one-turn `--model sonnet` call under
`ISOLATION_FLAGS` returns `claude-haiku-4-5-20251001` alongside
`claude-sonnet-4-6`, because the CLI spends a haiku call of its own. Taking the
first key records the wrong tier. The repository's `parse_result` requires
exactly one key and raises `CliError` on this shape. Here the answering model is
taken off the assistant event and asserted to be sonnet on every reading.

**The scorer lost four hits, and a blind adjudicator found all four.** 36 of 40
agreement. Every disagreement is the machine losing a hit and none manufactured a
swap. Two are accept-list misses (`low-water days`, `low working days`, `the
weir's own gauge`, the possessive failure [`V6_NOTE.md`](V6_NOTE.md) already
documents). Two are `affirmative_region` deleting the answer: one returned an
empty region on an unambiguous fee naming, one cut `before the deadline showed
the leat still regularly drops below milling flow` out of the middle of a
sentence and took three accept phrases with it.

Direction holds exactly as the v6 note predicted. Magnitude does not. The residue
cost 0.100 of the denominator on this run.

## Results

Read in the registered order. Dropout and off-list first, then `d`, then the
primary, then both bounds together.

| | pivotal | matched |
|---|---|---|
| N | 20 | 20 |
| `NO_BLOCK` | 0 | 0 |
| `OFF_LIST` | 3 | 0 |
| readable | 20 | 20 |

`d` = 0. `N` = 40. **`d/N` = 0.000.**

Hits 35, swaps 1, denominator 40. **Crossed primary = (35 − 1)/40 = +0.850**,
95% bootstrap [+0.725, +0.975], resampled within arm.

Against both bounds together: `d/N` = 0.000 and `coverage_bound` = 0.059, sum
0.059. Observed 0.850 sits far outside both and outside their sum, so neither
differential dropout nor asymmetric accept-list recall accounts for it, and the
two together do not either.

**The dropout bound is vacuous here rather than passed.** `d = 0` means the
`d/N` rule measured nothing on this run. It gives no evidence either way about
whether that rule works, and it is not a validated guard.

Hand-adjudicated, correcting the four scorer failures: hits 39, swaps 1,
**crossed = +0.950**, [+0.850, +1.000]. The single swap survives adjudication.

**Kills.** The ceiling kill at 0.70 **fires**, on the machine number and on the
hand-adjudicated one. `inert_instrument` does not fire. `adjudicated_fraction` is
1 of 40 = 0.025 against 0.25 and does not fire. **`dead_decoy` fires on both
decoys**: F_B 0 of 40 and F_D 0 of 40.

## Two registered validity checks failed

These belong beside the primary and not under it.

**`decoys_are_live`** requires that "each of F_B and F_D must be named at least
once" across both arms. Neither was named once in 40 readings. Checked again
against the raw text: zero F_B or F_D accept phrases appear in any of the 40
`LEVERAGE` blocks.

**`fork_is_real`** puts the minority course at or above 0.15 of control-arm
replies. The pivotal arm came back 20 of 20 `SIGN`, minority share 0.000. The
matched arm split 10 and 10, share 0.500, and passes. The pivotal arm's
recommendation did not fork.

Neither failure touches the crossed primary, which reads the `LEVERAGE` block,
asks a different question, and discriminated cleanly by arm. What they cost is
specific. **This item can no longer say anything about decoy resistance, and the
pivotal arm is not sitting near its recommendation threshold the way the design
assumed.**

One thing the decoy failure does not mean. Searching the full response text
rather than the scored block, F_D accept phrases appear in `BASIS` in 10 of 40
readings and in the free reasoning before the blocks in 14 of 40; F_B appears in
the free reasoning of 2. The decoys were reasoned about and set aside. They were
never chosen as the hinge, which is what `decoys_are_live` reads and what it is
right to read.

## Every secondary, with raw counts

| label | pivotal | matched | pooled |
|---|---|---|---|
| F_A | 16 | 0 | 16 |
| F_E | 1 | 19 | 20 |
| `OFF_LIST` | 3 | 0 | 3 |
| `ADJUDICATE_NO_CLAUSE` | 0 | 1 | 1 |
| total | 20 | 20 | 40 |

P(F_E | matched) = 19/20 = 0.950. P(F_A | pivotal) = 16/20 = 0.800. Off-list
given pivotal 3/20 = 0.150, and 0/20 in the matched arm. `NO_BLOCK` is 0 in both.

The `RECOMMENDATION` block, which the primary does not read: pivotal 20 `SIGN`,
matched 10 `DECLINE` and 10 `SIGN`.

## The adjudicated fraction, and the v6 note's own claim

1 of 40 = **0.025** against a kill of 0.25, split by cause as
`ADJUDICATE_MULTI` 0 and `ADJUDICATE_NO_CLAUSE` 1.

Set that against the 15 of 21 procedure-following phrasings that
[`V6_NOTE.md`](V6_NOTE.md) measured, which is 0.71 against the same 0.25 kill and
is why the skill arm is blocked. This run confirms the other half of the note's
claim: **the dismissal-parsing problem is scoped to the skill arm and does not
touch the control arm.** The block stays where the note put it.

## Predictions, scored

**Prediction 1 was right in direction and right about the kill, and low on the
point estimate.** The registration named crossed primary 0.75 and expected the
kill at 0.70 to fire. Observed 0.850 machine, 0.950 hand-adjudicated. The kill
fires. The registered 0.75 sits at the very bottom edge of the machine interval
and **outside** the hand-adjudicated interval [+0.850, +1.000]. The registration's
"would not be surprised by 0.9" was the better half of the bet, and being right
by hedge is a weaker thing than having predicted it.

**Prediction 4 is partly borne out and stays open.** It registered that at least
one of the three screens would be uninterpretable for a reason that is not the
model. This screen is interpretable for the ceiling question, where the primary
is clean and far outside both bounds, and it is uninterpretable for anything
about decoy resistance, because both decoys came back dead and the pivotal arm
failed `fork_is_real`. Whether the prediction resolves depends on `cascade` and
`council`, neither of which ran here.

Predictions 2 and 3 are about `cascade` and `council` and are untouched.

## What this run cannot conclude

A crossed primary of 0.850 says **this one item is easy for a current model
unaided, in one call.** It does not say the procedure is useless. Nothing here
tests volume, long context, delegation, or work carried across a conversation,
and the failures the six procedures describe mostly do not happen inside a single
call. A ceiling on a one-shot screen is evidence about the venue at least as much
as about the construct.

It is **one item, two arms, twenty readings each**, which makes it a screen and
never an estimate. The interval quoted is over readings of this item and not over
items, and nothing here supports a claim about a population of `hinge` items.

## Files

| file | what |
|---|---|
| `readings.jsonl` | every reading verbatim, with its isolation receipt and usage |
| `plan/` | the 40 laid-out readings as each reader received them, plus the manifest the readers never saw |
| `SCORED.txt` | the scored output, in the registered order |
| `blind_leverage.json` | the 40 `LEVERAGE` blocks, shuffled, arm stripped |
| `adjudicated.txt` | the blind adjudicator's 40 labels |
| `key-h01-v3.json` | the accept lists, bare forms, suppressors and arm map, dumped from `key_h01.py` |
| `H01v3-nettlefold-flour-contract-*.yaml` | the three arms of the instrument, keys and kills included |
| `V6_NOTE.md` | the author's account of version 6: what the v5 review broke, the two derived bounds, and the dismissal-rule measurement that blocks the skill arm |
| `attempts.jsonl` | absent, because no call failed |

**The bytes here are the bytes that ran.** The 82 prompt files and
`blind_leverage.json` carry no trailing newline, because the prompts were sent
without one, and `.pre-commit-config.yaml` scopes `end-of-file-fixer` and
`trailing-whitespace` off `results/` so that stays true. The hook appended a
newline to all 82 in one silent pass while this run was being landed.

The scoring code that produced `SCORED.txt` is not in this directory. It fails
`ruff check` and `ruff format`, and landing it means reformatting it, which would
leave a scorer here that is not the scorer that ran. `key-h01-v3.json` carries
the vocabulary those modules hold, so the labels can be checked by hand from
`blind_leverage.json` without them.
