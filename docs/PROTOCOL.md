# Protocol

**Audience:** the evaluating reader.

Version 2. This is the standing methodology for every skill evaluated in this
repository. Changes get a new version number and a dated entry in
[`../notebook/`](../notebook/); they never silently amend a protocol a completed
run was conducted under.

**Version 2, 2026-08-28.** Two admission criteria were added to §6 after a
template passed every Version 1 gate while measuring a preference. Nothing else
changed. Every run published before this date was conducted under Version 1,
including the five-arm evolution study of 2026-08-27, and the criteria below do
not reach back to it.

## 1. The experiment

One skill, four arms, the same items in every arm, paired by item.

| Arm | System prompt | Purpose |
| --- | --- | --- |
| `off` | Task framing + response-format contract only | Control |
| `on` | Control + the skill body | Treatment |
| `placebo` | Control + word- and structure-matched filler | Isolates the length effect |
| `cot` | Control + "Think step by step" | Isolates the generic-reasoning effect |

Four arms, and the harness names five. The fifth, `in_situ`, holds the
treatment fixed and changes the venue: the same skill body delivered by
`--append-system-prompt`, which is how an install delivers it. It asks whether
the effect survives a real host prompt, a question about ecological validity, so
it stays out of this table. [`METHODS.md`](METHODS.md) renders all five from
`solvers/arms.py`. Noted 2026-08-21; every rule of Version 1 stands unchanged,
and no completed run was conducted under anything but what is written here.

Three rules make this a fair comparison rather than a demonstration:

The response-format contract appears in every arm. If only the treatment is
told to emit structured output, the experiment measures instruction-following,
not decision quality.

The placebo is matched on word count and structure (same approximate length,
same headings, bullets, and a worked example) but contentless. A skill that beats
`off` and not `placebo` is a length effect, and no `SHIP` verdict goes out
without a passing placebo arm.

Corrected 2026-08-31: this said "matched on tokens", and nothing here has ever
counted tokens. The delivered bodies of the five-arm study measure 655 prompt
tokens for the placebo against 778 for the skill it is matched to, and 910 and
1697 for the two evolved arms, which the placebo was never matched against at
all. The match is on words and structure, the gap in tokens is a stated
confound, and a placebo arm bounds the length effect for the arm it was built
against and no other.

Any option menus are held constant across arms. AgentAtlas
(arXiv:2605.20530**v1**) found that removing explicit label menus moved
trajectory accuracy by 14 to 40 pp across all eight models tested. Two
conditions travel with that figure, and they are why we use it only to justify
holding a variable constant, never as a magnitude to compare our own effects
against. First, it is v1-only: v2 (26 May 2026) removed the sentence and
replaced the quantity with "mapped label agreement can change substantially",
so the version must be named. Second, both versions call the study a
measurement-protocol demonstration on a synthetic 1,342-item set, and v2 says
explicitly it "should not be read as a 'definitive model comparison'". An
earlier draft of this paragraph called the effect "larger than any effect we
expect to measure". That is a cross-study magnitude comparison, which is the
reading v2's own abstract disclaims, so it is dropped.

A fifth `in-situ` arm, injecting the skill via `--append-system-prompt` on top of
the default system prompt rather than replacing it, tests ecological validity.
Disagreement between the isolated and in-situ arms is a reportable result.

## 2. Arenas

Three arenas with different permissions. Code enforces the separation, not
discipline.

| Arena | Models | Split | Skill may change | Emits a verdict |
| --- | --- | --- | --- | --- |
| `dev` | Local (Ollama, mock) | public | yes | no |
| `screen` | Cheap hosted (Haiku), agy, NVIDIA Build free tier | public | yes | no |
| `confirm` | Target (Sonnet, Opus) | private holdout | no | yes |

Prompting Inversion (arXiv:2510.22251) showed a sculpted prompt helping GPT-4o
(97% vs 93%) while *hurting* GPT-5 (94.00% vs 96.36% plain CoT). That is why the
separation matters: scaffolding tuned against a weak model can become a handicap
on a strong one. Iterating freely in `dev` and `screen` is therefore fine and
expected; carrying that iteration into the verdict is not.

