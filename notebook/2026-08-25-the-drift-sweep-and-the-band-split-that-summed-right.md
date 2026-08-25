# The drift sweep, and the band split that summed right

**2026-08-25.** The fortieth row landed in [`docs/RUN_INDEX.md`](../docs/RUN_INDEX.md)
and [`docs/STATUS.md`](../docs/STATUS.md) reached ten commits past its recorded
review, which is the exact point `de check` starts refusing. So this is the
every-third-run sweep of `README.md` and `docs/`, run against the eight documents
`de drift` named plus four more that its ranking put just under the line.

## How it was read

Each document was read against `git log <its review sha>..HEAD` over the paths it
names, by a sub-agent briefed to find claims that are no longer true rather than
prose it would have written differently. Every finding was then re-derived from
the source before anything was edited: a line number checked in the file, a count
recomputed off the corpus, a guard read in `trigger_arms.py`. Two reports named a
number I could not reproduce and those went in as "checked and sound" rather than
as edits. The `[tool.decision-evals.reviewed]` entries below record thirteen
documents at `2ada1a3` on that basis, and the basis is written down here so a
reader can weigh it rather than take it.

## The one finding worth the sweep

**The corpus band split has been wrong since 2026-08-20 and it sums to the right
total, which is why nothing caught it.** Counted off
`datasets/triggers/decision-making/{s,m,l,xl}.yaml`: 90, 90, 81, 69 items, so
s 30, m 30, l 27, xl 23 triples. Two living documents publish **l 28, xl 22**.

The arithmetic that settles it was sitting in the same paragraph the whole time.
Version 4 stood at s 24, m 24, l 21, xl 17, and version 5 added six triples to
every band, three routing to `council` and three to `hinge`. That gives 27 and 23
and cannot give 28 and 22.

Nothing derived from the totals moves: 110 triples and 330 items are right, so
the call counts, the movement rates and the adjudication denominators all stand.
What is instructive is the shape of the miss. A hand-maintained breakdown whose
total is correct is invisible to every check here — the trigger-set gate reads
structure and not prose, the claims register holds no band split, and a reader
sanity-checking the line adds four numbers, gets 110, and stops. It went in
`STATUS.md` as an appended correction and in
[`programme/part-3-the-instrument.md`](../docs/programme/part-3-the-instrument.md)
in place.

## Family A closing was the other half of the sweep

The quality track closed Family A the same morning, so several documents were
still describing a venue that had shut. Four of them said so in the present
tense:

- **`STATUS.md`'s Tracks table** had Track H as *"H1 authoring under way … registered kill did not fire"*. Both registered kills fired.
- **`programme/part-7-cross-cutting.md`** carried the structural argument that *"the mechanism that closed the other four therefore cannot ceiling this one by construction"*. That is the prediction Family A falsified, and it stays as written with what happened appended under it: the elicited quantity carries an answer key of its own, so reading that key is a verifier-backed accuracy in exactly the sense the four venues were, and the two stop being independent at the top. The hedge in the same paragraph — that a *different* mechanism could still ceiling it — held. The candidate the hedge named was wrong.
- **`docs/TAILORING_CORPUS_SPEC.md`** said *"no Track H item has ever been sent to a model"* and addressed itself to a second author writing triplets 4 to 20. Ninety-nine were sent on 2026-08-25 and those readings are what closed the venue.
- **`README.md`** said every number on record measures firing. The 99 readings do not.

## The runner is no longer behind every call

`scripts/run_triggers.py` is described in five places as the runner behind
*every model call on record*. Track H's 99 readings were dispatched as sub-agents
and both run records say so in their own first paragraphs. All five now say
*every trigger call*, and the distinguishing property — no checkpoint, no
`total_cost_usd`, nothing for `SCORECARD.md` — is stated where it matters.

Those 99 calls were also missing from `STATUS.md`'s **Model calls on record**
table, which counts calls made rather than calls that produced a usable number.
That is the 2026-08-13 omission repeating almost exactly: a run measuring the
instrument rather than the skill never passes through the reporting path that
puts a family in the table. Appended, with the count taken by line from the three
`.jsonl` files, and the running total goes ~12,474 → ~12,573.
`site/claims.json` refused the old figure on the next gate run, which is the
published-claims check doing precisely its job.

## Six other things had gone stale

- **The pre-registration lock has fired twice** and three documents still called it never-run and declared unwired. `[tool.decision-evals.unwired]` has been empty since `de confirm` reached `prereg` by static import. What has never run is the `confirm` arena, which still refuses for want of a holdout — that hedge is load-bearing and survived every edit.
- **`docs/WHY_THESE_RULES.md`** said the live answer key is at v5. It is at v6, and has been since `3524594` — which predates that document's last recorded review, so this is drift a review missed rather than drift a review could not have seen.
- **`README.md` said thirteen published runs.** The provenance gate counts sixteen.
- **Two backlog rows in `docs/AUTONOMOUS_WORK_ORDER.md` were finished work advertised as open** — the `stream-json` fold and the A1–A5 MDE — and in both cases the programme had said so first. The MDE row's own done-when condition named a phrase (`"sized from the MDE"`) that now appears nowhere in `docs/` except that row.
- **`docs/METHODS.md` attributed a quotation to `AGENTS.md`** that lives in `CONTRIBUTING.md`.
- **Six code citations in `programme/part-3-the-instrument.md` pointed at moved lines**, and one described a mechanism that no longer exists: `ask()` now reaches `run_isolated` rather than opening a `Conversation` itself, and the `--in-situ` flag the row says does not exist has been there since N9.

## What was sound

`CONTRIBUTING.md` is entirely sound and needed a review recorded and nothing
else. So is `programme/part-1-what-is-already-known.md`. `docs/ARCHITECTURE.md`
had one finding, and all four of its generated regions match their sources
exactly. `docs/AUTONOMOUS_WORK_ORDER.md`'s eleven-step landing sequence, every
CLI invocation in it, and every URL in its step-10 table check out. No document
had drifted into the present tense about a gate scoped to an arena that has never
run — the one rule this sweep was told to hunt hardest turned up nothing, which
is worth recording as a rule that is being followed.

## Left open

- **`docs/AUTONOMOUS_WORK_ORDER.md` over-specifies `pre-commit install --hook-type pre-push`.** `default_install_hook_types` in `.pre-commit-config.yaml` has covered both stages since the first commit. The same over-specified claim sits in `.pre-commit-config.yaml` and `.github/workflows/check.yml`, and the workflow comment cites this document as its source. Fixing one of three leaves the repository disagreeing with itself, so all three should land together and none did here.
- **`docs/STATUS.md`'s defect table cites `run_triggers.py:918`**, which now points at `report_negative_kinds`. It is a dated record of a defect found and fixed on 2026-08-19 and the fix is named in the same row, so the line number was left alone rather than retrofitted.
- **`docs/METHODS.md` §7 says the baseline pattern "appears seven times across the production modules."** More than seven may-only-shrink registers exist today. None of those files moved in the window and I could not establish what the correct count was when it was written, so no value was asserted. It is a hand-maintained count worth deriving.
- **`AGENTS.md`'s "Before any run" section does not mention the analysis lock**, which has now refused twice on ordinary refactoring. That is a missing rule rather than a false statement, and adding a standing rule is not a drift fix.
- **Four documents stay unread**: `DOCUMENTATION_MAP.md`, `PROTOCOL.md`, `VOICE.md` and `reviews/HOUSE_STYLE.md`, each one commit behind and none near the ceiling. No review was recorded for them, because none was done.
