# Writing the paper found three things the documents had wrong

**2026-08-28.** The documents were retargeted onto the study that ran and the
paper was written against them. Doing it in that order turned the paper into an
audit, because a section written from the code disagrees with a document written
from the intention, and the disagreement is visible.

This is the drift sweep the standing obligation asks for, landed as an entry
rather than as a commit body.

## `de figures` did not exist, and had been called for eighteen days

`paper/Makefile` called `de figures` and `paper/main.tex` declared that every
number in the prose comes from what it writes. Neither was true. The Makefile
also named `results/**/summary.json`, a file that has never existed anywhere
under `results/`.

Nothing caught it because the documentation gate scans root `*.md` and `docs/`
recursively, and `paper/` is neither. The one artefact that leaves the
repository was the only prose no gate reads.

It exists now, as `evals/src/decision_evals/figures.py` behind `de figures`,
with the decomposition split out into `stats/signal.py` so the notebook and the
paper compute informedness through one function. Both carry the 100/100 line and
branch floor that `stats/` already had, because a wrong branch here is a wrong
number in a PDF that has left the building.

Building it surfaced two bugs of its own, both of the shape this repository
keeps finding. Reading each record's `arm` field merged the two evolved winners
into one arm, because both carry kind `candidate` and are told apart only by
their body hash; the arm is now read off the file name. Keying items on
`item_id` counted 52 items in a 728-item study, because `item_id` does not
encode the seed and three seeds of one template collapse under it. Both produced
a clean run and a plausible number.

## Three claims that were false

**Arms ran in blocks, not interleaved.** `runner.iter_items` returns item-major
pairs so that arms alternate, and nothing outside the tests calls it.
`evolution/study.py` loops arm-major: every item of `off`, then every item of
`on`, and so on. So the five-arm study confounded each arm with whatever drifted
between blocks, and `HARNESS_DISCLOSURE.md` said the opposite.

What bounds it is a measurement rather than an argument. The A/A pass ran after
all five arms, 1,456 calls after the placebo pass it duplicates, and returned
728 of 728 identical. On a local server with no quota and no served-model churn,
across a third of the run, the drift a block design is exposed to did not occur.
That is worth reporting and it is not a defence of the design. Wiring the helper
in changes how a run is scheduled and belongs in its own commit.

**The two evolved skill bodies are gone.** Both searches wrote into
`results/evolution/`, which `.gitignore` excludes, so nothing they produced was
ever committed, and the directories no longer exist. A content-hash search of
every file on this machine under 300 KB, 40,936 of them, found neither body.
What survives is the SHA-256 on all 728 records of each arm. The study can prove
one fixed body produced each arm; nobody can obtain that body, including us.

The paper's appendix had said all five bodies were published and that the two
winners sat beside the records. The seed skill and the placebo do recompute to
the hashes in `run.json`, checked today. The other two cannot be checked by
anyone.

**Residency is pinned and not recorded.** `keep_alive: 60m` is a default in the
provider that builds the request, sent on every call, and no caller overrides
it. It is not in `run.json` and not on any record. Two documents and the paper
said it was recorded per pass. Temperature is in the same position. A replicator
reads both from the source.

## Two citations that overstated their sources

`refs.bib` carried eleven `% VERIFY` markers: an arXiv id and a title recorded
during the literature sweep, with an author list nobody had checked. All eleven
were read against arXiv's own metadata today and cleared. Eight had no author
list at all. Four had a title that did not match the paper at the id beside it,
and one of those four carried a different paper's title entirely: `smece2026`
was recorded as "Debiased Kernel-Smoothed Estimation of Calibration Error", and
arXiv:2603.14092 is "Soft Mean Expected Calibration Error (SMECE)".

Two entries also carry notes warning how their numbers may be quoted, and the
paper was violating both. SkillsBench's granularity effect is +0.7 on one model
and −6.7 on the other, and the note says the second must travel with the first;
the introduction gave only the +0.7. SkillOpt's +23.5 is GPT-5.5 in direct chat,
and the note says quoting it alone is defensible only if the harness is named;
three sections quoted it bare, and one of them attributed it to the CLI
harnesses, which is where the paper's own citation says +24.8 and +19.1. All
corrected. `related_work.tex` also gave SkillsBench's scale as "86 tasks across
11 domains", the exact figure its `refs.bib` note was written to retract.

A bibliography that records why a number is fragile only helps if somebody reads
it before writing the sentence.

## What the call ledger actually is

`STATUS.md` had not moved since 2026-08-25 and was short by about 6,600 calls.
Counted by line from the study's own `.jsonl` files, from the committed ceiling
screen, and from scratchpad JSON that survived, the new total is about 19,940.

Two searches are permanently uncountable for the same reason their bodies are
gone. That is recorded as a floor rather than rounded up.

## Prediction

None. Nothing here ran a model. Every figure above is read off committed records
or off the source, and the two that are not, the disk scan and the arXiv
metadata, are reproducible by rerunning them.

## What this leaves open

The paper is complete and unsubmitted. `paper/CHECKLIST.md` carries the open
boxes honestly, including three that need someone outside this repository: an
arXiv endorsement, a Zenodo DOI, and a TeX toolchain, which this machine does
not have, so the PDF has never been compiled. What has been checked without one
is that every `\input` resolves, every label a reference names is defined, every
citation key is in `refs.bib`, every environment balances, and every macro the
prose uses is one `de figures` writes.