**`dev` got a backend on 2026-08-19, having had none since this table was
written.** `evals/src/decision_evals/providers/openai_compatible.py` speaks the
wire format Ollama, vLLM, LM Studio and `llama.cpp` all serve, and
`runner.local_call` is the substitution `CallFn` was designed for, so a local
run needs no second run loop. **Measured since 2026-08-27**: the five-arm
evolution study ran 4,368 calls on `ollama/qwen3:1.7b` through this backend,
emitting no verdict as `dev` requires ([`STATUS.md`](STATUS.md)).

Two things it changes and one it does not. It costs nothing and consumes no
quota, which is what makes the standing rules affordable. Running a falsifier
against a known-good case first, and checking that some possible response would
have scored above zero, are cheap here and are not cheap on a subscription. And
it is the first backend that is not one Claude CLI, which the claim ladder's
sentence about *frontier models*, plural, will eventually need. What it does not
change is what may be claimed: `dev` emits no verdict, `arenas.py` enforces that
on the `ollama` model prefix, and a local number stays a local number.

**Isolation is checked here, not assumed.** The reasoning that nearly shipped
was that an HTTP server reads nothing off the client's disk, so there is no
`CLAUDE.md` to plant and isolation is structural. The first half is true and the
conclusion is false: an Ollama model is a Modelfile, and a Modelfile may carry
its own `SYSTEM` prompt, which is a planted instruction one layer down:
invisible in the request, present in every generation. `assert_isolated` reads
the model card and refuses one. Where a server offers no card, `Endpoint` makes
the caller record that no receipt was obtainable, because that is a different
statement from a receipt that passed.

**A free hosted tier joined `screen` on 2026-08-26.** NVIDIA Build speaks the
same wire format, so it is a row in `MODELS` and a constructor beside `ollama()`
rather than a backend. It sits in `screen` for a narrower reason than `agy`
does: nothing wraps the call, and the request is the whole context, but the
server publishes no card, so `has_receipt` is false and every run there records
an absence. A venue whose isolation cannot be checked is a venue whose results
are a screen. The permission to hold a key at all is
[`AGENTS.md`](../AGENTS.md)'s "Cost" section, amended the same day, and it
extends to a free tier only.

## 3. Pre-registration

Two mechanisms, and only one of them has ever run. This section said otherwise
until 2026-08-13, describing the unbuilt one in the present tense while every
call on record went through neither. The correction is in
[`notebook/2026-08-13-the-gate-that-was-documented-and-never-ran.md`](../notebook/2026-08-13-the-gate-that-was-documented-and-never-ran.md).

### 3a. For `dev` and `screen` runs: the standing mechanism

The mechanism is a dated notebook prediction, committed before the run. Every
run in `results/` is registered by one, and `de check`'s run provenance step
enforces it: it refuses a published run whose README carries no
`Prediction:` line, and refuses one whose prediction was not committed at or
before the commit the run was made at. The commit graph is the whole check. A
prediction that cannot be shown to predate its data is not evidence, it is a
story with a date on it.

The same step requires a run to declare the answer-key version its numbers were
computed under, and refuses a README whose declared version disagrees with the
records beside it.

Two runs are baselined out of this rule by name, with their reasons written
down: `results/decision-making/2026-08-12-40b6ba5/`, the 365-call run published
with no prediction, and `results/evidence-ledger/2026-08-10-baseline-corpus/`,
which predates the convention. This read *one* until 2026-08-19, while the file
it points at named two. See
[`results/provenance-baseline.txt`](../results/provenance-baseline.txt).

### 3b. For `confirm` runs: the locks, and what they now stop

A confirmation run commits `preregistration/<skill>-v<n>.yaml` before it starts,
carrying hypothesis, primary metric, item count, minimum detectable effect,
alpha, guards, stopping rule, plus `skill_sha256` and `analysis_script_sha256`.
The first one is on disk:
[`preregistration/decision-making-v1.yaml`](../preregistration/decision-making-v1.yaml),
with every number in it derived in a comment above the fields.

`de confirm` refuses to start unless:

1. the pre-registration file is committed and not dirty;
2. its commit is an ancestor of `HEAD` and predates every confirmation run in
   `results/<skill>/`;
3. `skill_sha256` matches the skill body on disk;
4. `analysis_script_sha256` matches the analysis code;
5. the supplied baseline accuracy falls inside the difficulty band;
6. the projected cost is within budget.

