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

## Appended the same day: the decomposition contribution rested on false algebra

A second adversarial pass found what the first three missed, and it is worse
than anything above because it is a contribution and not a caveat.

Accuracy on a two-option key is `pi*sens + (1-pi)*spec`. At `pi = 0.5` that is
`(J+1)/2`, a function of informedness alone. Response bias contributes exactly
nothing to accuracy on a balanced key, so there is nothing for a decomposition
to separate. Every template here is balanced 56/56 or 28/28 by construction,
and over the 50 template-by-arm cells the identity holds to four decimals in
every one of the 26 where no answer went unread.

The section's worked example was wrong in both directions. A policy answering
one option nine times in ten scores 0.50 on a balanced set, not 0.63; 0.63 is
what it scores at a base rate near two thirds. Two other places claimed a bias
shift was worth "roughly thirty points" on this corpus. A pure bias shift holds
J fixed, so on a balanced key it is worth zero, and the corpus-ceiling section
proved it against itself: sensitivity 1.000 with specificity 0.167 to 0.250
pins accuracy at 0.583 to 0.625, which is what it measured three times.

What survives is sharper than what it replaces. The identity breaks only when
unreadable answers land unevenly across the key, and that is measurable:
`gapParsed` for gepa on `rel-001-vendor-outage` is +0.2784, and the reported
accuracy for that cell is 1.8 points below chance. So the mechanism costs
accuracy on the metric we publish while inflating it on the parsed subset,
which is the opposite of the direction the paper claimed for two drafts.

The lesson for the register: three independent agents recomputed every macro in
this paper and all three confirmed the arithmetic. None of them checked whether
the estimator the arithmetic implements answers the question the prose says it
answers. A number can be correctly computed and still be an answer to nothing.

## Appended: the repair to the algebra needed a repair

A second adversarial cycle read the fixes rather than the original, and its most
useful finding was that the fix above inverted its own premise. Saying accuracy
is `(J+1)/2` and then that a chance template is hard to spot cannot both be
true: at `J = 0` accuracy reads exactly 0.5000, the floor of the scale and the
most diagnostic number on it.

Two things save the claim and both are in the records. Pooling, first: ten
templates with three at chance still return 0.7168 for an empty prompt, and a
corpus-level number does not say which three. And second, the metric this study
publishes is not the parsed one. Scoring an unreadable answer as wrong breaks
the identity and takes the ordering with it. `rel-003-oncall-escalate`
discriminates perfectly for `off`, `J = 1.000` on the 58.9% of items it
answered, and reports 0.5893. `rel-006-refund-request` barely discriminates and
reports 0.6071. A template that is always right when it answers ranks below one
that is mostly guessing.

The other bad repair was the memorisation claim. `utilisation_floor` belongs to
`rel-008-contract-renew`; `headroom_pct`, 2818 and 2032 belong to
`rel-007-capacity-scale`. Both are training templates, so neither appears in the
unseen set and no unseen number can speak to what the constants cost. On the two
templates concerned GEPA reads 0.8750 and 1.0000 against an empty prompt's
0.7679 and 1.0000. The sentence claiming memorisation cost GEPA accuracy was
written to be self-critical and was not true.

Six smaller ones went with them, including a p-floor whose stated reason was
wrong: the observed sign vector does not have to maximise the statistic, it only
has to be one of the `2^k` and therefore inside its own tail. For SkillOpt on the
seen set it sums +16 against an attainable +34, and the test still returns
18/64.

The pattern worth carrying: each cycle's errors were in what the previous cycle
had just written. Three cycles in, the defect rate in untouched prose is zero
and the defect rate in freshly repaired prose has been the highest in the paper
both times.

## Appended: cycle three, and the rule that admits our worst template

The pattern held a third time. Cycle three's findings were in what cycle two had
written, plus one file no cycle had touched.

**The admission rule the paper offers as a contribution admits the corpus's own
worst template.** The three criteria are accuracy below ceiling, skew near zero,
informedness below one. `rel-009-flight-rebook` on the control arm reads 0.4911,
skew +0.019, informedness +0.028. It passes all three, and it is one of the
three templates the five-arm study found measures nothing. A coin has zero skew
and zero informedness too. The third criterion bounds discrimination above and
never below, and the paper had claimed "No template we have passes all three".
A lower bound on `J` is the obvious repair and nothing has been run against one,
so the section now says the criteria are necessary, demonstrably not sufficient,
and better than the band they replace. `PROTOCOL.md` takes the same correction.

