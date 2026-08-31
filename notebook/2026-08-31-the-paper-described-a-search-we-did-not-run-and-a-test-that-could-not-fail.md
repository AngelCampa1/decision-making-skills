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

## Cycle eight: the provenance artifact was the last never-audited surface

Thirteen findings. The cycle opened two surfaces no previous one had: the
published run's own `README.md`, which the paper points readers at as its
provenance artifact, and the arm-purpose strings in `solvers/arms.py` that
`de sync` renders into the site.

**Four claims about our own provenance were false, and all four were universals
over a set.** `main.tex` listed the corpus-ceiling probes among the classes of
number that cannot be generated, and said "Both sections say so". The ceiling
*screen* wrote `nvbuild-ceiling-screen.json`, which is committed, which
`figures.py` reads, and which supplies six macros the section uses — and
`ceiling.tex` says so in terms. `results.tex` said "Every figure here is read
off the two search runs" in a subsection using thirteen generated macros.
`ceiling.tex` said everything after the screen wrote no records, which is wrong
for the admission-rule subsection: I recomputed all ten of its figures from
`records-off.jsonl` and every one reproduces, `rel-009` at skew +0.0187 and
J +0.0283 against the printed +0.019 and +0.028. And `appendix_prompts.tex`
said a replicator can recompute "all three" hashes one sentence before saying
"Both hashes above reproduce"; `off` is empty and its `candidate_sha` is null.

**"Matched on tokens" survived on six surfaces after the correction landed.**
`docs/PROTOCOL.md` has carried the dated correction since this morning —
nothing here has ever counted tokens, `check_placebo_match` compares word counts
within 15%. It reached three paper surfaces and none of: `arms.py` twice,
`study.py`, `docs/METHODS.md` twice, the run README twice. One of those is
`ARM_PURPOSE`, so `de sync` was publishing the false version to the site from a
source the `generated regions` gate certifies as matching. The gate was right
and the source was wrong, which is the failure mode a generated region has.

**The run README carried a git SHA that does not exist.** `0b379af` is not a
valid object; the prediction's first commit is `e882eff`, which the same file
gives correctly sixteen lines down. The provenance gate reads the commit graph
and not this prose, so nothing could see it. The README also asserted the exact
causal claim the paper spends a paragraph refusing — "every difference between
arms in the tables above is a difference the prompts caused" — and repeated
the residency wording `HARNESS_DISCLOSURE.md` was corrected for three days ago,
and counted eight screened models beside a committed file holding seven.

Corrections to the README went in as edits plus a dated corrections block at the
foot, rather than a silent rewrite: it is a dated record, and one that quietly
stops disagreeing with itself has lost the thing that made it worth keeping.

## Eight cycles

88 defects, and the fourth independent re-derivation of the arithmetic again
found nothing. Cycle eight also enumerated every remaining superlative in the
paper and every one of them checked out, which is the first time that pattern
has come back clean. The pattern that has not exhausted itself is the other one:
there was still one more surface nobody had opened, and it was the artifact the
paper cites as its evidence that the numbers are real.

## Cycle nine: a fix introduced a defect, and the citation file had never been read

Fifteen findings, and one of them is mine from cycle eight. I changed the run
README's "five arms at a matched token budget" to "at a matched word count",
which corrected the word *token* and left behind a claim that is false either
way: the five arms do not share a body size, and `method.tex` spends a
subsection saying so. The right edit was to delete the phrase. A correction that
repairs the wrong half of a sentence is a new defect wearing the shape of a fix.

**A figure caption asserted a comparison that its own figure refutes.** The
`fig:accuracy` caption said the gap between the two item sets is larger than the
gap between any two arms within a set. From the plotted coordinates the largest
within-set gap is 0.0919 (seen `skillopt` 0.8087 against seen `off` 0.7168) and
the set-to-set gap is 0.0844 on arm means and below 0.0919 for three of the five
arms. Nine cycles in, this was the first false claim found in a caption, because
captions are where nobody looks.

**`CITATION.cff` had never been opened by any cycle, and it ships with the
arXiv and Zenodo archive.** It says decision quality is not yet measured, where
`SCORECARD.md` says the shipped skill has been measured on it. It says the
controlled design "has not run". It says no published run has used the placebo
arm, beside a committed `records-placebo.jsonl` of 728 lines. The documentation
gate reads root `*.md` and `docs/`, so a `.cff` file is outside it, which is the
same reason `paper/CHECKLIST.md` has produced a finding in four cycles running.

