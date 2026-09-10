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
2. Tag the landed commit. The title page names a release, so the tag must
   point at the commit the package was built from:

   ```bash
   gh release create v1.0.2 --title "v1.0.2: the seven-arm evaluation paper" --notes "Snapshot the arXiv preprint reports on. Paper source in paper/, run records in results/."
   ```

   `v1.0.0` was cut on 2026-09-02 at `1589826`, which is one commit before the
   acceptance-claim rewrite and the three added citations landed at `30a2dc1`.
   Its two assets are that earlier paper and stay as they are: they are what
   was published that day. `v1.0.2` is the release the title page names and the
   one to upload from.

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
| Title | `Do Automated Skill Optimisers Survive a Placebo Control? A Pre-Registered Seven-Arm Study of GEPA and SkillOpt across 14,700 Calls` |
| Authors | `Angel Campa` |
| Abstract | the block below, verbatim |
| Comments | `29 pages, 2 figures, 4 tables. Code, data and every run record: https://github.com/AngelCampa1/decision-making-skills (release v1.0.2)` with a space after the URL. No copyright line here; arXiv forbids one in this field |
| Primary category | `cs.AI` |
| Cross-lists | `cs.LG`, whose description names evaluation methodology, and `cs.SE` for the agent tooling. Not `cs.CL`: the paper is not natural-language processing. Moderators add and strip cross-lists either way |
| ACM class | optional; `I.2.7` if any |
| License | **CC BY 4.0.** It matches `paper/LICENSE` and the title-page notice, and the choice is irrevocable per version |

The abstract field refuses more than 1,920 characters. This one is 1,785. It
was read against `generated/macros.tex` on 2026-09-10 and must be read again
if the macros change:

```text
Two open-source engines, GEPA and Microsoft's SkillOpt, automatically rewrite the markdown "skill" files that agent tools load, accepting edits on single unreplicated score comparisons. Their evaluations lack two cheap controls: a placebo of matched length and structure whose content says nothing, and power arithmetic from the design before the run. We report the first placebo-controlled evaluation of automated skill optimisation, pre-registered under a gate enforcing that predictions predate data by git ancestry. We evolved a decision-making skill with each engine against ollama/qwen3:1.7b, then ran seven arms across two deterministic passes over a fresh holdout: no skill, the initial seed skill, a structure-matched placebo, two length-matched per-winner placebos, and the two evolved winners (14,700 calls in all). Comparisons are McNemar exact against matched placebos with Holm correction, on 588 unseen items across 7 held-out templates and 392 seen items across 7 trained templates, backed by template cluster sign-flip tests. No arm rejects on either set at the pre-registered dual bar (Holm q < 0.05, cluster sign-flip p < 0.0167). SkillOpt clears the item unit on unseen scenarios (+0.0918, Holm q = 0.000086) but fails cluster sign-flip (p = 0.0313). GEPA clears the item unit on seen scenarios (+0.0510, Holm q = 0.0280) but fails cluster sign-flip (p = 0.0781). Both winners wrote training constants into their bodies; an ablation probe confirms seen-template gains collapsed without hardcoded numbers. An empty prompt beat the seed skill by 6-7 points: prompt text provoked runaway generations. Pass agreement was 100%, and an A/A control returned 980 of 980 identical. Template clustering eliminates false discoveries; both controls belong in skill evaluations.
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
