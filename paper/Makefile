# Paper build.
#
#   make paper    regenerate figures from ../results, then compile main.pdf
#   make arxiv    build, then zip the exact file set arXiv needs
#   make figures  regenerate figures and generated/macros.tex only
#   make watch    continuous rebuild while drafting
#   make clean    remove build intermediates (keeps main.pdf)
#   make distclean  also remove main.pdf and generated/
#
# The point of the figures dependency is that the PDF cannot drift from the
# data. Figures and every reported number are generated artifacts; editing
# them by hand is a defect, not a shortcut.
#
# Requires latexmk and a TeX distribution. `uv` is invoked as `python -m uv`
# because a pip-installed uv does not land on PATH on Windows. Where it is the
# other way round, `make UV=uv paper`.

UV      := python -m uv
LATEXMK := latexmk -pdf -interaction=nonstopmode -halt-on-error

.PHONY: paper arxiv figures watch clean distclean

paper: figures
	$(LATEXMK) main.tex

# arXiv does not run BibTeX, so the package carries main.bbl and not refs.bib,
# and it compiles from the root of the archive with pdflatex alone. This is the
# file set that was test-compiled that way on 2026-09-01, three pdflatex passes
# with no bibliography step: the source, the sections, the generated macros and
# tables, the pgfplots figures, and the bibliography as built. Nothing else. The
# .bbl is gitignored, which is why this target builds before it packs: a stale
# one on disk compiles to a `[?]` wherever refs.bib has moved since.
arxiv: paper
	rm -rf arxiv-submission arxiv-submission.zip
	mkdir arxiv-submission
	cp main.tex main.bbl arxiv-submission/
	cp -r sections generated figures arxiv-submission/
	cd arxiv-submission && zip -qr ../arxiv-submission.zip .
	rm -rf arxiv-submission
	@unzip -l arxiv-submission.zip | tail -1

# `de figures` reads the latest run under ../results/evolution-study/ and writes
# generated/macros.tex, generated/tables.tex and figures/*.tex. Everything is
# TeX rather than PDF: pgfplots draws the pictures, so a figure is a diff a
# reviewer can read and the build needs no plotting library. With no results
# present it emits an empty macro file and returns cleanly, which keeps the
# generator from erroring on a bare checkout. It does not make the paper build:
# main.tex guards both \input targets with \IfFileExists, so the missing tables
# are skipped silently, and what stops the build is that every \NUM would be
# undefined. Checked 2026-08-31; this comment first claimed the skeleton
# compiled, then gave the wrong reason it does not.
#
# This named ../results/**/summary.json until 2026-08-28. No such file has ever
# existed anywhere under results/, and nothing noticed for eighteen days,
# because the documentation gate reads *.md and docs/ and a Makefile is
# neither.
figures:
	cd .. && $(UV) run de figures --out paper

watch: figures
	$(LATEXMK) -pvc main.tex

clean:
	latexmk -c main.tex
	rm -f main.bbl main.run.xml
	rm -rf arxiv-submission arxiv-submission.zip

distclean: clean
	latexmk -C main.tex
	rm -rf generated figures
