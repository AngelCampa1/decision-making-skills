# Track N10 — the six description arms, rebuilt on answer key v6

**2026-08-25.** 6 arms × 330 items × 2 repeats = **3,960 isolated `claude -p`
calls**, `haiku`, **0 unparseable**, 0 isolation failures. Code at `5ed5d38`.

**Answer key:** `datasets/triggers/decision-making/index.yaml` v6

Prediction: [`notebook/2026-08-24-prediction-n10-the-six-description-arms-on-v6.md`](../../../notebook/2026-08-24-prediction-n10-the-six-description-arms-on-v6.md),
committed before the launch. Two of its six predictions were found unlicensed
before any of them were scored, recorded in
[`notebook/2026-08-24-n10-addendum-two-of-six-predictions-were-never-licensed.md`](../../../notebook/2026-08-24-n10-addendum-two-of-six-predictions-were-never-licensed.md).

Every published trigger number before this run was scored at v4 on a 258-item
corpus. `label_versions_comparable` refuses that comparison, so nothing on
record described the corpus on disk. This run is the baseline every later arm is
scored against.

| arm | accuracy | recall | FPR |
|---|---|---|---|
| `no-opener` | **0.9439** | 0.9955 | **0.0818** |
| `stakes-shown` | 0.9242 | **1.0000** | 0.1136 |
| `full` | 0.9015 | 0.9909 | 0.1432 |
| `stakes-named` | 0.8727 | 0.9955 | 0.1886 |
| `no-exclusions` | 0.7970 | 0.9909 | 0.3000 |
| `opener-only` | 0.7955 | 0.9818 | 0.2977 |

No cross-version comparison against N6 or N7 appears here or anywhere else from
this run. Six arms compared pairwise is fifteen comparisons and this run
registered no multiplicity control, so no p-value is offered on the ordering.

## The pre-registered confirm hypothesis points the wrong way

`preregistration/decision-making-v2.yaml` registers that the shipped description
fires on decision turns more often than the same description with its
trigger-phrase opener removed. On this corpus it does not. `full` recalls
0.9909 against `no-opener`'s 0.9955, and `no-opener` reaches that while halving
the false-positive rate.

The screen arena exists to find this before the confirm arena is built, and it
found it. Nothing is decided here: the private holdout is a different sample and
the hypothesis is registered against that one. What this run establishes is that
the effect it predicts is absent in the direction predicted on the public
corpus, which is where a v3 pre-registration or a change to the description
would have to start.

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

Routing to those same two procedures is poor — `hinge` routes correct on 0.3542
of its fires. So the expectation was not wrong about the procedures being
unfamiliar. It was wrong about where unfamiliarity shows up. Noticing that a
turn is a decision and choosing which procedure it needs are separate
capabilities, and these two predictions scored the first while reasoning about
the second.

### 5 held on the rule as written, and the margin is inside the noise

The gap from `opener-only` (0.2977) to `stakes-named` (0.1886) is 0.1091
against a registered threshold of 0.10. A cluster bootstrap on triples puts that
gap at 95% CI [0.0659, 0.1523], with 63% of resamples above 0.10.

That bootstrap is exploratory and was not registered. It is reported because the
margin is one-twelfth of the threshold and a reader would otherwise have to
assume the separation is firmer than the data supports.

## Routing is a competition between procedures

Prediction 4 registered `ledger` as the weakest of the four carried routes, and
`routing_by_procedure` agrees under both the `first` and `any` rules. That
metric is `over_answered`, which is route recall, and reading it as route
quality gets `ledger` backwards.

| procedure | precision | recall | times chosen |
|---|---|---|---|
| `ledger` | **0.9574** | 0.2027 | 47 |
| `fit` | 0.9407 | 0.6167 | 118 |
| `cascade` | 0.6996 | 0.8125 | 223 |
| `council` | 0.5523 | 0.9167 | 239 |
| `hinge` | 0.4766 | 0.3542 | 107 |
| `timing` | 0.4475 | 0.8239 | **324** |

When the router picks `ledger` it is right 96% of the time. It rarely picks it.
`timing` is chosen 324 times at a precision of 0.4475 and `council` 239 times at
0.5523, and those two absorb what `ledger` does not claim.

Prediction 4 also registered that `ledger`'s misroutings continue to concentrate
on `cascade`, which S9 retargeted `ledger`'s router row against. They do not.
They concentrate on `council` at 44.1%, with `cascade` second at 27.1%.
`council` did not exist as a routing target when S9 was written.

The precision column is computed here and is not part of any registered
prediction.

## What this does not establish

The precision reading above is one run on one corpus at one tier, and no arm of
this run varies the router. It says where the fires went. It does not show that
narrowing `timing` or `council` would move them, and the obvious next step —
editing `skills/decision-making/SKILL.md` — changes the measured artefact and
needs its own registered arm.

`stakes-shown` reaching 1.0000 recall is the third arm on record to saturate
recall on this instrument. A ceiling that three of six arms touch is a ceiling
the instrument cannot see past, which is the same problem prediction 6 was
written to route around and did not.