**"The harness registers eleven" models.** `arenas.py` registers seven vendor
*prefixes*; `ModelEntry`'s docstring says prefix rather than exact id, and no
roster of eleven models exists anywhere in the tree. Eleven is how many models
this key can reach under those prefixes, which is how `docs/STATUS.md` and
`docs/LIMITATIONS.md` both word it. The paper was the only surface that
converted reachability into registration, and `figures.py` had copied it.

**0.722 was attributed to the wrong pass.** `hrd-002` read 23/36 = 0.639 first
and 13/18 = 0.722 later; the notebook says so in a sentence naming both. The
paper called 0.722 the first pass and 0.639 appears nowhere in `paper/`.

`SCORECARD.md` said a screen-tier run would carry a verdict, where `arenas.py`
gives `emits_verdict=True` to `confirm` alone — the load-bearing sentence
explaining why that table is empty. It also said N7 is running, where
`docs/STATUS.md` records N7 done on 2026-08-19 and N10 since. And the A/A
over-claim, retracted in the paper and in the run README, was still standing in
`README.md` and `docs/STATUS.md`; the latter takes an appended correction by
standing rule, not an edit.

Fixing all of this took the PDF from 28 pages to 29, which stales the build
figures in the box I had just corrected. Updated in the same commit and dated
this time, because a page count without a date is a number that goes wrong
silently.

## Nine cycles

103 defects. Still no arithmetic error, on a fifth independent re-derivation.
Two things this cycle establishes that the previous eight only suggested. The
first is that repair is not merely where defects concentrate: it manufactures
them, and I have now done it myself in consecutive cycles. The second is
mechanical and fixable — every surface that has produced a repeat finding
(`CHECKLIST.md`, `CITATION.cff`, `paper/` itself) sits outside the documentation
gate's scope of root `*.md` and `docs/`. The gate cannot see the files that
break most often.

## Cycle ten, first report: five of thirteen were mine

An agent auditing the surfaces outside the documentation gate's scope returned
thirteen findings. Five are defects my own cycle-eight and cycle-nine fixes
created or left behind, which is the clearest measurement yet of the pattern
these cycles keep finding.

**The run's provenance artifact pointed at two directories that never existed.**
The arm table gave each evolved winner as "frozen winner of
`results/evolution/2026-08-27-1b24c9d-...`". Neither directory exists, neither
sha resolves, and `.gitignore:79` excludes `results/evolution/`, so neither
could ever have been committed. Three other surfaces say the bodies are gone;
only the artifact a reader is sent to said they were locatable. Nobody had
checked, in nine cycles, whether a path in a table resolves.

**My Makefile comment gave the wrong reason.** Cycle eight found the false claim
that the skeleton compiles from a bare checkout, ran it, and replaced it with a
reason that is also wrong: `main.tex` guards *both* `\input` targets with
`\IfFileExists`, so the missing tables are skipped silently. What stops the
build is the undefined `\NUM` macros alone. The comment carried "Checked
2026-08-31" two lines below the sentence the check missed.

**And the same claim survived in two test docstrings and one more in
`figures.py`**, which cycle eight did not sweep for.

**My cycle-nine edit contradicted itself inside one docstring.** I added
"eleven is reachable models, not registered ones" to a test and left the next
paragraph saying "Eleven is how many models the harness registers".

**My cycle-nine rewrite kept an over-generalisation.** The run README says no
screen-tier venue can host this study. `arenas.py` registers three backends at
that tier and the screen covered one of them. The paper made the same move at
`ceiling.tex` with "no verdict-bearing venue", now scoped to what was screened.

The rest were surfaces nobody had opened: `site/src/lib/site.ts` still said no
published run has used the placebo arm, four days after one did; a CI comment
named a test that does not exist; `arms.py`'s opening line counts five arms
against a six-arm tuple, which is the exact defect its own `ARM_PURPOSE`
comment was written to prevent; the hash-lock checklist box says every arm's
body is hashed, where `off` carries null on all 728 records; and two files
outside the gate make the AgentAtlas magnitude comparison that `refs.bib`
records as withdrawn by v2.

