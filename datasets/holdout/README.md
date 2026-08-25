# The private holdout

**Audience:** an agent or reader who followed a refusal message here.

This directory is where the `confirm` arena's split lives, and it is empty.

## Why it is empty

`.gitignore` excludes `datasets/holdout/*.jsonl` and will keep excluding it until
a verdict publishes. The split is the only uncontaminated data this repository
has, and contamination cannot be undone within a seed, so a copy in the tree is
a copy that has been read.

Nothing has been built here yet either. Every call on record is a `screen`-tier
trigger measurement on the public split, `SCORECARD.md` is empty, and
`decision-making` and all six procedures carry `verdict: UNTESTED`.

## The records are JSONL, and that is load-bearing

One line per item, in `*.jsonl` files directly under this directory. Three
things agree on that pattern and all three break together if one moves: the
`.gitignore` rule above, `cli.HOLDOUT_GLOB`, which is how `de confirm` decides
whether a split exists, and this sentence.

A split written to any other extension would be invisible to `de confirm`, which
would report no holdout while one sat here, **and** untracked by the ignore rule,
which would put the one file in this repository that may never be committed into
the next `git add`. The public corpus under `datasets/triggers/decision-making/`
is YAML; the holdout takes its item construction and not its serialisation.

## What reads it

`de confirm` checks a pre-registration against the repository, finds no split
here, prints the reason and exits without making a call. The locks it runs first
are `decision_evals.prereg`, and the six refusals are described in
`docs/PROTOCOL.md` section 3b.

`decision_evals.arenas` holds the separation as data. `ARENAS` records that
`confirm` runs on the holdout and `dev` and `screen` run on the public split, and
`assert_split_allowed` refuses a run against the wrong one. **That function has
no caller outside its tests**, which makes it a rule written down rather than a
rule enforced, in the same state `decision_evals.prereg` was in until
2026-08-24. `arenas.py` says the same thing about its own registry: the arena
check fires where a caller asks for it. The caller that would make this
structural is the confirmation runner, which does not exist.

## What building it would take

A corpus using the same item construction as
`datasets/triggers/decision-making/`, drawn so no item in it appears in the
public split, serialised as JSONL, generated from a passphrase-derived seed so it
can be rebuilt from something that is not in the tree. It goes through the same
shortcut battery and the same three-judge blind adjudication as the public corpus
before any number is computed against it, and the pre-registration that governs
the run is committed before the first call.
