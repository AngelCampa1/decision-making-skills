# Track H — the `ledger` yield probe, and the ceiling it found on the way

**2026-08-25.** 15 prompts × 3 arms-worth of instances × 2 conditions =
**90 blind `claude -p` calls**, `sonnet`, 0 unparseable, 0 isolation failures.
Code at `f578604`.

**Answer key:** `candidates/` v1, the `set_version: 1` stamped in every candidate
YAML the prompts were cut from.

Prediction: [`notebook/2026-08-25-prediction-the-quality-venue-and-the-tau-rule.md`](../../../notebook/2026-08-25-prediction-the-quality-venue-and-the-tau-rule.md),
committed in `7f175a7`, before any call. The result is written up in
[`notebook/2026-08-25-the-ledger-venue-ceilings-at-ninety-readings.md`](../../../notebook/2026-08-25-the-ledger-venue-ceilings-at-ninety-readings.md).

**These calls did not go through `scripts/run_triggers.py`.** They were
dispatched as sub-agents, so there is no checkpoint, no `total_cost_usd` and no
isolation receipt, and nothing here belongs in `SCORECARD.md`. It is a probe
that decides where the next real run points, and it is filed here because 90
calls with an answer key beside them is a record somebody has to be able to
read, not because it is a published run.

## What was asked

Five `ledger` triplets, authored in parallel across five domains, K = 10 sibling
facts each. The registered kill: **fewer than 3 of 5 surviving blind
re-derivation and an adversarial review means the volume dial does not solve the
yield problem.**

## Two conditions, same fifteen prompts

`g1-verdicts.jsonl` carries the gate's brief: a professional framing, a demand
for step-by-step arithmetic, and an instruction to declare any second defensible
reading. `off-verdicts.jsonl` holds the format contract identical and deletes
all three. Nothing else differs.

The three arms of a triplet were never shown to one reader. The fifteen prompts
were partitioned into three groups holding one arm from each of the five
triplets, so every prompt a reader saw was a different scenario in a different
domain and there was nothing to compare. Blind ids are opaque and shuffled under
seed 20260825, and each group was copied to its own directory so the manifest
was not reachable from where a reader was working.

```
g1-verdicts.jsonl      45 readings  15/15 arms unanimous  15/15 equal to key
off-verdicts.jsonl     45 readings  15/15 arms unanimous  15/15 equal to key
```

Sensitivity 1.000, specificity 1.000, **J = 1.000 in both conditions**. One
reader volunteered one fork, on the arm of the item that was cut for it.

**Three of the fifteen YAMLs no longer match the prompt that was read.** L05's
author repaired its three arms after the readings were taken, so `candidates/blind/`
is the authoritative record of what a reader saw and the L05 YAMLs have moved on.
The values did not change — 14, 26, 14 before and after — but the bytes did, and
the repairs went in the direction that would have made the item *harder*: the
phrase "a fourteen-pump pub" was printing the string 14 in line two of every arm,
where 14 is the correct answer in exactly the two arms it is correct for, and two
same-date count bullets were letting a reader separate the arms by asking whether
an insert named the same beer as the line above it. So L05's three unanimous
readings were taken against a version carrying two leaks that are now gone. That
weakens L05's contribution to the ceiling and does not touch the other four
items' twelve arms. Verify with:

```
python -c "import yaml,json,pathlib; run=pathlib.Path('candidates'); man=json.loads((run/'blind-manifest.json').read_text()); print([(m['triplet'],m['arm']) for b,m in man.items() if yaml.safe_load((run/m['file']).read_text())['prompt'] != (run/'blind'/f'{b}.txt').read_text()])"
```

## What that means, and what it does not

The registered kill is **unaided** J at or above 0.70, and only the second file
reads on it. The first is close to what `ledger` itself instructs, so its 1.000
bounds the treated arm: it says the items are solvable and the keys are right.
An unaided reader given less help could have scored *worse*, which would have
meant more headroom rather than less, which is why the second 45 calls exist.

They came back identical. `ledger` closes on the ceiling kill.

It closes on the yield kill too, independently: L01 and L04 and L05 cut, L02 and
L03 surviving, which is below the 3-of-5 line.

## Why, in the reviewers' words

Three adversarial reviewers, on different items, unable to see each other,
converged on one objection none was asked to look for. One counted effective
ledger width at 1-of-2; one found 3 of 10 siblings doing arithmetic work and 7
inert; one found 6 of 10 written pre-closed by a terminating clause and put
effective K at 3 against an advertised 10.

**Volume buys retrieval load and not decision difficulty.** All ten siblings must
be scanned to find which stage is slowest or which body is the registered
practice. But the rule sentence is single-input and exclusive, so once scanned,
no discrimination is required: the siblings that could matter separate from the
ones that cannot by type, in one pass, with no domain reasoning.

The general form, from the L04 review: **skeleton identity and the same-alarm
requirement are structurally incompatible whenever the swapped proper noun is
the entity the rule sentence selects on, unless resolving that entity requires
work.**

Two reviewers found a leak no gate here can see. `"the tied beer"`, `"her own
practice"` and `"the field it was grown in"` are definite descriptions resolving
to exactly one name, so lexical overlap with the rule sentence reads 0.0 while
referential overlap is 1.0. `scripts/separability.py` is token-based and will
report those items clean.

## Files

| file | what |
|---|---|
| `g1-verdicts.jsonl` | 45 readings under the gate's brief |
| `off-verdicts.jsonl` | 45 readings with the reasoning scaffold deleted |
| `candidates/blind-manifest.json` | each opaque blind id to its triplet, arm, role, unit and keyed value. Never shown to a reader. |
| `candidates/blind/` | the fifteen prompts as the readers received them |

The prompts, the candidate YAMLs carrying the keys, the two gate briefs and the
scorers are in `candidates/` beside this file. They sit inside the run rather
than alongside it because the provenance step reads every directory under
`results/track-h/` as a run, and a staging directory that claims to be one is a
run with no README and no commit in its name.
