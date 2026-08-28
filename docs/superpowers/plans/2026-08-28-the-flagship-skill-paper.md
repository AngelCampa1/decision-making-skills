# The flagship skill paper, as it was outlined before any results existed

**Written 2026-08-10. Preserved here 2026-08-28, unchanged.**

`paper/` was scaffolded on 2026-08-10 as a complete argument with no data in it:
every section a comment block stating what it would say, what it must report,
and why, so that the outline could not be quietly bent to fit whatever the
numbers turned out to be. It describes a study of five skills evaluated through
the Claude Code CLI, with trigger-quality and wiring-mode ablations and a
council-versus-self-consistency comparison at matched token budget.

That study has no venue. Its subscription venue was ruled out by maintainer
instruction on 2026-08-26, and none of those ablations ran. On 2026-08-28 the
paper was retargeted onto the study that did run, the five-arm evolution study
of 2026-08-27, and these files were rewritten.

**This is the record of the outline, kept because the reasoning in it is worth
more than the sections were.** Several pieces have no home elsewhere: the
presence-versus-prose adjudication between SkillsBench and SkillOpt with the
SkillsBench null pre-registered as the prediction; the reporting rules fixed in
advance, including nulls at the same prominence as wins and underpowered
comparisons labelled `UNTESTED` with their MDE rather than presented as nulls;
and the three fairness invariants stated as the thing whose absence makes most
skill evaluations uninterpretable.

Nothing here is a plan of record. It is what one earlier version of this project
intended, left as written.

---

## `sections/introduction.tex`, as written 2026-08-10

```latex
\section{Introduction}
\label{sec:intro}

% ARGUMENT (fixed before results; the numbers are not):
%
%   1. Markdown "skills" are now a real distribution channel. The Agent Skills
%      standard has ~40 adopting products and a shared .agents/skills/ path.
%      Thousands of these files are installed and running.
%   2. Almost none of them carry evidence. The closest prior art ships 28
%      skills and its own README concedes none is proven to improve accuracy.
%   3. The 2026 literature disagrees with itself about whether the content of
%      such a file even matters: SkillsBench says presence is worth +18-36pp
%      and prose granularity +0.7pp with CIs crossing zero; SkillOpt reports
%      +23.5pp from optimising that same prose.
%   4. Meanwhile harness variance exceeds model variance by ~7.8x, so the
%      scaffold is the dominant term and almost nobody reports it.
%   5. So: hold the model fixed, vary one markdown file, and measure it
%      properly -- placebo arm, CoT arm, paired exact tests, clustered
%      bootstrap, hash-locked pre-registration.
%
% TONE: this is a measurement paper. It does not need to argue that skills are
% good or bad. It needs to argue that the question is currently unanswered and
% that the design here can answer it.

\TODO{Draft after the first skill has a verdict (sequencing step 8).}

\paragraph{Contributions.}
% Each of these stands whether the skills succeed or fail. That is deliberate:
% a contribution contingent on a positive result is a bet, not a contribution.
\begin{enumerate}
  \item A harness for evaluating markdown skill artifacts \emph{with the model
    held fixed}, using the Claude Code CLI itself as the subject under test and
    reproducible on a consumer subscription with no API key. Configuration is
    disclosed against the ETCSOVG checklist \citep{harnessdisclosure2026}.
  \item An adjudication of a live disagreement in the 2026 literature between
    \citet{skillsbench2026} and \citet{skillopt2026}, with the SkillsBench null
    \emph{pre-registered as our prediction}.
  \item Methodological apparatus this literature currently lacks: a
    token- and structure-matched placebo arm, a plain chain-of-thought arm,
    paired exact tests with clustered bootstrap intervals, Benjamini--Hochberg
    control across skills, and hash-locked pre-registration.
  \item A replication attempt on the distractor effect in an agentic setting,
    using a two-auditor-filtered dataset, in light of the 2026 re-audit that
    largely dissolved the original GSM-NoOp magnitude \citep{gsmsymbolic2024}.
\end{enumerate}
```

## `sections/related_work.tex`, as written 2026-08-10

