# 2026-08-24 — The confirm pathway has a caller, and it still refuses

`decision_evals.prereg` implemented six refusals at a 100% line-and-branch
coverage floor and nothing in this repository imported it. `de confirm` now does,
by static import from the console script, so `[tool.decision-evals.unwired]` is
empty and `de check`'s integrity wiring step is what keeps it that way.

The command stops before making a call. It loads the pre-registration, gathers
the commit facts, runs all six refusals, and then says that the `confirm` arena
reads the private holdout and there is no holdout on disk. That is the correct
end state today. No holdout was fabricated to get past a gate this repository
wrote to stop exactly that.

This entry records the two choices the work made, because standing rule 1 says a
parameter that is not derived is a choice and has to be written down as one.

## Choice 1: `precedes_results` is scoped to confirmation runs

`prereg.RepoState.precedes_results` is documented as "its commit predates
everything already in `results/<skill>/`". Gathered literally, it is `False` for
`decision-making` and for every other skill this repository has measured, because
`results/decision-making/` has held twelve published screening runs since
2026-08-12. A gate in that state can never pass, and standing rule 2 says a
falsifier must be run against a known-good case before it may fail anything.

So `cli._gather_repo_state` counts only runs that declare a pre-registration,
read off a `**Pre-registration:**` line in the run's README.
`cli.confirmation_runs` is that reader, and against the real record today it
returns an empty list, which `tests/unit/test_confirm.py` asserts without
monkeypatching anything.

**The argument that this is not a weakening.** The screen/confirm split exists so
that screening precedes a confirmation and informs it: the two stages use
disjoint items, the screening result never enters the final p-value, and it only
decides whether to spend. `docs/PROTOCOL.md` section 3b has said so since it was
written. A pre-registration written after a screening run is the intended order,
and the postdiction the refusal is aimed at is a second pre-registration written
after a confirmation run has already reported.

**What could make this wrong.** A confirmation run that publishes without the
`**Pre-registration:**` line would be invisible to `confirmation_runs`, and the
next pre-registration would pass a check it should fail. Nothing gates that line
today. The obvious close is a provenance rule requiring it of any run whose
model resolves to the `confirm` arena, which is worth building alongside the
confirmation runner rather than before it.

## Choice 2: `p_discordant = 0.20` in the first pre-registration

`preregistration/decision-making-v1.yaml` carries
`minimum_detectable_effect: 0.086`, which is
`stats.minimum_detectable_effect(330, 0.20, alpha=0.05, power=0.80,
design_effect=2.0)`. Everything in that call is derived except the discordance.

- `330` is the item count of the version 4 public corpus, counted off
  `datasets/triggers/decision-making/` as 90 + 90 + 81 + 69. The holdout is
  specified to the same size and construction.
- `2.0` is the design effect in `docs/PROTOCOL.md` section 4.
- `0.05` and `0.80` are the alpha and power the protocol uses throughout.
- **`0.20` is a choice.** Nothing on disk measures the discordance between the
  full description and the opener-ablated one. What would measure it is a
  screening run of those two arms against each other, paired per case id, which
  is a run this repository can afford and has not made. `de power` prints the
  whole sweep from 0.15 to 0.50, so a reader who disagrees can price another
  column: at 0.15 the MDE is 7.4pp and at 0.30 it is 10.5pp.

The budget is derived rather than chosen. `budget.estimate_cost_usd` over the
longest prompt this instrument sends, the 635-character shipped description plus
the 8,363-character longest turn in the corpus, gives $0.00562375 per item, and
`project_cost(330, 2, 2, 0.00562375)` gives $7.42335 against a pre-registered
$7.43. That estimator over-counts by design, so the projection is a ceiling.

## A prediction, for the record

When the holdout is built and this pre-registration runs, the difficulty band
will refuse it. Published screening recall on the trigger corpus sits at or near
1.0 on several arms, and `[0.35, 0.75]` exists to stop a run with no headroom to
measure. If that happens it is the band working rather than the band being
wrong, and the right response is a v2 pre-registration on a harder split rather
than a wider band.

## Also in this change

`evals/src/decision_evals/arenas.py` joined the decision register's governed
paths. It is the one governed path that is source rather than data, and the
reason is in `docs/DECISIONS.md`: `MODELS` decides which runs may become
evidence, and moving a row between arenas is invisible in every artefact the
other gates read.

`de screen` landed beside `de confirm` as a pass-through to
`scripts/run_triggers.py`. It reimplements nothing; the runner's parser is still
the only parser.
