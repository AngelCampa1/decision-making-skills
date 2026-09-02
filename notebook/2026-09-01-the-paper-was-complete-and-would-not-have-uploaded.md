# The paper was complete and would not have uploaded

**2026-09-01.** The day after the restructure landed, the maintainer asked how
to publish it. Working through arXiv's current rules against the actual files
turned up three things that would have stopped the upload and one that would
have risked it, none of which any gate reads, because `paper/` is outside all
of them.

**The abstract does not fit the form.** arXiv's metadata field refuses more
than 1,920 characters, and the abstract in the PDF is about 2,890. The PDF may
keep its abstract; the form needs a shorter one. A 1,914-character version now
sits in `paper/SUBMISSION.md`. It is a hand-typed copy of macro values, which
is exactly the class of text the 2026-08-31 truth cycle caught a defect in, so
every figure in it was read against `generated/macros.tex` and the 2.6 ratio
is paired with the seen-set MDE it was computed from and not the unseen one.

**The bibliography on disk was stale and arXiv does not run BibTeX.**
`main.bbl` is gitignored. The copy on this machine predated the `refs.bib`
change that gave `skillsbench2026li` an author list, and a compile from that
`.bbl` renders the citation as `[?]`. Nothing noticed because `make paper`
runs BibTeX and overwrites it, and the PDF on `main` was built in a worktree
whose `.bbl` was fresh. `make arxiv` now rebuilds before it packs, and the
file set it packs was compiled with three passes of `pdflatex` and no
bibliography step: 27 pages, no warnings, no undefined references.

**`\date{\today}`.** arXiv rebuilds PDFs from source now and then, so the
printed date would have drifted. It is fixed at the submission date.

**No disclosure of the tool that wrote the prose.** arXiv's moderation policy
asks authors to report significant use of text-to-text generative AI, and in
May 2026 the CS section chair announced a one-year ban for unchecked model
output. This paper's prose was drafted and revised by Claude from the run
records, and it did not say so anywhere. An unnumbered section before the
bibliography now names the tool, what it did, where the numbers come from
instead, and who is responsible.

**Endorsement is the long pole.** Since 2026-01-21 an institutional address
no longer endorses a new author by itself; it takes that and a prior arXiv
paper in the domain, or a personal endorsement from an author with three
`cs.*` papers between three months and five years old. The maintainer has
neither, so this is a request to a stranger and it can take weeks. The
checklist and `SUBMISSION.md` both say so now, and the title page names
`release v1.0.0` instead of a DOI, so the paper does not wait on Zenodo.

What was not done: the account, the endorsement, enabling Zenodo, and the
release tag. Each needs a login this repository does not have. The order they
go in, and every value the form asks for, is `paper/SUBMISSION.md`.