```latex
\section{Related Work}
\label{sec:related}

% SOURCE OF TRUTH: ../docs/RELATED_WORK.md. That file is organised by what each
% finding changed about the design and flags confidence per source. This section
% is a condensation of it, not a second inventory -- keep them consistent, and
% when they diverge the docs file is correct.
%
% Reviewers will know this neighbourhood well. Position explicitly against:
% SkillOpt, SkillsBench, the AGENTS.md impact study, and the two harness papers.

\TODO{Condense from \texttt{docs/RELATED\_WORK.md} once the results fix which
threads are load-bearing.}

\subsection{Skills as an intervention}
% The core tension, stated plainly and early. SkillsBench (86 tasks, 11 domains):
% availability +18.0 to +36.0pp; granularity +0.7pp (GPT-5.5) / -6.7pp
% (DeepSeek), CIs crossing zero. SkillOpt: +23.5pp from bounded edits to the
% same prose, evaluated inside Claude Code and Codex CLI harnesses.
%
% Be fair to SkillOpt. Its method is sound in outline and its harness choice is
% the right one. The criticism is narrow and specific: no CIs, no significance
% tests, and no correction for the many implicit comparisons its
% accept-if-strictly-better ratchet performs. Its own ablation shows a
% target-matched optimiser recovering only 56-74% of the gain, which implies a
% distillation component the paper does not name.

\subsection{Context degradation and irrelevant information}
% GSM-Symbolic, and the 2026 re-audit that kept 117/945 (12.4%) of candidate
% distractors and found the residual effect indistinguishable from zero. Report
% the re-audit's provenance honestly -- it is a re-analysis, not peer-reviewed.
% Then relocate: context rot survives in long-horizon agentic search at 30-50%.

\subsection{Harness variance}
% ~7.8x HV/MV, six ranking reversals in nine comparisons, 23.8-point swing in
% Harness-Bench. This is what makes "hold the model fixed and vary the markdown"
% a coherent experiment rather than a curiosity.

\subsection{Judges and councils}
% PoLL -> RoPoLL (unbounded bias under contamination; geometric median). Nine
% judges, two effective votes (n_eff 2.18). Debate losing to isolated
% self-correction at 2-3x the token cost. Criteria drift.

\subsection{Evaluation methodology}
% Miller's error bars, qualified by the no-CLT result at our N. Biderman et al.
% on reproducible evaluation. Murphy decomposition and smECE. The Husain/Shankar
% bottom-up error-analysis school.
```

## `sections/method.tex`, as written 2026-08-10

```latex
\section{Method}
\label{sec:method}

% SOURCE OF TRUTH: ../docs/PROTOCOL.md (versioned; v1 at time of writing).
% This section is the paper-facing rendering of it. If the protocol is revised
% mid-project, the paper must state which version each run was conducted under.

\subsection{Design}
% Four arms, same items, paired by item:
%   off      task framing + response-format contract
%   on       control + skill body
%   placebo  control + token- and structure-matched contentless filler
%   cot      control + "Think step by step"
% Plus a fifth in-situ arm (--append-system-prompt) for ecological validity.
%
% THREE THINGS TO STATE EXPLICITLY, because their absence is what makes most
% skill evaluations uninterpretable:
%   (a) the response-format contract is in EVERY arm -- otherwise the experiment
%       measures instruction-following, not decision quality;
%   (b) the placebo is matched on tokens and structure, and no SHIP verdict is
%       issued without it;
%   (c) option menus are held constant across arms, because removing them moved
%       trajectory accuracy 14-40pp in AgentAtlas -- larger than any effect we
%       expect to measure.

\subsection{Arenas}
% dev (local/mock) -> screen (cheap hosted) -> confirm (target model, private
% holdout, hash-locked). Only confirm emits a verdict. The separation is
% enforced in code, not by discipline, and the reason is Prompting Inversion:
% scaffolding tuned against a weak model can become a handicap on a strong one.

\subsection{Pre-registration}
% preregistration/<skill>-v<n>.yaml: hypothesis, primary metric, N, MDE, alpha,
% guards, stopping rule, skill_sha256, analysis_script_sha256. A confirmation
% run refuses to start unless the file is committed, is a git ancestor of HEAD,
% predates every result, and both hashes match.
%
% Emphasise the analysis-script lock. A pre-registered metric means nothing if
% the code computing it can be rewritten after seeing the data, and that is the
% gap most "pre-registered" ML work leaves open.
%
% Fixed N, no interim analysis. The screen/confirm split buys cost control
% without alpha spending because the stages use disjoint items.

\subsection{Statistics}
% McNemar exact for paired binary; paired permutation for continuous;
% cluster bootstrap over TEMPLATES for intervals. Not the CLT -- restricted
% below a few hundred effectively independent datapoints, and a design effect of
% 1 + (m-1)rho ~ 2.0 at m=6, rho=0.2 puts us squarely in that range.
%
% Guards are one-sided non-inferiority tests and are deliberately NOT corrected:
% correcting a conservative-direction test would make it easier for a harmful
% skill to pass. State this so it is not mistaken for an oversight.
%
% BH at q=0.10 across the pre-registered primaries. Report raw p and adjusted q.
%
% Calibration: Murphy decomposition with a hard resolution floor, and smECE
% rather than binned ECE.

\subsection{Harness disclosure}
% Full ETCSOVG record in Appendix~\ref{sec:appendix-harness}. Two points belong
% in the body because they are results-relevant rather than administrative:
% arms are interleaved per item so quota drift cannot align with an arm, and
% CLAUDE.md isolation is proven by a canary test rather than assumed.

\TODO{Draft alongside the first confirmation run, not after it.}
```