## Ten cycles, and what the record now says

116 defects. Still no arithmetic error. The distribution is now unambiguous and
it is not flattering: the defects are concentrated in the repairs, and I am the
one making them. Cycle nine caught one of mine, cycle ten caught five. A fix
lands on the sentence it was aimed at and leaves the sibling, or corrects the
wrong half, or states a new reason that is wrong in a new way.

The mechanical part of this is fixable and worth recording for whoever picks it
up: every surface that has produced a repeat finding sits outside the
documentation gate's scope of root `*.md` and `docs/`. `paper/` entirely,
`paper/CHECKLIST.md`, `CITATION.cff`, `results/**/README.md`, `.py` docstrings,
`Makefile`, `.github/`, `site/src/`. The gate cannot see the files that break
most often, and no gate reads whether a sentence is true in any of them.

## Cycle ten, second report: a replicator following the appendix builds the wrong prompt

Thirteen more, from an agent that executed every claim the paper makes about the
repository rather than reading it.

**The prompt appendix gives the wrong assembly order.** "Two blocks precede the
arm's body in every system prompt." `arms.py:149-162` builds `[BASE_FRAMING]`,
appends the body, then appends `FORMAT_CONTRACT`. One block precedes and one
follows. This is the appendix whose whole purpose is to let a replicator rebuild
the prompt, and a replicator following it puts the body last and reproduces a
different prompt in every arm. Ten cycles read that section for what it claimed
and none of them ran the function.

**The paper claims a recomputation that does not happen.** The Observability
paragraph says every number the paper draws from the study is recomputed from
the records by `de figures`. `figures.py` opens by saying the opposite in bold —
"This is a renderer and never a second analysis" — and reads accuracies,
p-values and adjusted q-values straight out of `analysis.json`. `results.tex`
states it correctly. The appendix asserted a universal with three named
exceptions and the largest class was not among them.

**Three false claims in one sentence about the nine hard templates.** "Nine
harder templates in two days, in distinct domains, each built around a rule the
model has to select." Git says all nine were added on 2026-08-28 between 09:26
and 11:30. `hrd-008` carries `hrd-003`'s solution expression byte for byte and
`hrd-009` carries `hrd-002`'s, which the section says itself four paragraphs
later: two of them were built to diagnose a third. And `hrd-001` is
`'honour_claim' if owned_months <= term_months else 'decline_claim'`, one
threshold and no selector, where the other eight all carry the
`(X if category else Y)` form. The partition two subsections down leaves the
same template unaccounted: six plus the two one-sided ones is eight of nine.

**"The third ran on a realised 18/17 split."** 18 + 17 is 35, and the sentence
quotes 0.629, which the enumeration two sentences earlier gives as the 35-item
measurement. It is the first. The other two are balanced 12/12, which is why
they land on the identity exactly.

**The estimator count is not supported by any of our records.** The paper says
four estimators that could not return a non-zero value, two producing clean runs
and one caught in source. Four separate notebook entries and documents give
four, four, five and three, and the one that gives four says *two* were caught
in source. The paper picked a count and added a split nothing supports. Replaced
with the shape of the claim and an admission that our own records disagree,
which is a better argument for the check than a number would be.

Two of the thirteen were fixes from earlier this cycle that had not been swept:
the introduction still carried "no verdict-bearing replication can be built on
this corpus" after `ceiling.tex` was scoped that morning, and cycle eight's
narrowing of "Every figure here" was still wrong for a third search.

## Ten cycles, closing count

129 defects. No arithmetic error in any of them, and this agent independently
re-derived the fourth-criterion paragraph, the parse-failure split, the at-cap
counts, the balanced-key identity in all sixteen fully-parsed cells and the
worked appendix item, which renders byte-identically from the template at seed
10226. Six independent re-derivations now.

The two findings worth carrying out of this cycle are not about any one
sentence. The first: a claim about code is only checked when someone runs the
code, and "two blocks precede the body" survived ten readings because reading is
not running. The second: a fix is a new claim and inherits none of the
verification of the sentence it replaces.

## Cycle ten, third report: two already fixed, and one thing we cannot check

Four findings, two of which the second report's fixes had already closed: the
lost-directories sentence and the 300 KB bound on the content-hash search. A
machine-wide search confirmed the stronger version of the first — no search-run
directory survives anywhere, not the two tested seven-template winners and not
the four earlier ones.

