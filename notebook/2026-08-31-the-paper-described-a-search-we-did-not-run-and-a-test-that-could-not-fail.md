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

## Appended: cycle five, and a green gate I reported that had since gone red

The first finding was about the record rather than the paper. I reported the
full gate green, and it was, at the commit I ran it on. A rebase then pulled in
another session's commit removing `README.md`'s `**Audience:**` line, which the
documentation step refuses, and I committed a notebook appendix without
rebuilding the site. Both landed after the run I was quoting, so the claim was
true when made and false when read. The notebook entry reporting a green gate is
what turned it red.

The lesson is narrow and worth keeping: a gate result is a statement about a
commit, not about a branch, and a rebase invalidates it silently.

**A false clause survived four cycles.** `results.tex` said SkillOpt "is not
above the placebo" on the seen set. It reads 0.8087 against 0.7679, it is the
paper's own headline arm, and the table saying so is on the same page. What
SkillOpt does not do is clear the placebo *after correction*. Cycle four rewrote
the sentence around that clause and left it in place, which is the sharpest
version of the pattern these cycles keep finding.

**Three superlatives, all false, all in one section.** `ceiling.tex` said
`PROTOCOL.md` "still carries" the thirty-point sentence, in a clause added by
the same commit that deleted it. It called `rel-005`'s -0.400 the largest skew
magnitude in the corpus, nine lines below quoting `rel-004` at +0.464. And it
called rel-009's +0.019 as near zero as anything measured, where `rel-003` and
`rel-007` both read exactly 0.000. A superlative is a claim over a set, and none
of the three had been checked against the set.

**`related_work.tex` and `appendix_prompts.tex` were the unaudited files this
time**, as `corpus.tex` was last time. The first said neither paper reports an
interval on the quantity in dispute, eleven lines after reporting SkillsBench's,
and asserted what SkillOpt's full text does not contain three lines before
promising not to make claims about sections nobody read. `refs.bib` flags that
exact sentence as unverifiable from an abstract, and had done all along.

Four figures and two docstrings corrected besides. The one worth naming: the
bootstrap constant's docstring claimed the paper reproduces the notebook's
published intervals "rather than near-misses of them", and three of the four
differ in the third decimal. A comment asserting a property nothing checks is
the same failure as prose asserting one, and it had been sitting in the module
whose entire purpose is that the paper cannot disagree with the records.

## Five cycles

47 defects. Still no arithmetic error, and every generated macro has been right
every time. Three stable patterns:

Repair is the highest-risk operation. Every cycle's defects concentrated in
prose the previous cycle had just written, five times out of five.

Files nobody has opened end to end are the second-highest risk, and there is
always one more of them than you think.

And a superlative is a claim over a set. This paper contained five of them that
nobody had checked against the set, and four were false.

## Appended: cycle six, and the reasoning chain that was never recorded

Sixteen. The worst is not a number, it is a claim about what this study
published.

**The records do not carry the reasoning chain, and the paper said three times
that they do.** `RunRecord` has no field for it. The provider parses
`reasoning`/`thinking` off the response and `runner.py` writes
`response=result.text` only, so `grep -c reasoning records-*.jsonl` returns
zero. The size of the gap is in the records themselves: for `on`, `placebo` and
`skillopt` the median generation bills between 564 and 716 output tokens against
a recorded response of roughly five tokens' worth of text. About 99% of what
those three arms generated was paid for and is gone.

The harness appendix said reasoning "is kept, not discarded". The prompts
appendix said full transcripts are published. `CHECKLIST.md` ticked the box.
That box is open now, all three passages say what the records hold, and the
paper names `biderman2024lessons` as the standard it misses rather than the one
it meets. No gate reads for this and none could: the claim is about a field's
absence, and absence is what a renderer cannot notice.

**Four more false claims.** `method.tex` said the `screen` arena may emit a
verdict; `arenas.py` sets `emits_verdict=False`, and the scope claim this whole
paper rests on depends on that being right. Two files said GEPA's winner is the
only arm below an empty prompt; on the unseen set the skill we wrote is below it
too, 0.6786 against 0.6845. `method.tex` said the item-level and template-level
tests disagree in one direction with the clustered test more conservative; two
of six go the other way, one by 0.35.

