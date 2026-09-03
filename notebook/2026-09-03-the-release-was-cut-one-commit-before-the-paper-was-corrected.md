# 2026-09-03 — The release was cut one commit before the paper was corrected

`v1.0.0` went up on 2026-09-02 at 14:27 UTC, tagged at `1589826`, with
`main.pdf` and `arxiv-submission.zip` attached. The three paper defects the
2026-09-01 assessment found were fixed at `30a2dc1`, which landed after that.
So the two assets on the public release are the paper *before* the fix: they
carry the old acceptance claim and none of the three citations
(`webson2022understand`, `min2022demonstrations`, `ma2024promptoptimizers`).

Nobody has downloaded either asset — the API reports `downloadCount` 0 for
both — so the only cost so far is that the artefact was wrong for a day.

## What was done about it

`v1.0.1` at this commit, built from the corrected source, and `v1.0.0` left
exactly as it is. Overwriting the older release's assets was the other option
and is worse: the tag would still point at `1589826` while the files beside it
came from a different tree, and the record of what was actually published on
2026-09-02 would be gone. A release is dated evidence like anything else in
`notebook/`.

The title page, `README.md`, `CITATION.cff` and the arXiv `Comments` field in
[`paper/SUBMISSION.md`](../paper/SUBMISSION.md) now all name `v1.0.1`. The
paper points at a tag rather than a DOI, so nothing here waits on Zenodo.

## Why it happened

The plan for the day said Step 0 (fix the paper) came before Step 1 (tag and
release) *because* the release attaches the PDF. Both steps ran. The release
ran against the commit that was on `main` when the release command was typed,
not against the commit the fix landed on, and no gate reads a release. The
provenance gate covers `results/`, the claims register covers figures in
documentation, and the drift gate covers documents. An attached binary on
GitHub is outside all three.

Nothing has been added to the gate for this. The check would have to hold a
GitHub API token and reach the network, which `de check` deliberately does not
do — it runs offline and deterministically, and that is worth more than
catching this one class of mistake. The rule is procedural instead: cut the
release last, after the gate is green on the commit you are tagging, and read
back what the assets were built from.

## Where the programme is

Not paused. The re-run registered on 2026-09-02 has not started collecting:
the first 42 calls found 6 records whose response was empty because the model
hit the 4,096-token output cap mid-reasoning, four of them in one arm, and a
truncated answer that no record can distinguish from a refusal is an arm
losing on output budget rather than on judgement. The study is stopped at 0.3%
until every zero is auditable. Two searches are frozen and committed with
their winners, and those are the artefacts the re-run needs.
