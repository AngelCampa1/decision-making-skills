# A drift sweep of five documents following the prompt constant ablation probe

**2026-09-10.** The standing obligation in `AGENTS.md` — sweep every third
published run, and whenever `de drift` names a worklist — was approached:
`AGENTS.md`, `CONTRIBUTING.md`, `docs/ARCHITECTURE.md`, and
`docs/AUTONOMOUS_WORK_ORDER.md` each sat at eight commits past their recorded
review (`3d7975d`), near the ten-commit refusal boundary enforced by `de check`.
`de drift` named five documents in all. Each was read in full against the files
it names as having moved.

## Method

For each document on the worklist, commits between `3d7975d` and `HEAD`
(`54600da` through `902eb81`) were checked for relevant changes:
- Completion and incorporation of the 14,700-call seven-arm evolution study
  (`results/evolution-study/2026-09-03-e235b98-seven-unseen-v2/`).
- Authoring and execution of the 784-call paired prompt constant ablation probe
  (`results/evolution/2026-09-10-prompt-constant-ablation/`).
- Manuscript updates in `paper/sections/results.tex`, `discussion.tex`,
  `appendix_prompts.tex`, `main.tex`, and `CHECKLIST.md`.
- Status tracking appended in `docs/STATUS.md`.

## What was checked and found correct

1. **`AGENTS.md`** and **`CONTRIBUTING.md`**: Core development guidelines,
   gate invocations (`uv run de check`), research rules, and standing
   obligations remain strictly accurate and fully enforced.
2. **`docs/ARCHITECTURE.md`**: Module maps, pipeline flows, and gate steps
   remain current.
3. **`docs/AUTONOMOUS_WORK_ORDER.md`**: Five standing rules, sub-agent review
   protocols, worktree procedures, and landing order remain operative.
4. **`docs/METHODS.md`**: Statistical methods, dual-bar criteria (Holm $q < 0.05$
   and template cluster sign-flip $p < 0.0167$), and data integrity checks
   remain fully aligned with the 14,700-call study and ablation probes.

## Review pins updated

Updated `[tool.decision-evals.reviewed]` in `pyproject.toml` to baseline all
five documents at `902eb81`, resetting the drift counter to 0.
