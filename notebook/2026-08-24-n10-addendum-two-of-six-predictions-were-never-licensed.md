# 2026-08-24 — N10 addendum: two of six predictions were never licensed

Written after the first of six arms finished and before the other five did. The
[prediction](2026-08-24-prediction-n10-the-six-description-arms-on-v6.md) stays
exactly as registered. This entry says what is wrong with it.

## The defect

Predictions 1 and 3 register bands against numbers computed from the v4 records.
Prediction 1 asks whether per-arm recall on the carried items lands within ±0.02
of its v4 value. Prediction 3 asks whether routing to `council` and `hinge`
falls below the 0.5327 the four established routes reached at v4.

**The harness refuses both comparisons, and I did not ask it before registering
them.** Handing the N6 `full` arm and this one to the four guards:

| guard | verdict |
|---|---|
| `label_versions_comparable` | **refuses** — `[4]` against `[6]` |
| `models_comparable` | passes |
| `venue_comparable` | passes |
| `skill_versions_comparable` | **refuses** — one arm records `0.3.0` and the other records nothing |

The label refusal is the whole reason this run exists, and registering a band
straight across it was careless in a way the prediction's own opening paragraph
should have caught.

The second refusal I did not know about at all. **Every v4 record carries
`skill_version: None`**, because the stamp landed after those runs were made. An
absent stamp reads as unknown rather than as a particular revision, so nothing
establishes that N6 and this run were given the same description text. That is
not a technicality here: `metadata.version` reached 0.3.0 on 2026-08-19 by
rewriting this exact frontmatter from four procedures to six, and N6 ran on
2026-08-18.

So the honest statement is not that prediction 1 was falsified. **It could not be
scored**, and neither could prediction 3. A number that moved across a boundary
two guards refuse is not a finding about the corpus, the description or the
model.

This is the same shape as the defect [N7 recorded against
itself](2026-08-18-prediction-n7-the-remaining-description-arms.md): a band
re-derived from observed numbers while citing an earlier run. The lesson there
was about where a threshold comes from. The lesson here is one step earlier —
**call the guard before registering the band, not after reading the result.**

## What the four surviving predictions say, on the `full` arm

660 rows, parse rate 1.0000. All figures within v6, one key, one skill revision,
one model.

| | accuracy | recall | FPR |
|---|---|---|---|
| all 330 items | 0.9015 | 218/220 = 0.9909 | 63/440 = 0.1432 |
| the 258 carried | 0.9089 | 170/172 = 0.9884 | 45/344 = 0.1308 |
| the 72 added at v5 | 0.8750 | 48/48 = **1.0000** | 18/96 = 0.1875 |

**Prediction 2 is falsified, and cleanly.** The 24 `council` and `hinge`
positives were supposed to fire at a lower rate than the carried 86 because
nothing had ever been asked about them. They fire at 1.0000 against the carried
0.9884. Being new to the corpus did not make them harder to notice.

**Prediction 6 is falsified by the same fact.** The band went on the new
positives because recall was saturated on the carried ones, and it turns out to
be saturated there too. The instrument has no headroom on this axis anywhere, on
this arm.

**Prediction 4 is met, and by a wider margin than registered.** `ledger` is the
weakest of the four carried routes and is the weakest route on the corpus:

| route | routed correct when fired |
|---|---|
| `ledger` | 8/38 = 0.2105 |
| `hinge` | 11/24 = 0.4583 |
| `fit` | 20/30 = 0.6667 |
| `timing` | 23/28 = 0.8214 |
| `cascade` | 28/32 = 0.8750 |
| `council` | 23/24 = 0.9583 |

**Prediction 5 needs the other five arms and is not scored here.**

## The thing worth noticing, which nothing predicted

`council` and `hinge` were added together, in equal numbers, to the same bands,
for the same reason. They do not behave alike at all: **0.9583 against 0.4583**.
Whatever made two procedures reachable did not make them equally reachable, and a
run that had reported one pooled figure for "the procedures added at v5" would
have averaged 0.71 and said nothing. No prediction registered here would have
caught that, and it is the most interesting number on the page.

It is one arm. Five more are running and the figure may not survive them.

## The instrument check that was actually available

The comparison I wanted was whether the same item behaves the same way twice.
Across corpus versions that is not on offer. Within the arm it is, and it was
free:

- **Firing agrees between repeats on 309/330 items, 0.9364.**
- **Routing agrees on 95/130 doubly-fired items, 0.7308.**

Routing is markedly less stable than firing, which is not new — it is what
[2026-08-12](2026-08-12-five-repeats-firing-is-stable-routing-is-not.md) found
and named. It should have been the registered instrument check here, because it
is the one no guard refuses.
