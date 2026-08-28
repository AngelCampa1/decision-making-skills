# Main was red in CI for three commits and the local gate could not see it

**2026-08-28.** Three commits landed on `main` today with a green local `de
check` and a red `check` workflow: `5ce35f5`, `9827501` and `c263b3e`. One step
failed in all three, `documentation`, and the local gate is structurally unable
to fail it for the same reason.

`AUTONOMOUS_WORK_ORDER.md` already says CI checks a commit while a hook checks a
working directory, and gives the first red run as the measurement. This is the
second, and the mechanism is worth having written down because the same shape
will recur.

## The failure

`docs/LIMITATIONS.md` and `docs/STATUS.md` both name `results/evolution/`, and
both do so to make the point that `.gitignore` excludes it and the two evolution
winners are gone. The path resolves on this machine, because an empty
`results/evolution/` survived the searches that wrote into it. It cannot resolve
on a clean clone. `check_path_references` was right both times: right to pass
here and right to refuse there.

`c263b3e` then added two more of the same shape. Its `docs/STATUS.md` entry
named `paper/figures/accuracy.tex` and `paper/figures/signal.tex`, which
`de figures` writes and `paper/.gitignore` excludes.

`results/evolution/` is declared in `[tool.decision-evals.docs-ignored-paths]`
now, which is the case that register exists for: there is nothing left to
commit, so the `git add -f` the register itself recommends is not available. The
two figure paths are not declared. The sentence was rewritten to stop naming
them, because a reader learns nothing from two filenames that nobody will ever
have, and two more register entries to carry that is a bad trade.

## Reproducing CI locally in about ten seconds

The gate cannot be trusted to catch this class in a working directory, and
waiting five minutes for a CI run to say so is the slow loop. Exporting the
commit and checking that instead is the fast one:

    git archive HEAD | tar -x -C <tmp>
    mkdir -p <tmp>/.venv/Scripts

Then call `check_docs` against `<tmp>`. The first line is the whole idea: a
clean tree holds what the commit holds and nothing a run left behind.

The second line is not optional and cost a wrong answer before it was added.
`check_path_references` builds its set of repository-rooted prefixes from the
directories that exist, so with no `.venv/` on disk it does not recognise
`.venv/Scripts/de.exe` as a path at all, and then reports the register entry
naming it as dead. The CI job runs `uv sync` before the gate, so `.venv/` is
there. Without the `mkdir` the simulation invents a fifth issue that CI does not
have, and an unexplained disagreement with the arena you are simulating is worth
exactly nothing.

With the `mkdir`, the simulation reported four issues against `c263b3e` and CI
reported the same four in the same order. After the fix it reports none.

## What this does not fix

Nothing runs that simulation automatically. It is a thing to reach for when a
change adds a path reference to a living document, which is the trigger, and
`de check` still will not refuse the case in a working directory. Wiring it into
the gate as a step is the obvious next move and is not made here: the export is
cheap but not free, the gate is already the slowest thing in the loop, and this
is one class of failure rather than a general answer to "CI sees more".
