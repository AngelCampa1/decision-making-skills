# Submitting the paper

**Audience:** the maintainer.

**What this is.** Everything the arXiv form and the Zenodo release need, in the
order they happen, with the values already worked out. The three steps that
need a login are the maintainer's; everything else is done and landed. Checked
against arXiv's help pages and the January 2026 endorsement policy on
2026-09-01; if it is much later than that, re-read
<https://info.arxiv.org/help/submit/index.html> before trusting the details.

## 1. Account and endorsement, today

1. Register at <https://arxiv.org/user/register>. The username is permanent.
   Affiliation may be "Independent"; the paper names no affiliation, only the
   repository.
2. Link an ORCID at <https://arxiv.org/user/confirm_orcid_id>.
3. Start a new submission, even with nothing uploaded. arXiv emails an
   **endorsement request** with a six-character code and a link.
4. Find an endorser: on the abstract page of a paper this one cites, click
   *Which authors of this paper are endorsers?* at the bottom. Any author with
   three `cs.*` papers between three months and five years old can endorse
   for `cs.AI`; the GEPA, SkillsBench and harness-disclosure authors are the
   natural asks. Send the code, the PDF and the repository URL. One positive
   endorsement covers the whole `cs.*` domain. arXiv staff cannot waive this
   or endorse on their behalf.

## 2. The release, once Zenodo is enabled

1. At <https://zenodo.org>, log in with GitHub, open the profile menu,
   **GitHub**, **Sync now**, and toggle `AngelCampa1/decision-making-skills`
   on. Zenodo reads `CITATION.cff` for the record's metadata; there is no
   `.zenodo.json`, so that file is authoritative.
2. Tag the landed commit. The title page says `release v1.0.0`, so the tag
   must point at the commit the package was built from:

   ```bash
   gh release create v1.0.0 --title "v1.0.0: paper submission" --notes "Snapshot the arXiv preprint reports on. Paper source in paper/, run records in results/."
   ```

3. Zenodo ingests the release within minutes and shows a version DOI and a
   concept DOI. The DOI goes in `README.md` and `CITATION.cff` after the paper
   is announced, not in the paper: the paper points at the tag, which does not
   depend on which service archived it.

## 3. The package

```bash
cd paper && make UV=uv arxiv
```

That writes `paper/arxiv-submission.zip`: `main.tex`, a fresh `main.bbl`,
`sections/`, `generated/` and `figures/`. It carries no `refs.bib`, because
arXiv does not run BibTeX, and no build intermediates. The same file set
compiled with three passes of `pdflatex` and nothing else on 2026-09-01.

## 4. The form

| Field | Value |
|---|---|
| Processor | TeX Live 2025, the default. This machine runs 2026; read arXiv's rendered PDF page by page, that is the one thing not tested locally |
| Title | `Do Automated Skill Optimisers Survive a Placebo Control? A Pre-Registered Five-Arm Study of GEPA and SkillOpt` |
| Authors | `Angel Campa` |
| Abstract | the block below, verbatim |
| Comments | `29 pages, 2 figures, 4 tables. Code, data and every run record: https://github.com/AngelCampa1/decision-making-skills (release v1.0.0)` with a space after the URL. No copyright line here; arXiv forbids one in this field |
| Primary category | `cs.AI` |
| Cross-lists | `cs.LG`, whose description names evaluation methodology, and `cs.SE` for the agent tooling. Not `cs.CL`: the paper is not natural-language processing. Moderators add and strip cross-lists either way |
| ACM class | optional; `I.2.7` if any |
| License | **CC BY 4.0.** It matches `paper/LICENSE` and the title-page notice, and the choice is irrevocable per version |

The abstract field refuses more than 1,920 characters. This one is 1,919. It
is a hand-typed copy, so it was read against `generated/macros.tex` on
2026-09-01, twice, the second time after the control-token re-read added
seven macros to it, and must be read again if the macros change:

```text
Two open-source engines, GEPA and SkillOpt, rewrite the markdown "skill" files that agent tools load, and both accept an edit on a single unreplicated score comparison. Their evaluations lack two cheap controls: a placebo of matched length and structure whose content says nothing, and power arithmetic from the design before the run. We report the first placebo-controlled evaluation of automated skill optimisation we are aware of, pre-registered under a gate that checks by git ancestry that the prediction predates the data. We evolved a decision-making skill with each engine against ollama/qwen3:1.7b, then ran five arms over a holdout minted after both winners were frozen: no skill, the seed, a matched placebo, and the two winners. Comparisons are McNemar exact against the placebo with Holm correction, on 336 unseen and 392 seen items, separately. No arm rejects on either set as registered. The best showing is SkillOpt at +0.0408 on trained scenarios, raw p = 0.0341, Holm 0.1022. The placebo beats the skill we wrote on both sets. Both winners wrote training-item constants into their bodies. An A/A control returned 728 of 728 items identical. Our scorer refused 87 answers that carried the model's thinking-mode switch, "ANSWER: monitor /think"; 84 named the key. Fifty-six fell on GEPA's winner, 29 on the empty prompt. Re-read with the token stripped, GEPA's winner rises from 0.6280 to 0.7440 on unseen scenarios and reads Holm q = 0.0497 against the placebo on trained ones at the item unit, 0.0469 uncorrected at the template unit. We report the re-read beside the registered figures and promote neither. Power arithmetic decides half of the null before the data: the template is the unit, the unseen set is three clusters, and a one-sided test over three admits no p below 0.1250. The minimum detectable effect at the protocol's design effect is 0.1137 unseen, 2.6 times the largest gain observed.
```

## 5. Timing and what happens next

Submissions in by 14:00 US Eastern, Monday to Friday, are announced at 20:00
Eastern the same day. After Thursday 14:00 the next announcement is Sunday
20:00. Labor Day, 7 September 2026, is on arXiv's deferral list. Edits before
the cutoff create no version.

A first submission from a new author is usually **held for moderation** for
some days. Do not resubmit. Reclassification is routine. A rejection can be
appealed through the user support portal; appeal decisions are final and come
with no feedback.

Once announced:

- `CITATION.cff` gets a `preferred-citation` block with the arXiv identifier
  and `README.md` a citation and the Zenodo badge.
- `docs/STATUS.md` gets an appended entry; it is never rewritten.
- A correction is a **replacement**, which makes v2 beside a v1 that stays
  visible for good, so the Comments field should say what changed.