## `sections/datasets.tex`, as written 2026-08-10

```latex
\section{Datasets}
\label{sec:datasets}

% SOURCE OF TRUTH: ../docs/PROTOCOL.md sec. 6 and the eval-set datasheet.

\subsection{Generation}
% Parameterised YAML templates with COMPUTED ground truth, in the style of
% GSM-Symbolic. The argument for this over authored items is auditability:
% checking ~50 template rules is tractable, checking 300 authored answers is
% not. Publish the template schema in full -- it is more useful to a replicator
% than the items themselves.

\subsection{The distractor audit}
% This is the most important gate in the whole pipeline and should be presented
% as such, because the 2026 re-audit is the single largest threat to the
% flagship's premise.
%
% A distractor qualifies only if (a) the computed solution is provably invariant
% to its removal, and (b) two independent passes agree it is genuinely
% irrelevant rather than plausibly foldable into the reasoning. The re-audit
% kept 12.4% of candidates; report our own attrition rate whatever it is.
% \NUM{\attritionRate}

\subsection{Difficulty gates}
% All three run on the CONTROL arm only, so they cannot bias the
% treatment-minus-control difference. Say that explicitly -- it is the kind of
% detail that separates a fair gate from a thumb on the scale.
%
%   1. Clean-room: >=95% control accuracy on distractor-free variants. An item
%      missed WITHOUT distractors is ambiguous, not hard.
%   2. Difficulty calibration: control accuracy on distractor-present items in
%      [0.35, 0.75]. Above that there is no headroom and required N explodes.
%   3. Realism: forced choice against human-written items, judged blind, scored
%      against 0.5. Replaced the 10% human audit on 2026-08-18 -- see
%      docs/EVAL_SET_DATASHEET.md. Needs a public human-written source that
%      clears the outside-data rule; none is cleared, so this gate is UNRUN.

\subsection{Clustering}
% Items from one template are correlated. Design effect 1 + (m-1)rho, so the
% design favours MANY templates with FEW variants each (50 x 4-6, not 10 x 30).
% Template id is the cluster key in every score record and the resampling unit
% in every interval.

\subsection{Splits and contamination}
% Public/screen items are committed and expected to become contaminated; they
% only gate spending and never enter a verdict. The holdout regenerates from a
% seed kept in an uncommitted local file outside the repository, published after the
% verdict, with fresh seeds next run.
%
% State the principle: contamination is handled by regeneration, not secrecy.
% A benchmark whose validity depends on nobody having seen it has a shelf life;
% one that can be regenerated does not.

\TODO{Report final template counts, attrition, and gate pass rates.}
```

## `sections/results.tex`, as written 2026-08-10