**And the skew superlative was still there**, because I applied half of cycle
five's fix: I removed the clause about the placebo arm and left the false
superlative it was attached to. `rel-003` and `rel-007` both read exactly 0.000.

**ETCSOVG is ours.** `refs.bib` has said so since 2026-08-13 — "the ETCSOVG
expansion is ours, not the paper's" — and two sections plus
`docs/RELATED_WORK.md` credited the checklist to the paper we cite for the
requirement. The correction was in the repository the whole time, in the file
whose job is to hold it.

**Eight `CHECKLIST.md` boxes had never been audited and seven were wrong.** The
build-environment box named a Windows machine's toolchain beside this machine's
page count. The A/A repeated `placebo`, not the arm `PROTOCOL.md` calls the
control. A test described as deliberately removed is present and is the
replacement for the one that was. And the scope box claimed the abstract states
the model, which it did not until this cycle added it.

## Six cycles

63 defects, still no arithmetic error. The distribution has not moved: every
cycle's findings sit in prose the previous cycle wrote, plus one surface nobody
had opened. Cycle six's contribution to the pattern is the sharpest yet — a fix
applied to half its target, where the half left behind was the false part.

## Cycle seven: the source of truth was the last thing anyone read

Twelve findings, nine of them in the paper as shipped. The cycle also ran the
strongest check any of these has: an agent recomputed 887 of the 899 generated
macros from the raw JSONL without importing a line of project code, and found
zero mismatches. The arithmetic has now been re-derived independently three
times and has never moved.

**The precedence rule routed the reader to the false claim.** Cycle six fixed
three paper surfaces to say the reasoning chain is not recorded.
`appendix_harness.tex` opens by saying that where the appendix and
`docs/HARNESS_DISCLOSURE.md` disagree, the docs file is correct. The docs file
still said **recorded**. So the fix that corrected the paper pointed the reader
at the one place still asserting the opposite, and did it by the paper's own
rule. That is a worse state than before the fix.

**The half-applied fix, again, and this is three cycles running.** Cycle six
raised the omitted-settings count from two to five in `appendix_harness.tex` and
left `CHECKLIST.md` saying two. Same shape as cycle six's own finding about
cycle five's skew fix.

**A repair that over-generalised.** Cycle six's note about the clustered test
was right — "two of six go the other way" — and the sentence I wrote from it
said "on the unseen set it is not [more conservative]", which is wrong for
`skillopt`, 0.3012 to 0.3750. The commit body was more accurate than the paper.

**Two superlatives and a universal, which is the third pattern holding.**
"Every hosted model we could reach" — three registered models never returned, so
*measured* is the word. "Every other arm is tested against [the placebo]" —
`off` is not, by registration. "The two the model answers perfectly" — those two
read informedness 1.000, not accuracy 1.000; `rel-003` reports 0.5893.

**We cannot inspect the evolved bodies either.** `limitations.tex` said they
"cannot be inspected by anyone but us". A content-hash search of the machine
found neither, which the same paragraph says. Nobody can inspect them.

**The skeleton does not compile from a bare checkout.** `paper/Makefile` and two
docstrings in `figures.py` promised it. Ran it: the no-run path writes
`macros.tex` and nothing else, `main.tex` inputs tables that were never written,
and every `\NUM` would be undefined regardless. Three statements of a claim
nobody had executed.

**One macro family was named for the wrong operand.** `\gap<Set><Template><Arm>`
puts the arm last; `\gap<Set><Template><Baseline>` put the *baseline* last while
always measuring `gepa`. Two families, one prefix, the trailing token meaning
opposite things. Renamed to `\gepaLess<Set><Template><Baseline>`, value
unchanged at -0.2589.

## Seven cycles

75 defects and still no arithmetic error, against three independent
re-derivations of the numbers. The pattern the record now supports is narrow and
worth stating plainly: this paper's numbers have been right the whole time, and
its sentences about those numbers have been wrong 75 times. The defects live in
prose written to fix earlier prose, in the surface nobody has opened yet, and in
any sentence quantified over a set.