**Five of the six bite today, and the run still stops.** `decision_evals.prereg`
implements the refusals and `de confirm` is the caller that reaches them, which
is what changed on 2026-08-24. The module carried a 100% line-and-branch
coverage floor with nothing importing it, and this section described the
refusals in the present indicative while every one of them was inert. The
`[tool.decision-evals.unwired]` declaration that held that gap open is gone, and
`de check`'s integrity wiring step refuses the module the moment it stops being
reachable again.

What stops the run is the split. The `confirm` arena reads the private holdout,
`datasets/holdout/` is regenerated from a passphrase-derived seed and stays out
of the tree until a verdict publishes, and no confirmation runner reads it yet.
`de confirm` checks the locks, says which piece is missing, and exits without
making a call. Every number on record remains a `screen`-tier trigger
measurement.

**Point 2 is the sixth, and it is the one that does not bite yet.** It is scoped
to confirmation runs rather than to every run in `results/<skill>/`, because
screening precedes a pre-registration by design: screening runs the public
split, its items are disjoint from the holdout's, and its result never enters
the final p-value. Counting a screening run as a postdiction would refuse every
skill this repository has ever measured, and a gate no known-good case can pass
is a gate somebody turns off. `cli.confirmation_runs` reads the
`**Pre-registration:**` line a confirmation run's README carries, which is the
only thing in a run directory that separates the two.

**Nothing writes that line and no gate requires it, so today the check passes
over an empty set.** `de confirm` prints the count it checked against for that
reason. Two things would close it: the confirmation runner writing the line, and
a run-provenance rule refusing a run in the `confirm` arena that carries no
pre-registration. Both belong with the runner. Until then point 2 **will
refuse** a postdiction, and has never had one to refuse.

Editing one word of a skill after pre-registration aborts the run and names the
next version. Proceeding requires writing `-v2.yaml`, which is a new, dated,
visible commit, so prompt tuning becomes an auditable event. Locking the
analysis script matters just as much: a pre-registered metric means nothing if
the code computing it can be rewritten after seeing the data.

The stopping rule is fixed N with no interim analysis. The screen/confirm split
gives cost control without alpha spending, because the two stages use disjoint
items and the screening result never enters the final p-value. It only decides
whether to spend.

## 4. Metrics

One primary metric per skill. Guards that can only veto. Secondaries that are
descriptive and explicitly labelled exploratory.

The primary tests are McNemar's exact test for paired binary outcomes and a
paired permutation test for continuous ones. Confidence intervals come from a
cluster bootstrap resampling *templates*, not items. We avoid the CLT on
purpose: arXiv:2503.01747 restricts its validity below a few hundred effectively
independent datapoints, and after a design effect of ~2.0 our counts sit in
exactly that range.

Guards are all one-sided non-inferiority tests:

| Guard | Threshold |
| --- | --- |
| No harm on the clean stratum | Δ ≥ −2pp |
| Beats placebo | CI on (on − placebo) excludes 0 |
| Beats plain CoT | CI lower bound on (on − cot) > −2pp |
| Format integrity | Parse-failure rate increase ≤ 1pp |
| Cost | Median output tokens ≤ 2.5× control |

We report means alongside p90 and p99. The AGENTS.md impact study
(arXiv:2601.20404) found the benefit of an instruction artifact concentrates in a
small number of expensive runs rather than spreading uniformly, so a mean-only
report can hide the effect entirely.

Calibration uses the Murphy decomposition with a hard floor on resolution
(Δ ≥ −0.005). A skill that improves Brier purely by shrinking every forecast
toward the base rate is hedging, and the resolution term is what catches it.
Calibration error is reported with a kernel-smoothed estimator rather than
binned ECE, which is bin-count dependent and biased at small n.

Trigger quality is measured separately from task accuracy, against a positive
set and a negative set of ~50 turns that superficially resemble triggers.
Precision and recall are both reported. A suite that improves accuracy while
firing on most ordinary turns is a net loss in practice, and an accuracy-only
evaluation would not notice.

## 5. Multiplicity

Benjamini-Hochberg at q = 0.10 across the primary tests of the pre-registered
skill set. Both raw p and adjusted q appear in the scorecard.

Guards are not corrected. They are conservative-direction non-inferiority tests,
so adjusting them would make it *easier* for a harmful skill to pass: the
correction would work against safety rather than for it.

## 6. Datasets