```latex
\section{Results}
\label{sec:results}

% EVERY number and figure in this section is generated. Nothing is transcribed.
% `make figures` writes figures/*.pdf and generated/macros.tex from
% ../results/**/summary.json; if a number appears here that is not a macro from
% that file, it is a bug.
%
% REPORTING RULES, fixed in advance:
%
%   - Report the pre-registered primary first, before anything exploratory.
%   - Report raw p AND BH-adjusted q for every primary.
%   - Report every guard, including the ones that passed. A guard table with
%     only failures is a guard table nobody can check.
%   - Report means WITH p90 and p99. The AGENTS.md study found the benefit of an
%     instruction artifact concentrates in a small number of expensive runs; a
%     mean-only report can hide the effect entirely.
%   - Report nulls in the same table, same format, same prominence as wins.
%   - Report the placebo and CoT arms every time. A skill that beats `off` but
%     not `placebo` is a length effect and must be shown as one.
%   - Where a comparison is underpowered, report the MDE and label it UNTESTED
%     rather than presenting it as a null.

\subsection{Main table}
% One row per skill: verdict, primary metric, effect, 95% CI, p, q, N, model,
% run id. Mirrors ../SCORECARD.md, which is itself generated -- and `de check`
% fails the build if the committed scorecard disagrees with the results.

\TODO{Generated table.}

\subsection{Per-skill detail}
% For each skill: the four-arm comparison, the guard table, the stratified
% breakdown (clean vs distractor-present), and the error taxonomy from the
% bottom-up analysis.

\subsection{Trigger quality}
% Reported SEPARATELY from task accuracy, against a positive set and a negative
% set of ~50 turns that superficially resemble triggers. Precision and recall.
%
% This is not a secondary curiosity. A suite that improves accuracy by 10pp
% while firing on 60% of ordinary turns is a net loss in daily use, and an
% accuracy-only evaluation would not notice.

\subsection{Wiring modes}
% Auto-trigger vs AGENTS.md workflow wiring vs explicit invocation vs hook.
% Given SkillsBench's presence-vs-prose result, this is expected to be the
% larger effect, and it is the one a practitioner can act on.

\subsection{Run-to-run variance}
% >=2 independent runs per cell. Report the variance rather than claiming
% determinism -- sampling parameters are not exposed by the CLI, and temperature
% 0 is not deterministic on hosted inference in any case.
```

## `sections/ablations.tex`, as written 2026-08-10

```latex
\section{Ablations}
\label{sec:ablations}

\subsection{The presence-versus-prose adjudication}
% THE HEADLINE ABLATION. SkillsBench and SkillOpt cannot both be right in the
% general case, and this is the experiment that separates them.
%
% Design: ACE-style incremental playbook curation (preferred over GEPA's
% whole-prompt rewrite, to avoid regression and context collapse) run against
% local Ollama models, where rollouts are free and unlimited. Then measure
% transfer to the target model.
%
% The SkillsBench null is PRE-REGISTERED as our prediction. That pre-registration
% is what makes a null informative here rather than a failure to find something
% -- and it is precisely the discipline an accept-if-strictly-better ratchet
% lacks.
%
% Transfer is simultaneously a direct test of Prompting Inversion on our own
% data: scaffolding tuned against a small local model may become a handicap on a
% frontier one. Either direction is reportable.
%
% Whatever comes out, this is an ablation row and never the load-bearing claim.

\subsection{Forked versus inline context curation}
% Three-way: no curation / inline curation / forked curator returning only a
% ledger. Motivated by arXiv:2604.11462, which found a decoupled curator lifting
% WebArena 36.4 -> 41.2 with 8.8% FEWER tokens.
%
% Report tokens alongside accuracy. A curation win that costs 3x the tokens is a
% different result from one that costs fewer, and only the second is interesting.

\subsection{Isolated versus in-situ injection}
% --system-prompt (full replacement) vs --append-system-prompt (on top of the
% default). The first is the clean measurement; the second is what daily use
% actually looks like.
%
% Disagreement between them is a reportable result, not an inconvenience -- and
% where they disagree, the in-situ number is the one that describes practice.

\subsection{Council versus self-consistency at matched budget}
% The council must beat CoT + self-consistency at MATCHED TOKEN BUDGET, not at
% matched sample count. Anything else is buying accuracy with compute and
% calling it a method.
%
% Report the panel's measured effective sample size. With n_eff ~ 2 for three
% judges, "three perspectives" is a description of the prompt, not of the
% estimator, and saying so is more useful than the headcount.
```