**The implicit-test count was stated per rollout and belongs per proposal.** The
discussion said a run of a few hundred rollouts performs a few hundred implicit
tests. The rule fires once per proposal, and `results.tex` gives the proposal
counts two pages earlier: nine candidates for SkillOpt, twelve for GEPA. The
argument does not need the inflated number and is stronger without it, because
the point is that the count scales with the budget and nobody reports it.

**And one caveat that is not a defect but belongs in the paper.** The
three-and-three split of six frozen winners cannot be enumerated from any
record. Our notebook names three of the six; the other three are unnamed, the
bodies are gone, and nobody can check the split, us included. The paper now says
so where it makes the claim. Six independent re-derivations have found no
arithmetic error, and this is the one number in the paper that no re-derivation
could reach.

## Cycle ten, fourth and fifth reports: the homepage denies the study

Thirty-one more findings across two agents, one auditing the paper's claims
about mechanisms and one auditing every prose surface no gate reads.

**The project's own homepage contradicts the paper.** `index.astro` says of the
call ledger: "Every one asks the same thing. Does the skill turn on at the right
time? Not one of them asks yet whether it helps you choose better." The number
rendered beside that sentence is generated from a ledger row that includes the
5-arm study's 4,368 calls, which measure exactly that. A second paragraph says
"No run has used it yet" of the placebo, which was that study's registered
control over 728 items. Both paragraphs predate the run by a week and nobody
swept them. `CITATION.cff` points readers at that page.

**A refusal the paper describes in the present indicative never ran.** The
harness appendix says Ollama's `/api/show` card "is read as an isolation
receipt and the run is refused if it carries a `SYSTEM` prompt". The only
caller of `isolation_receipt` in the repository is a test. The study path goes
through `evolution/adapter.py` and never reaches it, and neither `run.json` nor
the run README carries a receipt line. This is the exact failure `CLAUDE.md`
has a standing rule against — prose naming a mechanism has to name the tense it
runs in — and it sat under a heading called Verification.

**The records do not carry "the arm".** The Observability paragraph lists it
among the fields. `records-gepa.jsonl` and `records-skillopt.jsonl` both hold
`arm: "candidate"` on all 728 rows, and the A/A pass holds `arm: "placebo"`.
A reader rebuilding the two accuracy tables as the appendix describes cannot
separate the two evolved arms, or the A/A from its own control. `study.py` says
so in a comment; the paper did not.

**The paper printed the vacuous version of its own distractor criterion.**
"A distractor qualifies only if the computed solution is provably invariant to
its removal." `generators/audit.py` explains at length that this is trivially
true of every fact in this generator, load-bearing ones included, which is why
the implemented check is variable overlap instead. The paper published the
phrasing the code was written to avoid.

**"The repository refuses commits under any address but one"** is false three
ways: it is a blocklist of one domain, it reads working config at gate time
rather than any commit, and the log carries two addresses. It was offered as the
reason ancestry cannot be gamed, which it is not; the ancestry argument stands
without it.

**And the screen that justifies the model choice ran after it.** Both the
introduction and the limitations said the 1.7B target was "chosen because" every
larger model ceilings. `ceiling.tex` says the screen came after the study. In a
paper whose second headline is that we failed to compute something before a run,
that ordering had to be stated rather than smoothed.

Eleven more sat in run READMEs and repository furniture: a precision column
scored to v1 under a README declaring v2, a negative-observation count from the
same stale key, "380 adjudication calls" that are 361, "five" that is four,
"18 discards" that are 19, "eight trivial features" that are eleven, "82 prompt
files" that are 80, a reliability bin holding nothing, an answer key that does
not cover the item it reports, three scripts and a data file listed as present
that do not exist, CI described as running on every push, "that is the whole
install" for an install that also needs the `claude` CLI and npm, and a
pre-commit comment calling a nineteen-step gate four steps. Run READMEs took
appended corrections; the rest took edits.

## Ten cycles, final count

160 defects. No arithmetic error in any of them. Seven independent
re-derivations now, and one of these agents regenerated every artefact under
`paper/generated/` and `paper/figures/` byte-identical to what is committed, so
the PDF is not stale against the records.

