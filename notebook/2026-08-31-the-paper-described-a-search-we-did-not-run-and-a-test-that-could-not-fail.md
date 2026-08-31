# 2026-08-31 — The paper described a search we did not run, and a test that could not fail

No model calls. This is an audit of `paper/` against the committed records and
the dated entries behind them, and the repairs it forced. Six commits on
`paper-audit-fixes`.

The paper compiled clean at 22 pages and was about to go out. Three sub-agents
read it: one adversarial review and two re-derivations that were not shown the
review's numbers. Every generated macro recomputed correctly. Every defect they
found was in what the paper compared, what it claimed, or what it left out.

## What was wrong

**The placebo is not token-matched.** Delivered body sizes are placebo 655,
`on` 778, `gepa` 910, `skillopt` 1697 prompt tokens. The per-item delta against
`off` is exactly constant, so these are counted and not estimated. Five places
in the paper called the match a token match. It is a word and structure match
against the seed skill only, and the evolved winners were never in it.

**`\placeboWords` was computed off an asymmetric pair.** `figures.py` compared
the skill with its frontmatter stripped against the placebo raw. The real pair
is 612 and 557, not 612 and 628. The gate's own call site at `skills.py:365`
had been doing it correctly the whole time.

**Three registered primaries could not have rejected.** Items come from
templates, the limitations section says the template is the independent unit,
and the unseen set is three templates. A one-sided sign-flip test over three
clusters has a p-floor of 0.1250. No outcome would have cleared alpha. SkillOpt's
seen headline moves from 0.0341 to 0.2812 under the same unit.

**The minimum detectable effect was pre-registered and never printed.** 0.0807
unseen and 0.0749 seen at alpha 0.05 and 80% power, computed at a design effect
of 1.0 for a corpus built from templates. `PROTOCOL.md` specifies about 2.0. At
2.0 the same arithmetic gives 0.1137 and 0.1053, roughly 2.6 times the largest
gain the study observed. `CHECKLIST.md` said no MDE was reported, which was
false about our own registration.

**Section 5.3 described the wrong search.** Two rounds ran on 2026-08-27: one
over all ten templates, one over the seven training templates. The second
produced the winners the study tested, and the prediction entry rules the first
pair out as arms in as many words. Section 5.3 was typed from the notebook entry
about the first pair, and both entries are dated the same day.

The check that settles it needs neither document: `rel-009-flight-rebook` is a
holdout template, a seven-template search never met it, so a travel-connection
specialisation cannot be a body that ran. Withdrawn with it: "20 of 21", "eight
of ten", the 49-pair 14.3% flip rate, and "three items above their seed".

**The GEPA winner-selection sentence had the same provenance error.** The
tested run's `winner.json` says `score = 1.0, n_items = 3, winner_source =
engine`. The search ran to completion and the engine's own acceptance rule chose
a body scored on three items. The paper said our code picked it from a lineage
after a budget stop, which is true of the search we did not test.

**The runaway-generation claim was retracted in its own notebook entry** and
the five-arm records invert it. At the 4096-token cap: placebo 47, `on` 34,
`skillopt` 27, `off` 9, `gepa` 3. The arm that provokes runaway generations
hardest is the document whose content says nothing, which makes it a length
effect and not a formatting fix either winner supplied.

**Four citations pointed at works that do not carry the figure beside them.**
The 7.8x variance ratio is `harnessdisclosure2026`'s and three sites credited
`harnessbench2026`. AgentAtlas was unpinned and carried a comparison v2's own
abstract disclaims, which `PROTOCOL.md` had already withdrawn. The 2026
GSM-Symbolic re-audit was cited to the 2024 paper it re-audits, and it is an
unrefereed re-analysis with no bib entry. The trust-framing 59% was uncited.

## What changed

`figures.py` gained `body_tokens`, `clustered_tests`, `power_macros`,
`per_template_macros`, `restricted_macros`, `key_selectivity` and
`at_cap_macros`, so every number above is generated from committed records
instead of typed. `stats/cluster.py` gained `cluster_sign_flip`, which
enumerates all 2^k sign vectors when k is small enough and returns the attainable
floor beside the p-value. 639 macros now, 22 tests added, full gate green.

The paper is 26 pages. The abstract, the contributions and a discussion
subsection now lead with the undecidability. That is the reframe: a
pre-registered study with a placebo, a post-hoc holdout, an A/A control and a
hash-locked registration, which still could not answer its own question, and two
lines of arithmetic over the registration that would have said so beforehand.

## Prediction, registered here before the next run

If the p-floor check is applied to the skill optimisation papers in
`docs/RELATED_WORK.md` that report a template-built or task-family-built corpus,
more than half will have a floor above their stated alpha on at least one
reported comparison. Stated now because it is cheap to check and because a
prediction made after checking is not one.

## What is still open

The two `CHECKLIST.md` boxes that need the maintainer: arXiv endorsement and the
Zenodo DOI. Neither is a machine's to close.