## `sections/discussion.tex`, as written 2026-08-10

```latex
\section{Discussion}
\label{sec:discussion}

% Write this from the results, not from the plan. The outline below is what the
% discussion should ANSWER, not what it should conclude.

\subsection{What the presence-versus-prose result means for skill authors}
% If the SkillsBench null replicates, the practical advice inverts most current
% skill-authoring guidance: effort belongs in the description and the wiring,
% not in the body. If SkillOpt replicates instead, prose optimisation is worth
% automating and the field needs the confidence intervals it currently lacks.
% Both outcomes are actionable; say which one the data supports and how strongly.

\subsection{Where the distractor failure mode actually lives}
% If the flagship's effect is small on distractor-present items but real in
% long-horizon agentic accumulation, that relocates the failure mode rather than
% dissolving it -- and that is a more useful finding than either "it is real" or
% "it was an artifact".

\subsection{Wiring as the dominant term}
% If trigger quality moves results more than skill content does, the field's
% unit of analysis is wrong: we have been evaluating documents when we should be
% evaluating retrieval. Follow this thought honestly even though it partly
% undercuts the premise of writing skills at all.

\subsection{What a verdict is worth}
% A verdict is a claim about one model version at one point in time, under one
% harness, on tasks with computable ground truth. Given HV/MV ~ 7.8x, transfer
% to another harness should not be assumed -- which is the same warning
% arXiv:2605.23950 issues about everyone else's numbers, applied to ours.

\subsection{Negative results}
% Any NULL or HARMFUL verdict gets a written entry here: hypothesis, N, observed
% effect, CI, why we expected otherwise, and what would need to change.
%
% This is not ritual self-criticism. Publishing the nulls is what stops a
% reviewer discounting the wins, and it is the cheapest credibility available to
% a paper in a neighbourhood this crowded.
```

## `sections/limitations.tex`, as written 2026-08-10

```latex
\section{Limitations}
\label{sec:limitations}

% SOURCE OF TRUTH: ../docs/LIMITATIONS.md, written before any results existed so
% it could not be tuned to flatter them. This section condenses it. Nothing may
% be dropped between that file and this section without a note saying why.

\TODO{Condense from \texttt{docs/LIMITATIONS.md}. Do not shorten by deletion.}

% The ones that must appear in the paper regardless of how the results land:
%
%   - No temperature control. The CLI exposes no sampling parameters. Mitigated
%     by >=2 repeats per cell with variance reported, not by claiming
%     determinism.
%   - Small N. Subscription throughput caps items, and a cluster design effect
%     of ~2.0 halves the effective count again. Exact and resampling methods
%     recover validity but not power.
%   - Self-generated datasets. We avoid contamination and thereby own the item
%     biases. Realism rested on a 10% human audit, retired 2026-08-18; the
%     forced-choice replacement cannot run until a human-written source clears
%     the outside-data rule, so nothing measures realism today.
%   - The distractor premise is weakened by the 2026 re-audit, whose source is a
%     re-analysis rather than peer-reviewed work. Flag the confidence.
%   - Judge panels carry ~2 effective votes regardless of headcount, and drift
%     between recalibrations.
%   - Local judge models are weaker; provider diversity is bought at the cost of
%     individual judge quality.
%   - Single harness. The paper's own central citation says this limits transfer.
%   - Tasks with computable ground truth only. This is the same restriction
%     SkillOpt operates under; the difference is that we state it.
```

## `sections/appendix_harness.tex`, as written 2026-08-10