The thing worth writing down after ten cycles is narrow. The numbers were right
from the first cycle and have never moved. What was wrong, 160 times, was
sentences: about what the numbers mean, about what the code does, about what the
repository contains, and — increasingly, as the cycles went on — about what the
previous cycle's fix had just established. Reading a claim is not checking it,
and the checkable ones are the ones you can run.

## Cycle eleven: five findings, four of them in cycle ten's own prose

Thirty-one down to five, and the shape is unchanged. Four of the five are
sentences the previous cycle wrote that afternoon.

**The isolation-receipt fix corrected one paragraph and left the same claim
twenty lines below it.** Cycle ten rewrote the Verification paragraph to say the
study path never calls `isolation_receipt` and that we would rather say so than
let the mechanism's existence read as its use. The closing paragraph of the same
appendix then said the hosted tier's absent card "is recorded as *no receipt
obtainable*". Nothing is recorded: `grep -ril receipt results/evolution-study/`
returns nothing, and the screen artifact's schema has no such field. The fix
stated the principle and then broke it in the next paragraph.

**The colliding-pair fix resolved one pair.** Cycle ten's own commit message
named both — the two evolved arms record `candidate`, and the A/A pass records
`placebo` — and the prose it wrote covered only the first, presenting the hash
as the disambiguator. For the A/A pass the hash does not disambiguate either:
`records-aa.jsonl` and `records-placebo.jsonl` are identical in both fields,
`16ed9ebfceb9` on all 728 rows of each. `figures.py` says it in bold: the arm is
the file name, not the record's `arm` field.

**"Refuses a commit" survived its own diagnosis.** Cycle ten's commit message
said the gate reads "working config rather than any commit, over a log carrying
two addresses", and the replacement sentence it wrote still said the gate
"refuses a commit". `check_git_identity` runs `git config user.email`. In CI the
workflow sets that value itself two lines before invoking the gate, so there the
check validates what the workflow just wrote.

**And the exception the same commit added was one of two.** The appendix called
the admission-rule subsection "the one exception" among typed study figures;
`method.tex` types a second, `gepa` by 0.35, which is two study macros
subtracted. Replaced with the two macros, which removes the exception rather
than documenting it. The counterpart sentences also disagreed about scope: one
said skew, the other skew and informedness, and informedness is generated and
printed in the template table.

## Eleven cycles

165 defects. Still no arithmetic error. The convergence is real — 31, then 5 —
but the composition has not changed at all: from cycle seven onward, the modal
defect is a sentence written to repair a defect, and the most reliable predictor
of where the next one is remains "wherever the last fix touched".

## Cycle twelve: three findings, two of them a word I deleted

Five down to three, and two of the three are one edit of mine from cycle eleven.

**I dropped "per-template" and made a true sentence false in three places.**
Cycle eleven's fix rewrote "emits no per-template skew macro" as "emits no macro
for skew". `de figures` emits five skew macros — `\meanSkewOff` through
`\meanSkewSkillopt` — and `signal.tex` cites two of them a page earlier. The
asymmetry the sentence was reaching for is real and is per template:
`tables.tex` carries a per-template informedness table and no skew of any kind.
The qualifier was the whole content of the claim and I removed it as noise.

The same edit also said the informedness beside those skew figures is
"generated". The figure in question, `+0.028`, is hand-typed with no `\NUM{}`,
because there is no per-template informedness macro either — only the table. So
the class-4 entry I had just added to the paper's own typed-number register
covered skew and left a typed informedness in no class, while asserting it was
generated.

**And the arena separation is not enforced in code for this run.** `method.tex`
said "The separation is enforced in code rather than by discipline, and it cuts
against us here." An AST scan of the whole `evolution/` package finds no import
of `arenas`; the two mentions are docstrings. `de study` calls neither
`assert_model_allowed` nor `assert_may_emit_verdict`; their callers are
`scripts/run_triggers.py` and friends, plus `tests/unit/test_locks.py`. No
arena error could have fired on this run. The registry is data the authors
honoured, which is exactly the "discipline" the sentence contrasted itself
against — and the paper is scrupulous about this distinction in five other
places, which is what made this one visible.

## Twelve cycles

