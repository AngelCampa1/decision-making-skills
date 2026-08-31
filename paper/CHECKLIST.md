# Reproducibility checklist

**Audience:** the evaluating reader.

**What this is.** The NeurIPS-style reproducibility checklist, filled in as the
work happens rather than the week before submission, and kept in the repository
so the gap between what is claimed and what exists is visible at every commit.

`[x]` means the artifact exists and is committed; `[ ]` means it does not. A box
is never ticked on the strength of an intention. Two boxes below are marked
**blocked**: they need someone outside this repository, and a blocked box is
still an open box. A third was blocked on this machine having no TeX toolchain,
and installing one closed it.

Last worked through 2026-08-28, against the five-arm study at
[`../results/evolution-study/2026-08-27-53b4965-five-arm/`](../results/evolution-study/2026-08-27-53b4965-five-arm/).

## Claims

- [x] Every claim in the abstract and introduction is supported by a numbered
      result or a citation. Numbers about our own runs are `\NUM{\macro}` from
      `generated/macros.tex`; numbers from other people's papers carry a
      citation whose `refs.bib` entry carries the quote they came from
- [x] The scope of the claims matches the experiments: one harness, one model
      at 1.7B parameters, tasks with computable ground truth. Stated in the
      abstract, again at the end of the introduction, and enforced by the arena
      rule that declines to issue a verdict from this tier
- [x] Limitations are stated in the paper, not only in the repository:
      `sections/limitations.tex`.
      Source: [`../docs/LIMITATIONS.md`](../docs/LIMITATIONS.md)
- [x] Limitations were written *before* results existed, so they cannot be
      tuned to flatter them

## Experimental design

- [x] Standing protocol is versioned and public:
      [`../docs/PROTOCOL.md`](../docs/PROTOCOL.md), now v2. **The run reported
      here was conducted under v1**, and the paper says so where it describes
      the method. v2 added the corpus-admission criteria that this study's own
      failure produced, after the fact
- [x] Hypotheses pre-registered before the run, in a dated `notebook/` entry
      committed before the first call. One amendment was appended mid-run,
      after 143 of 4,368 calls and before any comparison was read, and it is in
      the entry rather than in a commit message
- [x] Pre-registration commits are ancestors of the result commits, verifiably.
      Not asserted: `de check`'s `provenance` step refuses a published run
      whose prediction entry's first commit is not a git ancestor of the run's
      commit
- [x] Skill body hashes locked. Every arm's body is SHA-256'd and the hash is
      on every one of that arm's 728 records and in `run.json`
- [ ] Analysis script hash locked in the pre-registration. The analysis code is
      committed and the run names its commit, which is weaker: nothing stops a
      later commit from changing `analyse` and nothing would notice
- [x] Stopping rule fixed in advance; no interim analysis. `max_calls` and
      `max_seconds` are in the request recorded in `run.json`, and the
      comparisons were computed once, at the end
- [x] Control arm and placebo arm specified and run
- [ ] Plain-CoT arm specified but **not run, and refused on this backend**. A
      reasoning model reasons whether or not the prompt asks, and emits the
      chain in a separate field, so a `cot` arm here would differ from `off` in
      what was requested and not in what the model did
      ([`../docs/HARNESS_DISCLOSURE.md`](../docs/HARNESS_DISCLOSURE.md))
- [x] Response-format contract specified as common to every arm, assembled by
      one function with no way to omit it
- [x] Option menus held constant across arms. The user message is
      arm-independent by construction

## Statistics

- [x] Test chosen for the data type: McNemar exact (paired binary), paired
      permutation (continuous)
- [x] Intervals from a cluster bootstrap over templates, not items
- [x] CLT deliberately avoided at this N, with the reason recorded
- [x] Multiplicity controlled across the pre-registered primaries. Holm across a
      registered family of three, applied in the run's own analysis and
      reported in both tables. *Corrected 2026-08-28: this box carried a long
      note saying no confirmation run had produced a family of primary
      p-values. A family of three was produced and corrected on 2026-08-27.*
      Benjamini-Hochberg remains implemented, 100%-covered, exported from
      `stats/__init__.py`
      ([`../evals/src/decision_evals/stats/multiplicity.py`](../evals/src/decision_evals/stats/multiplicity.py)),
      and called by nothing. Holm was the right choice for a family of three
      primaries and BH is still waiting for the family it was written for
- [x] Guards left uncorrected by design, with the asymmetry stated.
      The design rationale is committed prose
      (`stats/multiplicity.py` module docstring), true independent of whether
      the correction above has ever run
- [x] Raw p and adjusted q both reported for every primary, in the same table
- [ ] Effect sizes reported with intervals, never p-values alone. **Half done.**
      The signal table reports cluster-bootstrap intervals on every ΔJ. The two
      accuracy tables report the effect and the test with no interval around
      the effect, because the run's analysis did not compute one and
      `de figures` renders that file rather than reanalysing it. Closing this
      means re-running the analysis, not editing the paper
