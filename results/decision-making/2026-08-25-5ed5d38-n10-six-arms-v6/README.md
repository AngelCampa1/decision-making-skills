# Track N10 — the six description arms, rebuilt on answer key v6

**2026-08-25.** 6 arms × 330 items × 2 repeats = **3,960 published `claude -p`
calls**, `haiku`, **0 unparseable in the published set**, 0 isolation failures.
Code at `5ed5d38`.

**Answer key:** `datasets/triggers/decision-making/index.yaml` v6

Prediction: [`notebook/2026-08-24-prediction-n10-the-six-description-arms-on-v6.md`](../../../notebook/2026-08-24-prediction-n10-the-six-description-arms-on-v6.md),
committed before the launch. Two of its six predictions were found unlicensed
before any of them were scored, recorded in
[`notebook/2026-08-24-n10-addendum-two-of-six-predictions-were-never-licensed.md`](../../../notebook/2026-08-24-n10-addendum-two-of-six-predictions-were-never-licensed.md).

Every published trigger number before this run was scored at v4 or earlier: M4,
L5, M5 and M6/M6b at v1, L7 at v2, and N5, N6, N7 and N9 at v4. The v4 items are
carried forward inside v6 rather than gone, and
`label_versions_comparable` refuses the comparison on the version integer, so
none of those numbers describes this key. This run is the baseline a later arm
on v6 will be scored against.

## How these calls were collected, which is not uniform across the arms

**At least 4,003 calls were made and 3,960 are published.** The `no-opener` arm
first completed carrying 43 contiguous null rows, every one reading `the CLI
stream ended without a result on turn 1; the process died mid-turn`. The
contiguity identified one infrastructure window rather than model behaviour.
Those 43 rows were deleted and the same `(case, repeat)` cells re-run. All 43
refills fired `True`, and the same 43 cases at repeat 0, which were never
touched, also fired `True`. No surviving verdict changed.

**Two arms were collected alone and four under sixteen-way process
concurrency.** `full` and `no-opener` ran as whole-corpus single processes.
`no-exclusions`, `opener-only`, `stakes-named` and `stakes-shown` ran as sixteen
concurrent `(arm, band)` processes across four worktrees pinned to the same
commit. So arm is confounded with collection load, and the four concurrent arms
sit higher on FPR at every band.

Two things cut against reading that as a load effect. `stakes-shown` was
collected concurrently and sits at FPR 0.1136, below single-process `full` at
0.1432. And load fell over the window, from sixteen processes to four for the
`xl` tail, while the gap between the two groups is widest at `xl`. The confound
cannot be resolved from this record, and prediction 5 names two arms that are
both in the concurrent group.

`run_triggers.py` collects serially and knows nothing about this. The
concurrency was introduced at the OS-process level, outside anything the code
can see or refuse, and `runner.py`'s `CONCURRENCY_UNSAFE` register says this
backend is unmeasured for concurrency rather than safe.

| arm | accuracy | recall | FPR | collected |
|---|---|---|---|---|
| `no-opener` | **0.9439** | 0.9955 | **0.0818** | alone |
| `stakes-shown` | 0.9242 | **1.0000** | 0.1136 | 16-way |
| `full` | 0.9015 | 0.9909 | 0.1432 | alone |
| `stakes-named` | 0.8727 | 0.9955 | 0.1886 | 16-way |
| `no-exclusions` | 0.7970 | 0.9909 | 0.3000 | 16-way |
| `opener-only` | 0.7955 | 0.9818 | 0.2977 | 16-way |

No cross-version accuracy, recall or FPR comparison against N6 or N7 appears
here. Six arms compared pairwise is fifteen comparisons and this run registered
no multiplicity control, so no p-value is offered on the ordering.

## What the opener does, and what it does not do

`preregistration/decision-making-v2.yaml` registers that **on the private
holdout**, the shipped description fires on decision turns more often than the
same description with its trigger-phrase opener removed, **by at least 0.086**.

On the public corpus the recall difference is 0.0046 and runs the other way,
which is far inside that bound. Paired on all 220 positive rows it is **one
discordant call**: `no-opener` fires where `full` misses once, `full` fires
where `no-opener` misses never. Exact McNemar p = 1.0000. On the registered
metric these two arms separate by nothing at all, and the reported recalls of
0.9909 and 0.9955 are two misses against one.

What does separate is the false-positive rate. `full` 0.1432 against
`no-opener` 0.0818 is a 42.9% reduction, 57 discordant negatives split 42 to 15,
exact McNemar p = 0.0005. That is a real difference and it is not the registered
metric.

So the run says the opener buys no detectable recall and costs false positives.
It does not falsify the hypothesis. The hypothesis is registered against a
private holdout that does not exist yet, this is the screen tier, and the recall
comparison here has one discordant call in it. A v3 pre-registration or a change
to the description would have to start from the false-positive result rather
than from this recall comparison.

The screen arena changed what the confirm arena should be registered against,
before that arena was built. That ordering is the arena split working. It is not
a cost saving: the confirm run is registered at 1,320 calls and this screen run
made 3,960.

## The four licensed predictions: one held, two failed, one split