Parameterised YAML templates with computed ground truth, in the style of
GSM-Symbolic. Auditing ~50 template rules is tractable; auditing 300 authored
answers is not.

Five gates before a family is eligible for pre-registration, all run on the
control arm only so they cannot bias the treatment-minus-control difference.
This said three until 2026-08-31; criteria 4 and 5 were added earlier and the
lead-in was not:

1. Distractor audit. A distractor qualifies only if the computed solution is
   provably invariant to its removal *and* two independent passes agree it is
   genuinely irrelevant rather than plausibly foldable into the reasoning. The
   2026 GSM-Symbolic re-audit kept 12.4% of candidates; expect similar attrition.
2. Clean-room check. ≥95% control accuracy on distractor-free variants. Items
   missed *without* distractors are ambiguous, not hard.
3. Difficulty calibration. Control accuracy on distractor-present items in
   [0.35, 0.75]. Above that there is no headroom and the required N explodes.
4. Response bias. Skew near zero on the control arm, where skew is the rate the
   model answers an option minus the rate the items called for it.
5. Discrimination. Informedness below one on the control arm, so there is
   something left for an arm to gain.

**Criteria 4 and 5 are new in Version 2, and criterion 3 is why.** A model
answering one option nine times in ten scores about 0.63 on a two-option key
whose base rate is near two thirds, which lands inside [0.35, 0.75] and reads as
difficulty. `hrd-002-shipping-escalation` did exactly that: 0.583 and 0.625 on
a 30B across two 24-item passes, reached with sensitivity 1.000 against
specificity of 0.167 and 0.250. Corrected 2026-08-31: this quoted 0.722, an
18-item reading from a different pass, beside the sensitivity and specificity of
the 24-item ones. On a balanced key those cap accuracy at (0.250 + 1) / 2 =
0.625, so 0.722 was not reachable from the figures printed next to it.
Criterion 3 cannot tell that apart from a template the model is genuinely
finding hard.

Corrected 2026-08-31. This paragraph said the key was balanced and that an arm
nudging the model toward the other option would have gained about thirty points.
On a balanced key accuracy is `(J+1)/2`, so a pure bias shift gains nothing at
all and the 0.63 needs the unbalanced base rate now stated. The audit that found
it is in
[`../notebook/2026-08-31-the-paper-described-a-search-we-did-not-run-and-a-test-that-could-not-fail.md`](../notebook/2026-08-31-the-paper-described-a-search-we-did-not-run-and-a-test-that-could-not-fail.md).

Neither criterion closes the case on its own. `rel-009-flight-rebook` passes all
three on the control arm — accuracy 0.4911, skew +0.019, informedness +0.028 —
and is one of the three templates the five-arm study found measures nothing. A
coin has zero skew and zero informedness too. Criterion 5 bounds discrimination
above and not below, and a lower bound is the obvious repair; nothing has been
run against one, so it is not written here as a rule.

Both are computed by `stats/signal.py` over the control arm's own records, so
they cost no calls beyond the calibration run criterion 3 already needs. No gate
in `de check` reads them today; a corpus admission gate that enforced them
**will refuse** a template failing either, and until one exists the criteria are
applied by hand and the reading is recorded with the corpus.

Templates rather than items are the clustering unit, so the design favours many
templates with few variants each.

Public/screen items are committed and expected to become contaminated over time;
they only gate spending. The holdout regenerates from a seed kept in an
uncommitted local file outside the repository, and is published after the
verdict, with a fresh seed for the next run. A file rather than a passphrase: a
secret only a person can supply makes regeneration wait on one. The exposure
this adds is real. A file on the machine is readable by any agent with
filesystem access, and a passphrase in someone's head is not. We accept it
because the seed has to reach the generator through an agent either way, and
because secrecy was never the contamination mechanism here; regeneration
between runs is.

## 7. Verifiers and judges

We test verifiers before trusting them: fixtures of known-correct, known-wrong,
paraphrased, and boundary responses, run through the verifier first. Every zero
score is classified rather than assumed to be the model's fault. The code admits
seven causes, not the four this section listed until 2026-08-19: `agent_wrong`,
`format_violation`, `output_truncated`, `infrastructure`, `item_defect`,
`verifier_defect` and `environment_leak`. Separating a bad item from a bad
checker is the deliberate one: they have completely different fixes, and the
omission here had the spec disagreeing with `scorers/answer.py` for as long as
both existed. `output_truncated` is the seventh, added 2026-09-03, and it holds
the reply the output cap stopped before it reached an answer line. The record
carries the backend's own stop reason and the reasoning text the cap was spent
on, so which of the two a zero is stays readable after the run.