- [x] Underpowered comparisons reported as `UNTESTED` with their MDE, not as
      nulls. This box read "`stats/power.py` computes an MDE and this study did
      not report one" until 2026-08-31, and that was false about the
      pre-registration: the MDE was computed before the first call, at 0.081
      unseen and 0.075 seen, and recorded in the prediction entry. What was true
      is that the paper never carried it. `limitations.tex` now reports both,
      beside the largest effect observed, and beside the same figure recomputed
      at the design effect `PROTOCOL.md` specifies. The nulls remain reported as
      failures to reject rather than as nulls
- [x] Statistical code covered at 100% line and branch, with property tests
      pinning McNemar against `scipy`. `stats/signal.py`, added 2026-08-28 for
      the decomposition, inherits that floor and meets it, as does
      `figures.py`.
      Benjamini-Hochberg is a thin wrapper around `statsmodels`, not an
      independent implementation checked against it, so nothing here pins
      against `statsmodels`; that self-referential test was deliberately
      removed (`tests/property/test_stats_properties.py`,
      `TestBenjaminiHochberg.test_rejections_agree_with_the_adjusted_values`)
- [ ] Coverage simulation: 1,000 simulated clustered datasets with known Δ,
      empirical 95% CI coverage in [0.93, 0.97]
- [x] **One unit of analysis, named before the run and used after it.** Added
      2026-08-31 because this study did not have one. `method.tex` paired on
      items and `limitations.tex` said templates were the independent unit, and
      nothing reconciled the two until the run was over. Both units are now
      reported side by side (`sec:clustered`), and the correction is stated in
      the limitations rather than quietly applied
- [x] **Attainable p-floor computed from the cluster count before the run.** A
      one-sided exact test over k clusters cannot return a p below 2⁻ᵏ. Added
      2026-08-31 after the arithmetic showed three of this study's six
      registered primaries could not have rejected at any outcome: the unseen
      set is three templates and floors at 0.1250. `de figures` generates
      `\floorUnseen` and `\floorSeen` so no future run can omit them
- [x] **The estimator answers the question the prose asks.** Added 2026-08-31.
      Three independent agents recomputed every macro in this paper and all
      three matched; none checked whether accuracy on a balanced key contains
      the quantity the signal section claimed to extract from it. It does not:
      accuracy is (J+1)/2 there and response bias contributes nothing. A number
      can be correct and still answer nothing, and no gate in this repository
      reads for that

## Data

- [x] Eval-set datasheet: [`../docs/EVAL_SET_DATASHEET.md`](../docs/EVAL_SET_DATASHEET.md)
- [x] Ground truth computed from template rules, never authored
- [x] Template schema published in full. The ten templates are committed as
      YAML at [`../datasets/templates/`](../datasets/templates/), the generator
      that reads them is committed beside the harness, and golden-file tests
      pin what the pair produces
- [ ] Distractor audit procedure and attrition rate reported. The structural
      half is done (50/50 pass); the semantic half is pending local auditor
      models, and the 2026 GSM-Symbolic re-audit says it is the half that
      matters
- [ ] Difficulty gates run on the control arm only, and stated as such. The
      criteria exist as of protocol v2 and nothing computes them yet, so this
      **will refuse** a template rather than refuses one
- [x] Split committed. Templates are split by
      `sha256("evolution-study-v1:<template_id>")` and both sides are listed in
      `run.json`, with a corpus fingerprint per set
- [x] Holdout seeds published rather than withheld, in `run.json`, alongside the
      corpus fingerprints they generate. Contamination is managed by
      regenerating between runs rather than by secrecy
- [x] Generator output pinned by golden-file tests; regeneration requires an
      explicit bless step so the diff reaches review

## Code and environment

- [x] Code public from the first commit:
      `github.com/AngelCampa1/decision-making-skills`
- [x] Apache-2.0 for code: [`../LICENSE`](../LICENSE)
- [x] CC-BY-4.0 for the paper: [`LICENSE`](LICENSE), the full legal code, with
      the notice on the title page of `main.tex` and an SPDX line on `refs.bib`
- [x] Dependencies pinned via `uv` lockfile
- [x] Full local gate (`de check`) runs lint, types, tests, coverage floors
- [ ] **Blocked on the maintainer.** Zenodo DOI minted for the code and data
      release. Nothing in this repository can do it
- [ ] Exact CLI version and resolved model id recorded per run. The resolved id
      is recorded **per call**, read from the response's own `model` field
      rather than from the request. There is no CLI version to record because
      this study did not run through a CLI, so the box is open on a criterion
      that does not apply to it rather than on a missing artifact