| # | registered | outcome |
|---|---|---|
| 2 | the 24 new positives fire below the 86 carried, in every arm | **failed** — they fire at 1.0000 in all six |
| 4 | `ledger` weakest of the four carried routes, misrouting onto `cascade` | **split** — weakest held, `cascade` failed |
| 5 | `no-exclusions` and `opener-only` top the FPR table by more than 0.10 | **held**, by 0.0091 |
| 6 | no arm reaches 1.0000 recall on the 24 new positives | **failed** — all six do |

Predictions 1 and 3 are not scored and never will be. Both register a band
against a v4 figure, and the addendum above records why that licence does not
exist.

### 2 and 6 failed together, and for one reason

Both rest on the same expectation: that the 24 `council` and `hinge` positives,
which no arm had ever been measured against, would fire less than the 86
positives carried from v4. Firing on them saturated instead. All six arms reach
1.0000, which is above the carried rate in five arms and equal in the sixth.

Routing is uneven across those two procedures. Of the turns labelled for
`hinge`, 0.3542 reached `hinge` from an arm that fired and named something,
the second lowest of six, while `council` sits at 0.9167, the highest. So the
expectation was not wrong about the procedures being unfamiliar, and it was
wrong about where unfamiliarity shows up. Noticing that a turn is a decision and
choosing which procedure it needs are separate capabilities, and these two
predictions scored the first while reasoning about the second.

### 5 held on the rule as written, and the margin is inside the noise

The gap from `opener-only` (0.2977) to `stakes-named` (0.1886) is 0.1091
against a registered threshold of 0.10. A paired cluster bootstrap on the 110
triples, 20,000 resamples at seed 1, puts that gap at 95% CI [0.0659, 0.1523],
with 64.5% of resamples above 0.10.

That bootstrap is exploratory and was not registered. It is reported because
0.0091 against a threshold of 0.10 is a margin a reader would otherwise assume
was firmer than the data supports. Both arms it names were collected under
concurrency and the arms they beat include both single-process arms, which the
section above cannot resolve.

## Where `ledger`'s turns go instead

Prediction 4 registered `ledger` as the weakest of the four carried routes, and
`routing_by_procedure` agrees under both the `first` and `any` rules. That
metric is `over_answered`, which is route recall, and reading it as route
quality gets `ledger` backwards.

Pooled over all six arms, positives only, routing rule `first`:

| procedure | precision | recall | times chosen |
|---|---|---|---|
| `ledger` | **0.9574** | 0.2027 | 47 |
| `fit` | 0.9407 | 0.6167 | 118 |
| `cascade` | 0.6996 | 0.8125 | 223 |
| `council` | 0.5523 | 0.9167 | 239 |
| `hinge` | 0.4766 | 0.3542 | 107 |
| `timing` | 0.4475 | 0.8239 | **324** |

Every cell there is conditioned on turns that should fire. On those turns, when
the router picks `ledger` it is right 0.9574 of the time and it picks it 47
times. Across all 3,960 rows the router named `ledger` 108 times and was right
45, because 61 of those picks landed on turns that should not have fired at all.
The ordering survives the wider denominator, where `ledger` is 0.4167 against
`timing` 0.2984 and `council` 0.2953, and the 0.9574 does not.

The table also pools six descriptions, four of which are variants this project
does not ship. `ledger`'s 47 picks are 3 to 13 per arm, and `opener-only`, the
arm this run ranks last, contributes 69 of `timing`'s 324.

Prediction 4 also registered that `ledger`'s misroutings continue to concentrate
on `cascade`, which S9 retargeted `ledger`'s router row against. They do not. Of
the 177 misroutes that named a procedure, `council` takes 44.1% and `cascade`
27.1%, with `timing` third at 15.8%. Every `ledger` fire named a procedure, so
177 is the whole denominator: of the 228 rows labelled `ledger`, 222 fired and 6
missed, and a miss is not a misroute. `council` was not a
routing target when S9 was written, so no measurement from then could have
located this and none is compared against.

So `ledger` is picked rarely and picked well. A fix aimed at making `ledger`
pick better is aimed at a column that is already high. What is low is how often
the turns labelled for `ledger` reach it, and this run does not say whether that
is `ledger`'s row, the rows around it, or both.

## What this does not establish

Six arms vary the frontmatter `description`. Not one varies the router table in
`skills/decision-making/SKILL.md`, the model, the tier or the corpus. Nothing
here manipulates a router row, so nothing here reaches a mechanism. The table
says where the fires went.

Finding out whether narrowing `timing` or `council` would move them means
editing `skills/decision-making/SKILL.md`, which changes the measured artefact
and needs its own registered arm.

`stakes-shown` reaches 1.0000 recall. Arms have saturated recall on this
instrument before at other key versions, and `label_versions_comparable`
refuses a count across them. Within this run five of six arms sit at 0.9818 or
above and one is at the ceiling, which is a band the instrument cannot resolve
inside. That is the problem prediction 6 was written to route around and did
not.

The precision column, the misroute shares, the McNemar tests and the bootstrap
are computed by
[`scripts/score_n10.py`](../../../scripts/score_n10.py), committed beside this
record so the denominators and the seed are readable rather than guessed. None
of them is part of any registered prediction.
