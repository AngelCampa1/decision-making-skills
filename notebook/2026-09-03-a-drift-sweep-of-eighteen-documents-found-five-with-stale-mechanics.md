# A drift sweep of eighteen documents found five with stale mechanics

**2026-09-03.** The standing obligation in `AGENTS.md` — sweep every third
published run, and whenever `de drift` names a worklist — was at the refusal
boundary: `AGENTS.md`, `CONTRIBUTING.md`, `docs/ARCHITECTURE.md` and
`docs/AUTONOMOUS_WORK_ORDER.md` each sat at exactly ten commits past their
recorded review, the ceiling `de check` refuses past. `de drift` named
eighteen documents in all, furthest behind first. Each was read in full
against the files it names as having moved, not rubber-stamped.

## Method

For each document, `git log <reviewed-sha>..HEAD -- <dependency paths>`
isolated which of its named files actually changed, then the diff of each was
read against the document's own prose. Most of the worklist's apparent
staleness was `site/build-manifest.json` and `site/inputs.json` noise — both
regenerate on nearly every commit that touches a rendered document, and
neither carries content a document's prose could contradict. The real
dependency changes clustered in five places: `paper/refs.bib` (verification
annotations added, no existing quote or number changed — checked and found
not to be drift), `providers/claude_code.py`, `solvers/arms.py`, `runner.py` /
`evolution/study.py`, `providers/openai_compatible.py`, and `.gitignore`.

## What was wrong

**`docs/METHODS.md` and `docs/HARNESS_DISCLOSURE.md`** both said, in the
present tense, that arms run in blocks because `runner.iter_items` is never
called. That was true of the published five-arm study and is still true of
`iter_items` itself, but `evolution/study.py` was rewritten on 2026-09-02
(commit `80ab63b`) to schedule `de study` and `de evolve` calls in chunks
through `run_arm`, reaching the same interleaved ordering `iter_items` was
built for without ever calling it. Both documents now say both things: blocks
for the published study, chunked interleaving since.

**`docs/programme/part-3-the-instrument.md`** cited six line numbers in
`providers/claude_code.py` and `solvers/arms.py` for a proposed N9 mechanism.
Commit `c7b39eb` added an `_answering_model` helper ahead of `Conversation`,
shifting three of those citations by 52 lines (`Conversation` 603→655,
`Conversation.__init__` 633→685, `run_isolated` 756→808). Separately,
`solvers/arms.py` gained a sixth arm, `candidate`, after `in_situ` (commit
`47a6b71`, for the evolution work), so the document's claim that `in_situ` is
"a fifth named arm... deliberately ordered last" is now wrong on the count and
the ordering, and its quoted sentence no longer matches the module comment,
which was rewritten for the new arm. Fixed the six line numbers and the
arm-count/ordering claim, and requoted the current comment.

**`docs/WHAT_WE_FOUND.md`** said the two 2026-08-27 evolution searches wrote
into `results/evolution/`, "which `.gitignore` excludes" — present tense.
`.gitignore` no longer excludes that directory outright: the same
`evolution/study.py` commit re-included `winner.md`, `winner.json`,
`lineage.jsonl`, `run.json` and `search.log` per search directory. The lost
bodies are still lost — the rule changed after those two directories were
already gone — so the finding stands, but the present-tense clause was wrong.
Reworded to past tense with the current rule stated alongside it.

**`docs/PROTOCOL.md`** said of the `openai_compatible.py` backend, added
2026-08-19, "Nothing has been measured on it yet." The five-arm evolution
study ran 4,368 calls through exactly this backend on 2026-08-27. Added the
measurement and its `dev`-tier scope.

## What was checked and found correct

`AGENTS.md`, `CONTRIBUTING.md`, `docs/ARCHITECTURE.md`,
`docs/AUTONOMOUS_WORK_ORDER.md`, `docs/STATUS.md`, `docs/WHY_THESE_RULES.md`,
`docs/VOICE.md`, `docs/DECISION_FRAMEWORKS.md`,
`docs/programme/part-1-what-is-already-known.md`,
`docs/programme/part-2-the-product.md`,
`docs/superpowers/drafts/s9-ledger-replacement/README.md`,
`docs/programme/part-7-cross-cutting.md`, and `docs/RELATED_WORK.md`.

`docs/STATUS.md` is the largest of these and is hand-maintained and
append-only by rule; nothing in its 1,215 lines asserts an ongoing mechanism
that the recent changes falsify, and its most recent correction (2026-09-01,
the control-token scorer fix) already covers the most relevant recent change.
Nothing was appended to it: the newer commits in this sweep (`credentials.py`,
the study's chunking, the provenance twin-arm fix, the 429/529 mapping) are
gate and harness fixes, not published runs, so the standing obligation to
update `STATUS.md` alongside a published run does not apply to them.

`docs/RELATED_WORK.md` had already been corrected by commit `eacdde6`, which
edited the document and moved its own review pin — but to the parent commit
`2c4265f` rather than to `eacdde6` itself, so `de drift` still read it as one
commit behind. Content was re-verified against `paper/refs.bib` and found
current; only the pin needed moving.

`docs/ARCHITECTURE.md`'s generated regions (`de:generated harness-modules` and
`de:generated de-check-steps`) were already current, including the newer
`credentials` module and `candidate` arm, because a prior commit had run
`de sync`.

## What was not checked

`paper/sections/method.tex` changed twice in this window (commits `f686981`,
`1589826`, `02f9fb8`), but it is described in `docs/METHODS.md` as rendering
*from* the doc rather than the other way around, and the diff was prose
tightening plus the same control-token and provenance corrections already
covered above — no direction of drift from doc to paper.

## Housekeeping

`[tool.decision-evals.reviewed]` in `pyproject.toml` now pins all eighteen
documents to `30a2dc1`, the commit this sweep read them at (before its own
fixes landed). `docs/README.md` was re-read as the index per the standing
obligation and found to list all eighteen correctly.