Judges produce secondary metrics only; no primary metric is ever a judge score.
They emit a binary verdict plus a written critique rather than a Likert rating,
and they are calibrated against a deliberately failure-heavy set whose labels
come from three-instance blind adjudication (the N3 protocol, with movement
reported against its kill threshold) rather than from a person. TPR and TNR are
reported separately, because blended accuracy hides agreeableness bias: a judge
that agrees with everything scores well on a balanced set while catching almost
no real failures.

That calibration key is model-labelled, and that weakening is real. This
paragraph said *human-labelled* until 2026-08-18, when every
step waiting on a person came out of these plans; what it named had never been
produced, so the change is from an unavailable key to an available one and not
from a better key to a worse one. It does mean a judge is calibrated against
labels a model set, so a bias the adjudicator shares with the judge is invisible
to this check. Three independent instances and a reported movement figure bound
that; they do not remove it. A public human-labelled set that clears the
outside-data rule would, and none has been cleared. Criteria drift
(arXiv:2404.12272) means recalibration is required whenever the pipeline or the
model changes: "users need criteria to grade outputs, but grading outputs helps
users define criteria."

Panels are small and heterogeneous. "Nine Judges, Two Effective Votes"
(arXiv:2605.29800) found nine frontier judges from seven families provide "only
about 2 independent votes' worth of information", and that the best single judge
matches or outperforms the full panel across all conditions, so headcount is not
the lever, and diversity of failure mode is the only thing that could be.
Aggregation uses a robust estimator rather than a mean, per RoPoLL
(arXiv:2606.30931), which shows mean aggregation carries unbounded bias under any
positive contamination.

## 8. Verdicts

See [`../SCORECARD.md`](../SCORECARD.md) for the vocabulary. Two commitments:

Negative results are published. A `NULL` or `HARMFUL` verdict gets a written
entry: hypothesis, N, observed effect, CI, why we expected otherwise, and what
would need to change. The badge reports honest denominators.

A verdict is a claim about one model version at one point in time. Skills
validated in one month can decay in the next. A periodic drift watch on shipped
skills is part of the protocol.

## 9. Harness disclosure

Every run records its harness configuration against the ETCSOVG checklist
(Execution, Tool, Context, Scheduling, Observability, Verification,
Governance). The harness "is often a stronger determinant of agent performance
than the model it wraps", and current protocols therefore "systematically
misattribute harness-level gains to model improvements" (arXiv:2605.23950). An agent result without its harness disclosed
is not reproducible, and most published ones are not.

In that paper's own 3×3 experiment (three frontier models × three harness
configurations, on "a difficulty-stratified 100-task subset of SWE-bench
Verified", two runs per cell) the aggregate harness-to-model variance ratio was
7.80×, with ranking reversals in "6 out of 9 model-pair/harness-pair
comparisons" (§4.2, Table 2). One design on one task distribution, so the
direction transfers and the ratio does not.

> **Correction, 2026-08-13.** This paragraph read "in a controlled 3×3
> factorial, harness variance exceeded model variance by roughly 7.8× and
> produced six ranking reversals in nine comparisons". None of those figures
> is in that paper's abstract, which is a position paper's and contains no
> numerals at all. They may be in its body; they are *unverified*, and they are
> out of this file until somebody opens it. The qualitative direction quoted
> above is verbatim and the disclosure requirement is unaffected. The ETCSOVG
> expansion is likewise not in the abstract, which says only "a disclosure
> standard and a variance decomposition protocol". The seven names are this
> repository's, and we use them as our own checklist rather than as the
> paper's.

> **Correction to the correction, 2026-08-13, later the same day.** Somebody
> opened it. The full text is at `arxiv.org/html/2605.23950v1` and both figures
> are there verbatim, in §4.2 and Table 2, as output of an experiment the
> authors ran; two agents fetched it independently. The figures are restored
> above with the section named, and the caveat that was missing all along (one
> 3×3 design, one task distribution) is stated with them. The defect was citing
> a body figure as though it came from the abstract, not inventing one. The
> note about ETCSOVG stands unchanged: those seven names are still ours.