## Harness

- [x] ETCSOVG disclosure documented:
      [`../docs/HARNESS_DISCLOSURE.md`](../docs/HARNESS_DISCLOSURE.md), and
      reproduced for this backend in the paper's own appendix
- [x] Per-run manifest written and committed with results: `run.json`, carrying
      the request, the arms and their hashes, the seeds, the templates and the
      corpus fingerprints. *It is named `run.json` rather than `config.json`;
      the box previously named a file that never existed*
- [ ] Isolation canary test passing. On the CLI backend a planted `CLAUDE.md`
      is a live measurement and `--setting-sources ""` blocks it. On this
      backend the analogue is Ollama's `/api/show` card, refused when it
      carries a `SYSTEM` prompt, which is a receipt rather than a canary.
      Nothing plants a file and checks it is ignored here, because nothing
      here reads the filesystem
- [ ] ≥2 independent runs per cell, with variance reported. One pass per arm.
      The control arm has a second pass, the A/A, and it is the only cell with
      a repeat
- [ ] **Arms interleaved per item, not run in blocks.** Arms ran in blocks.
      `runner.iter_items` returns the item-major ordering and the study path
      never calls it, found 2026-08-28. The A/A bounds the exposure and does
      not remove it, and the paper reports both
- [x] Absence of sampling-parameter control stated rather than worked around
- [ ] Every setting that affects a call written into the run manifest.
      `keep_alive` and `temperature` are provider defaults and are not in
      `run.json`, so a replicator reads those two from the source

## Reporting

- [x] Exact prompt text published for every arm, in the paper's appendix, with
      the shared prefix, one fully rendered item, and the content hash per arm
- [x] Full transcripts published, not scores alone. Every record carries the
      complete response text, the parsed answer and the parse status: 3,640 arm
      records and 728 A/A records, committed
- [x] Placebo text published beside the skill it stands in for, with its length
      and section count reported against the skill's. The match is checked on
      word count within 15%; a token count would be the better measure and is
      not what the check reads
- [ ] Every evaluated skill body published at its pre-registered hash. **Three
      of five.** `off` is empty, and the seed skill and the placebo are
      committed and recompute to the hashes in `run.json`. The two evolved
      winners were written into a gitignored directory, were never committed,
      and a content-hash search of the machine on 2026-08-28 did not find them.
      The hashes are on every record; the bodies are gone. This is the worst
      open box on this page and it cannot be closed
- [ ] Means reported with p90 and p99. Accuracy on a binary key has no p90, and
      the latency distribution that would is not a result this paper reports
- [x] Negative results reported at the same prominence as positive ones. The
      discussion closes on them: our own skill lost to the placebo on both
      sets, three registered predictions were falsified, three of ten templates
      measure nothing, and the headline could not be replicated at a tier that
      carries a verdict
- [x] Figures generated from `results/` by `make paper`, never transcribed.
      `de figures` writes every macro and every table. Three classes of number
      are typed and each is identified in the prose: figures from cited work,
      configuration constants, and the sub-agent probes that wrote no records.
      `main.tex` lists them
- [ ] Committed scorecard matches the results. No `de report` command exists
      yet; a future one would check this, and until it does the match is
      asserted by hand

## Submission logistics

- [ ] **Blocked on the maintainer.** arXiv endorsement for `cs.AI`/`cs.CL`
      confirmed. **Check early, it can take weeks**
- [x] `\draftmode` switched off, so `\TODO` expands to nothing, and no `\TODO`
      survives anywhere in the source
- [x] All `% VERIFY` author lists in `refs.bib` checked. All eleven were read
      against arXiv's own metadata on 2026-08-28 and the markers cleared. Four
      carried a title that did not match the paper at the id recorded beside
      it, one of those four was a different paper's title entirely, and eight
      had no author list at all. All are corrected
- [x] Author, affiliation, and contact match the repository identity
      (Angel Campa, `AngelCampa1`)
- [x] No `@ventoralabs.com` address anywhere in the source or in the commit
      history. PDF metadata inherits `\author`, which carries no address
- [x] `make paper` compiles. TinyTeX 2026.08, GNU Make 4.4.1 and poppler 26.02.0
      are installed per-user outside the repository, and none of it is a
      dependency of the gate. From a clean worktree the build is 22 pages and
      408,470 bytes with no overfull or underfull boxes, no LaTeX warnings and
      no BibTeX warnings. Every `\input` target exists, every `\label` a `\ref`
      or `\Cref` names is defined, every `\cite` key resolves in `refs.bib`,
      every `\NUM{\macro}` resolves against `generated/macros.tex`, and no `??`
      survives into the output. Six defects that only a renderer could find were
      fixed in the same pass and are listed in
      [`../docs/STATUS.md`](../docs/STATUS.md)