**The memorisation paragraph reported half its evidence.** It quoted GEPA, where
the constants bought nothing, and omitted SkillOpt, where they may have bought a
great deal. SkillOpt lifted 63% from `rel-008-contract-renew` and reads 0.9821
there against an empty prompt's 0.7679, and that single template carries 8 of
the 16 net items behind the study's largest gain. Half the headline sits on the
template the winner memorised a threshold for. The hedges are real and stated:
`rel-005-security-patch` carries +17 with no constant lifted from it, and the
comparison was never registered. But writing a self-critical sentence and
checking it are different acts, and the first one had happened.

**SkillOpt did not lift from `rel-007`.** Its 63 cannot come from a variable
drawn between 10 and 40. Three places said both engines lifted from both
templates.

**`corpus.tex` was the file no cycle had opened.** It still pointed at section
5.3 for a transcription claim that section now contradicts: the rewrite of 5.3
moved the ground under a cross-reference two sections away, and nothing checks
that. Four smaller ones went with it, including a seven-template denominator
called ten and a phrase cycle two had retired everywhere except limitations.

Three cycles, 27 defects, and the defect rate in prose a cycle has just repaired
remains the highest in the paper. The corollary is the uncomfortable one: a
fourth cycle is not optional because a third one was clean, it is required
because the third one was not.

## Appended: cycle four, and the first defect a fix created two files away

Six more, four of them in what cycle three wrote. The one worth naming is the
mechanism rather than the fact.

Cycle three narrowed the corpus section's seed-holdout paragraph to say this
corpus has "no such rule to transcribe". The amendment it cited says
*constant*, not *rule*, and on this corpus that is the whole claim: every
template's comparison and its load-bearing facts are fixed across seeds, and
only the threshold value is redrawn. So the constant channel is closed here and
the rule channel is open, an engine transcribing a rule would still have been
scored as generalising, and the probe addressed a failure that is still
available. The discussion had been saying that all along. A one-word
generalisation in one file made it contradict a section two files away, and
nothing in the gate reads for that.

**The screen is seven models, not eleven.** The harness registers eleven, eight
returned inside the budget, and `nvbuild-ceiling-screen.json` holds seven. The
section called the committed artefact an eleven-model screen, so a reader
opening the file it names finds neither number. `screen_macros` reads the file
now. The eighth model is in a notebook entry and not in the artefact, and the
artefact stays as it is: a record edited to match a paper is not a record.

**The act-or-wait test covers nine of ten templates.** Six plus three is nine.
`rel-005-security-patch` is in neither group and carries the largest skew
magnitude in the corpus at -0.400. Its options are `patch_immediately` and
`schedule_patch`, which cannot be classified as act-or-wait or two-act without
choosing the answer. Placing it moves +0.097 to +0.026, or 0.172 to 0.230. The
direction survives either placement and the two averages do not.

Four smaller: only one *seen* template sits at chance, because rel-006 reads J
0.271 with an interval excluding zero and the second chance template is unseen;
the placebo has no row in the comparison column it was said to top, being the
control; "+8 of +16" reads as a share of a partition when the positives sum to
25; and a forward reference pointed at a section whose answer cycle three had
deleted.

Two typed-number classes are now generated. `screen_macros` reads the ceiling
screen and `template_range_macros` reads the integer bounds that the argument
about which template a lifted constant came from rests on. Both sources were
committed and both were being read by eye.

`PROTOCOL.md` said "three gates" over a five-item list, and still called the
placebo token-matched, which is the defect this audit opened with. The source of
truth was carrying the error the document it governs had been corrected for.

## The count, four cycles in

33 defects. None was an arithmetic error and the generated macros were right
every time. The distribution is the finding: every cycle's defects were
concentrated in prose the previous cycle had just written, and the one file no
cycle had opened was defective too. Repair is not a safe operation, and a paper
that has been reviewed four times is not the same as a paper that is correct.

The full gate rather than the fast one caught two more: `figures.py` and
`stats/` had fallen off their 100% floors, on the refusal branches the new code
added. `de check --fast` skips tests and coverage, so eleven commits went by
green while the branch that raises on an unshared prompt prefix had never run.
