# Fourteen truth cycles and not one prose review is how a paper gets this way

**2026-08-31.** The maintainer read `paper/main.pdf` and called it unreadable,
and the diagnosis took one look at the review record to confirm. Every one of
the fourteen audit cycles asked whether a sentence was true against the
records. None asked whether the paper was readable, whether it had one thesis,
or whether it should say "an earlier draft of this paragraph said" in print,
eight times. The house pipeline for prose, `docs/VOICE.md`, the humanizer
pass and the three review briefs, had never been run on `paper/`, because
`paper/` sits outside every content gate and the standing obligation that
routes prose through that pipeline was only ever applied to files a gate
reads. The result was a paper that was locally true 169 patches deep and
globally six papers interleaved.

This entry records the restructure that fixed it, the first-hand
re-verification of the cited papers that fixed the related-work section, and
what each pass found.

## The audit before the rewrite

Two agents read the paper end to end before anything moved, one for coherence
and one for the production history. The coherence audit found: six competing
theses, three of them introduced with the same "the more useful result"
escalation; eight published self-retractions narrating the draft history; the
$p$-floor argument told four times and owned by none of its tellings; roughly
2,800 of 14,099 body words being second and third tellings; ten hard
contradictions, among them a family size stated as three in the abstract and
"three of six primaries" in the contributions, and a body described as gone
and unexplainable in one subsection and quoted in detail two subsections
later; and `ceiling.tex` at 1,715 words about a different model, a different
template set and a different evidence class, sitting between the results and
their discussion.

## What the restructure did

One writer, the whole paper in context, which is the opposite of how the 169
patches were applied. The order is now introduction, related work, corpus,
method, results, discussion, limitations, with the harness and prompt
appendices unchanged in role and the ceiling post-mortem demoted to a third
appendix behind a 200-word summary in the discussion. The signal section
folded into results as a subsection, since it is a re-analysis of the same
records. The thesis is one sentence: the engines and their literature lack a
placebo and pre-run power arithmetic, and this study, which had the first and
computed the second too late, is evidence for both. The eight retractions,
the "we did not read the full paper" confession, the "weakest thing in this
paper" self-directions and the drafting-history narration are gone from the
print surface; the record of every one of those corrections stays in this
notebook and in `docs/STATUS.md`, where a correction belongs.

The withdrawn search figures from the 2026-08-31 audit ("20 of 21", "eight of
ten", the 14.3% flip rate) are no longer named in the paper at all. The
withdrawal stands in the audit entry; the paper now carries one provenance
paragraph saying the winners' described contents are typed from dated
notebook entries, placed before the descriptions rather than 190 lines after.

## The citations were re-verified against full texts, and two records moved

Nine cited papers were fetched and read first-hand by sub-agents on
2026-08-31: SkillOpt, the Xu-Wu SkillsBench-subset study, the SkillsBench
benchmark, GEPA, the prompt-optimisation coin-flip audit, both harness
papers, the AGENTS.md study, the authoring paper, and Prompting Inversion.
The verification fields in `paper/refs.bib` carry the dated notes and the new
`quote_body` fragments. Two standing records were corrected by the read:

- The absence claim about SkillOpt, that no interval, significance test or
  correction appears anywhere, was recorded on 2026-08-13 as something an
  abstract cannot settle. A term search over the full text settles it: none
  appears. The paper now states it from the full read instead of confessing
  it cannot.
- The 2026-08-13 note that "the ETCSOVG expansion is ours, not the paper's"
  was wrong about the headings: the harness-disclosure paper's Appendix A
  mandates exactly those seven layers. Only the acronym is ours. The
  correction is appended to the entry's verification field.

The read also corrected the paper in the other direction: "hundreds of times
in a run" for SkillOpt's ratchet is unsupported (the paper's own figure is 11
to 44 committed edits) and is gone; GEPA's reflection covers successes as
well as failures and its frontier is per instance, not over rollouts; the
Xu-Wu study is a controlled study on a SkillsBench subset and is no longer
called "SkillsBench" as if it were the benchmark.

## The review pipeline ran, and what each pass caught

The order was the one `docs/VOICE.md` prescribes: humanizer during writing,
then a truth cycle, then HOUSE_STYLE, POSITIONING and COLD_READER briefs to
separate agents, then a second truth cycle over the fixes.

The first truth cycle found 26 defects in the rewrite, which is the pattern
the fourteen-cycle audit predicted: fixes introduce defects. The two worst
were mine: the abstract paired `\mdeRatio` with the unseen clustered MDE when
`de figures` computes it against the smaller, seen figure, and the falsifier
was described as a harness mechanism when it is a protocol rule checked by
hand. Both are the defect classes the audit had already named, a deleted
qualifier that was carrying the truth, and a discipline stated as code. The
placebo claim in the abstract had also quietly pooled the item sets the paper
refuses to pool; it is now scoped to the seen set.

The cold-reader test passed on all seven diagnostics. The positioning review
found the paper underselling its two rarest assets, the machine-verified
pre-registration and the pre-study probe that predicted the memorisation
channel, and both now sit in the abstract and the contributions. The style
review counted the banned patterns down from 47 "rather than" and 20 "and
not" to a residue where each surviving instance carries a distinction that is
the point.

## What should change so this does not recur

`paper/` is still outside every content gate. The gate gap is recorded in the
audit entry of this date and in `docs/STATUS.md`; the fix that belongs to
this entry is narrower: the standing obligation in `AGENTS.md` already says
all prose goes through the voice pipeline, and the lesson is that "all prose"
has to include the prose no gate reads, because that is exactly the prose
that leaves the repository.
