# The static checks passed and the first real compile found six defects

**2026-08-28.** The paper was written, checked and declared complete on a
machine with no TeX on it. Every check that could be made without a renderer was
made and passed: every `\input` target exists, every `\label` a `\ref` names is
defined, every `\cite` key resolves, every environment balances, every
`\NUM{\macro}` resolves against `generated/macros.tex`. The checklist box for
`make paper` was left open and marked blocked, which was the right call, because
the checks were not a substitute for the thing they stood in for.

A toolchain now exists. TinyTeX 2026.08, GNU Make 4.4.1 and poppler 26.02.0,
installed per-user under `D:\tools\`, no administrator rights involved and
nothing added to this repository. `paper/Makefile` was already written against
`latexmk` and worked unchanged.

## What the compile produced

From a clean worktree at `origin/main` with the paper's changes applied and
`paper/generated/` and `paper/figures/` deleted first: 22 pages, 408,470 bytes,
no overfull or underfull boxes, no LaTeX warnings, no BibTeX warnings. The
second build in a different tree produced the same page count and the same byte
count. `pdftotext` over the output finds no `??`, no stray control sequence and
no `TODO`.

## The six defects

Every one is invisible without a renderer, and five of the six would have
shipped.

**Fifty-one internal audit notes were being typeset into the bibliography.**
`refs.bib` carried 74 `note` fields. Around fifty were our own working records:
line numbers we read, what we could not verify first-hand, which entry had been
corrected and when. `plainnat` prints `note`, so all of it was going into the
reference list of the artifact that leaves the repository. BibTeX silently
ignores fields it does not know, so those fields are now `verification` and the
23 that are genuine bibliographic detail stay as `note`. The classifier was
written, run, read, and then corrected: its first pass matched on capitalised
runs and pulled in `RLHF`, `EMNLP`, `CALM` and `MAST` as though they were file
paths.

**The strongest effect in the paper rendered with two plus signs.** `_signed()`
in `figures.py` emits the sign into the macro. Four sentences added their own,
including the abstract's headline number.

**Two generated figures were dead build output.** `de figures` writes
`paper/figures/accuracy.tex` and `paper/figures/signal.tex` from the committed
records, and nothing in the document ever `\input` either. The paper had three
tables and no figures. Both are now `\IfFileExists`-guarded floats, in the
results section and the signal section, so a bare checkout still compiles.

**T1 Computer Modern ships as bitmaps** unless `cm-super` is installed, and
microtype's font expansion then refuses to run and says so on every build.
Naming `lmodern` in the preamble costs a replicator one package fewer rather
than one more.

**The licence notice was a hand-rolled footnote** under an emptied
`\thefootnote`. It renders correctly, which is why nothing noticed, and it hands
hyperref an anchor it cannot name on every build. It rides on `\thanks` now,
which is the mechanism designed for a title-page footnote. `\thanks` is a moving
argument, so the URL inside it needs `\protect`.

**The PDF carried no metadata.** A viewer's title bar and an indexer both read
the document information dictionary, and left empty it says "LaTeX with
hyperref" and nothing else. Title, author, subject and keywords are set from
`\hypersetup`. Checked separately: no `@ventoralabs.com` address survives into
the file.

## What this says about checking without the tool

The static checks were not wrong. Everything they asserted was true, and none of
them was the check that mattered. They covered the failures that break a build,
and every defect here is one that a build tolerates: a field that prints when
you meant it not to, a sign that appears twice, a file that nothing reads, a
warning nobody sees, an anchor with no name, a dictionary left empty.

The reusable version: a check that stands in for a tool tests what the tool
would refuse, and a tool refuses far less than it reveals. Reporting the box as
blocked rather than ticking it on the strength of the substitutes was the part
that held.

Two boxes on `paper/CHECKLIST.md` are still open and both need the maintainer:
arXiv endorsement for `cs.AI` or `cs.CL`, and the Zenodo DOI.
