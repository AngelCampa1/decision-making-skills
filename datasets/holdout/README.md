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

## What reads it

`de confirm` checks a pre-registration against the repository, finds no split
here, prints the reason and exits without making a call. The locks it runs first
are `decision_evals.prereg`, and the six refusals are described in
`docs/PROTOCOL.md` section 3b.

`decision_evals.arenas` is what makes the separation structural:
`assert_split_allowed` refuses a `screen` run against the holdout and a
`confirm` run against the public split, so spending this split on a screening
run is an error rather than a matter of discipline.

## What building it would take

A corpus of the same construction as `datasets/triggers/decision-making/`, drawn
so no item in it appears in the public split, generated from a passphrase-derived
seed so it can be rebuilt from something that is not in the tree. It goes through
the same shortcut battery and the same three-judge blind adjudication as the
public corpus before any number is computed against it, and the pre-registration
that governs the run is committed before the first call.