168 defects, no arithmetic error, seven independent re-derivations. The count is
converging cleanly now — 31, 5, 3 — and the composition has not moved since
cycle seven. Two of three this round were mine from the previous round, and the
mechanism was the same both times: a fix that generalises. "No per-template skew
macro" became "no macro for skew" because the shorter sentence reads better, and
the deleted word was carrying the truth of it.

## Cycle thirteen: the prose was clean and I had reported a red gate as green

Cycle thirteen cleared both fix commits by execution — every sentence cycles
eleven and twelve wrote checks out, and a scan of every decimal literal in
`paper/sections/*.tex` outside a `\NUM{}` found each one inside an enumerated
provenance class. The prose vein has closed.

**It found the gate red at HEAD instead.** `de check` exits 1: `docs/METHODS.md`
names thirteen dependencies that have moved in eleven commits since it was last
read, over a ceiling of ten. The count was nine at `31ee70a`, ten at `ffed233`
— exactly the ceiling, still passing — and eleven at `e780118`. Cycle twelve's
own edit to `method.tex` is the commit that tipped it, and `e780118`'s message
says "23/23 gate steps".

I ran the gate before committing, saw green, and wrote the number down. The
drift step counts commits, so a run in the working tree cannot see the commit
that is about to exist. `CLAUDE.md` has a standing rule for this — commit, do
not stage, because a gate that runs in the working tree cannot see what the
commit is missing — and I have now broken it twice in this session, both times
by reporting a figure I had measured against the wrong object.

**The drift read was not a formality.** `docs/METHODS.md:525` said "Arms
interleave per item rather than running in blocks, so arm is not confounded with
model drift or quota state." That is the exact claim `runner.py` was corrected
for on 2026-08-28, which the paper reports as a design defect and which the run
README, the limitations section and the harness appendix all now disclose.
`METHODS.md` had kept the false version through six cycles of auditing, because
no cycle read it: it is a gated document and the gate that would have surfaced
it is the one I had been letting run late.

That is the argument for the drift ceiling, made against me. The mechanism found
a false sentence that thirteen adversarial reviews did not.

## Thirteen cycles

169 defects. The prose is clean, the arithmetic was never wrong, and the last
defect of the run was a stale claim in a document the gate had been telling me
to read.

## Cycle fourteen: zero blocking findings

The first cycle to return clean. It re-derived the two stamps rather than
trusting them — a stamp recording a read that did not happen would make a
register the project depends on false — and confirmed both: every clause of the
new `docs/METHODS.md` sentence checks against `runner.py` and `study.py`, and
none of the four documents stamped at `39731e3` makes a claim that anything
moving under them falsifies. Then a referee's pass over the PDF end to end:
abstract against sections, six contributions against the sections that deliver
them, and the places redundancy hides contradiction. Nothing.

**One correction to `39731e3`'s commit message.** It says three files moved
under the four documents. Four did: `site/build-manifest.json` is a fourth, a
generated hash manifest no document makes a claim about. The stamps stand and
the message undercounts. Recorded here because a commit message is not editable
and this register is the thing the drift gate rests on.

## What fourteen cycles cost and what they bought

169 defects. Not one of them was a number. Seven independent agents recomputed
every macro from the raw JSONL and one regenerated every artefact under
`paper/generated/` and `paper/figures/` byte-identical to what is committed, so
the arithmetic was right on the day it was written and never moved.

What was wrong, 169 times, was sentences: about what the numbers mean, what the
code does, what the repository contains, and — from cycle seven onward, more
than any other class — about what the previous cycle's fix had just established.
The defect rate per cycle fell 31, 5, 3, 1, 0. The *composition* never changed.

Three things worth carrying:

**Reading a claim is not checking it.** "Two blocks precede the arm's body"
survived ten readings of the prompt appendix and died the first time somebody
ran `build_arm`. Every one of the highest-severity findings in this run was a
claim about the repository that nobody had executed.

**A fix is a new claim.** It inherits none of the verification of the sentence
it replaces, and it is written under the confidence of having just been right
about something. The specific mechanism, seen four times: a fix that
generalises. "No per-template skew macro" became "no macro for skew" because the
shorter sentence read better, and the deleted word was carrying the truth.

**The gate found what fourteen adversarial reviews did not.** `docs/METHODS.md`
had said arms interleave per item since long before the study proved otherwise.
No cycle opened that file. The drift ceiling had been naming it every run, and I
had been treating the worklist as bookkeeping.