```latex
\section{Harness disclosure}
\label{sec:appendix-harness}

% SOURCE OF TRUTH: ../docs/HARNESS_DISCLOSURE.md. Reproduce the ETCSOVG table in
% full here -- Execution, Tools, Context, Scheduling, Observability,
% Verification, Governance. This is the appendix that makes the paper
% reproducible, and it is the one most papers in this area omit entirely.

\TODO{Render the ETCSOVG table from \texttt{docs/HARNESS\_DISCLOSURE.md}, plus
the per-run \texttt{config.json} schema.}

% Points worth stating in prose rather than leaving to the table:
%
%   - Subscription OAuth, no API key. --bare is unusable because its auth path
%     is strictly ANTHROPIC_API_KEY/apiKeyHelper and OAuth is never read. The
%     isolation is assembled from individual flags instead. This is a
%     reproducibility asset, not a workaround: anyone with a consumer
%     subscription can rerun the harness.
%   - Zero tools, no MCP, no settings sources, no session persistence. The skill
%     is the only intervention, and "the agent looked it up" cannot explain a
%     difference between arms.
%   - CLAUDE.md isolation is proven by a canary test that plants a file with a
%     distinctive instruction in the runner cwd and asserts the model does not
%     follow it. Isolation that is merely configured is isolation that will
%     silently break.
%   - Arms are interleaved per item rather than run in blocks, so quota drift
%     and served-model changes cannot align with an arm.
```

## `sections/appendix_prompts.tex`, as written 2026-08-10

```latex
\section{Prompts, skills, and transcripts}
\label{sec:appendix-prompts}

% \citet{biderman2024lessons} is unambiguous: publish the exact prompt
% formatting, and publish full transcripts rather than scores alone. Cross-paper
% comparison across differing templates is unreliable, and a paper that reports
% only aggregates cannot be checked.

\TODO{Include verbatim: the four arm system prompts, every evaluated SKILL.md
at its pre-registered hash, one worked item per template family, and the
response-format contract.}

% MUST APPEAR HERE:
%
%   - All four arm system prompts, verbatim, including the response-format
%     contract that is common to every arm.
%   - The placebo text, verbatim, with its token count next to the skill's.
%     A placebo the reader cannot inspect is a placebo the reader cannot trust.
%   - Every evaluated SKILL.md at its pre-registered sha256, so a replicator can
%     verify they have the same artifact that produced these numbers.
%   - One fully worked item per template family: variables, rendered prompt,
%     computed ground truth, and the model's response under each arm.
%   - A pointer to the published transcript archive and the holdout seed, both
%     released after the verdict.
```

## `main.tex`, as written 2026-08-10

```latex
% Do Agent Skills Actually Work?
% A Pre-Registered, Placebo-Controlled Evaluation of Markdown Decision Skills
%
% Build:  make paper      (regenerates figures from ../results, then compiles)
% Never edit figures/ by hand -- they are generated artifacts.

\documentclass[11pt]{article}

\usepackage[margin=1in]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{microtype}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{siunitx}
\usepackage{xcolor}
\usepackage[hidelinks]{hyperref}
\usepackage[capitalise,noabbrev]{cleveref}
\usepackage{natbib}

% Drafting aids. \draftmode is switched off before submission; the TODO macro
% then expands to nothing, so a stray note cannot silently ship.
\newif\ifdraftmode
\draftmodetrue

\ifdraftmode
  \newcommand{\TODO}[1]{\textcolor{red}{\textbf{[TODO: #1]}}}
  \newcommand{\NUM}[1]{\textcolor{blue}{\texttt{#1}}}
\else
  \newcommand{\TODO}[1]{}
  \newcommand{\NUM}[1]{#1}
\fi

% Every number that comes from a run is written by `de figures` into
% generated/macros.tex. Nothing in the prose is transcribed by hand -- if a
% number appears in the text and not in that file, it is a bug.
\IfFileExists{generated/macros.tex}{\input{generated/macros}}{}

\title{Do Agent Skills Actually Work?\\
\large A Pre-Registered, Placebo-Controlled Evaluation of\\Markdown Decision Skills}

\author{Angel Campa\\
\texttt{github.com/AngelCampa1/decision-making-skills}}

\date{\today}

\begin{document}
\maketitle

\begin{abstract}
\TODO{Written last. Do not draft an abstract around results that do not exist
yet -- that is how a paper acquires claims its data will not support.}
\end{abstract}

\input{sections/introduction}
\input{sections/related_work}
\input{sections/method}
\input{sections/datasets}
\input{sections/results}
\input{sections/ablations}
\input{sections/discussion}
\input{sections/limitations}

\bibliographystyle{plainnat}
\bibliography{refs}

\appendix
\input{sections/appendix_harness}
\input{sections/appendix_prompts}

\end{document}
```
