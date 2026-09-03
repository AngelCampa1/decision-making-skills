# What we found

**Audience:** the evaluating reader, someone who builds or evaluates LLM
harnesses and has five minutes now and thirty later.

**What this is.** The findings of this repository in the order they matter,
each with the record it comes from. The first section is the five-minute
version. The rest is the same story with the arithmetic, and every number in it
links to the run README, notebook entry or source file it was read from. The
skill under test is [`decision-making`](../skills/decision-making/SKILL.md),
six procedures behind one router, and the record behind the findings is twenty
published runs with their raw transcripts, indexed in
[`RUN_INDEX.md`](RUN_INDEX.md).

## The five-minute version

The harness was built to measure whether a decision procedure, loaded into an
agent as a skill, improves the decisions it makes. It found instead that the
thing it was pointed at could not fail. Every single-prompt decision scenario
authored here with an answer key was solved unaided: the scalar family at
Youden's J = 1.000 over 99 blind readings, `hinge` at +0.850 machine-scored and
+0.950 hand-adjudicated over 40, and `cascade` at +1.000, +1.000 and +0.850
over 40 each. The one construct without a key, `council`, returned a real null
with nothing for a procedure to fix
([`STATUS.md`](STATUS.md), the venue table). Seven hosted models in the
committed screen file solved the reliability corpus with an empty prompt at
0.933 to 1.000
([the run README](../results/evolution-study/2026-08-27-53b4965-five-arm/README.md)).
Four registered predictions bet against the ceiling, and every one lost.

Along the way the harness caught its own instrument, its own venue and its own
gate being wrong, in that order. The first trigger corpus was
<!-- de:fact corpus-solvability -->89%<!-- /de:fact --> solvable by
counting words. One relabelled item raised recall 3 to 5 points on four of the
five arms on disk without a call being re-made. Twenty-one of twenty-one scored
failures across three corpora were the answer key. Eighty-seven answers in the
one real controlled study were refused for carrying the model's thinking-mode
switch, and 84 of them named the key. A batching local server returned
different text for byte-identical prompts at temperature 0 whenever requests
ran concurrently. A module at 100% coverage with no caller shipped twice, and a
tested function nothing invoked made it three.

The one controlled study that ran to completion, five arms over 728 items on a
1.7B model, returned a registered null: two skill-evolution engines produced
winners that had written the answer key into their own bodies, and neither beat
a word-count-matched placebo after Holm. The unseen half of that design had
three template clusters, which floors a one-sided sign test at 0.125, so those
primaries could never have rejected. The bodies of both winners are lost.

The one finding that repeats across every corpus version is small and about
firing, which is upstream of helping: the opener sentence of the skill's
description costs false positives in every run that varied it, and its recall
contribution has never separated from zero in a paired test.

What the harness now refuses, as a result of each of those, is the part of this
repository that transfers. A confirmation run cannot start unless its
pre-registration is committed, is an ancestor of `HEAD`, predates every result
for that skill, and matches the skill body and the analysis script by hash
([`prereg.py`](../evals/src/decision_evals/prereg.py)); a published run cannot
land unless its prediction's first commit is an ancestor of the run's; and an
answer key cannot sit on disk with an item no blind three-judge panel has read.

---

## 1. There was nothing to measure

Every venue built for the decision-quality question closed on a ceiling, and
the closures came from reading the control arm before authoring the corpus.

**Family A, the scalar triplet behind `ledger`, `timing` and `fit`.** The
`ledger` yield probe closed on both of its registered kills over 90 blind
readings, and a nine-call screen of a repaired item, built under both repairs
the reviewers had named, came back unanimous and equal to key in every arm.
Across the two: 18 arms, 99 blind readings, unaided J = 1.000 against a
registered kill of 0.70. The registration said that if the repairs could only be
met by making the matched fact subtle, they had collapsed into `fit`'s
mechanism. They had not, and the item still could not fail.
[`2026-08-25-family-a-closes-and-the-dial-was-never-the-thing.md`](../notebook/2026-08-25-family-a-closes-and-the-dial-was-never-the-thing.md);
[the run](../results/track-h/2026-08-25-28311e2-ledger-v2-screen/README.md).

**`hinge`, a different family and a different answer shape.** Set membership
instead of a number: name the one unsettled detail that would put you on the
other course. 40 unaided blind readings, crossed primary +0.850, 95% bootstrap
[+0.725, +0.975], and +0.950 [+0.850, +1.000] from a blind adjudicator shown
the 40 blocks with arms stripped. The kill at 0.70 fires on both figures. Two
registered validity checks failed in the same run, so the item says nothing
about decoy resistance.
[`2026-08-25-the-hinge-screen-ceilings-and-two-validity-checks-fail.md`](../notebook/2026-08-25-the-hinge-screen-ceilings-and-two-validity-checks-fail.md);
[the run](../results/track-h/2026-08-25-c9f649a-hinge-control-screen/README.md).

**`cascade`, three items.** J = +1.000, +1.000 and +0.850 over 40 blind
readings each, against the same kill. C01's +1.000 rests on one author-written
guard list: without it the machine figure is +0.650, while the blind judges
ratify all seven affected readings and the adjudicated figure stays at +1.000.
[The run](../results/track-h/2026-08-25-4417803-cascade-control-screen/README.md).

**`council`, the construct with no answer key.** Two orderings scored against
each other, so there is no label to be easy. Second-position rate 0.4722 on 144
committed records from 176 draws, exact p 0.5598, 95% CI [0.3885, 0.5571]
against a null of 0.5. Eight
of nine admitted items named the same course sixteen times out of sixteen under
both orderings: order-blind with a hard content preference. The skill arm was
never issued, by a rule set before the number existed.
[The run](../results/track-h/2026-08-25-a6d654b-council-order-effect/README.md).

Those four came after earlier venues had already closed the same way: the first
single-turn relevance corpus at 0.946, with 15 of 15 zeros traced to the answer
key, and its rebuild with colliding distractors at 0.971
([`STATUS.md`](STATUS.md), venues table).

**The reliability corpus on hosted models.** The five-arm study's corpus was
calibrated for `ollama/qwen3:1.7b`, where an empty prompt scores 0.702 over 728
items. A screen of NVIDIA Build models with no skill at all found every one
measured solving it: seven rows in the committed
`nvbuild-ceiling-screen.json`, from 0.933 to 1.000. The notebook entry
records an eighth model that returned inside budget and is not in the file, and
the run README reports the file's count on the rule that a record edited to
match a write-up is not a record. Three larger models never returned and are
expected to ceiling, which is stated as an expectation.
[`2026-08-27-the-verdict-tier-is-reachable-and-the-corpus-is-not-hard-enough-for-it.md`](../notebook/2026-08-27-the-verdict-tier-is-reachable-and-the-corpus-is-not-hard-enough-for-it.md).

**Nine harder templates.** Authored to open room for a screen-tier run. The
first, built on the hypothesis that a rule stated as a fact rather than a
conditional is what makes an item hard, scored 24 of 24 on a 30B
(`nvidia/nemotron-3-nano-30b-a3b`, through NVIDIA Build). The second
hypothesis, two policies and a precedence rule, produced `hrd-002` at 0.583
and 0.625 across two 24-item passes on the same model, and the six selection
templates built on it landed at 111 of 117 = 0.949 as a set against a
registered band of 0.60 to 0.75. `hrd-002` holds a 30B off the ceiling by
answering one-sidedly, sensitivity 1.000 against specificity of 0.167 and
0.250, which on a balanced key caps accuracy at 0.625. Every template authored either sits at
the ceiling or has room and no signal.
[`2026-08-28-policy-selection-is-the-lever-and-it-costs-the-small-model.md`](../notebook/2026-08-28-policy-selection-is-the-lever-and-it-costs-the-small-model.md);
[`STATUS.md`](STATUS.md), "The harder corpus is blocked".

**The bets that lost.** Each of these was registered before the run, and each
predicted headroom.

| registered | observed | entry |
| --- | --- | --- |
| Family A v2: the unaided arm will not be unanimous | unanimous, 9 of 9 | [`2026-08-25-prediction-can-a-ledger-item-be-repaired-off-the-ceiling.md`](../notebook/2026-08-25-prediction-can-a-ledger-item-be-repaired-off-the-ceiling.md) |
| `cascade`: unaided J 0.45, below the kill | +1.000 | [`2026-08-25-prediction-will-families-b-and-c-ceiling-too.md`](../notebook/2026-08-25-prediction-will-families-b-and-c-ceiling-too.md) |
| `council`: true second-position rate 0.60 | 0.4722, and every departure was primacy | same entry |
| six selection templates land a 30B between 0.60 and 0.75 | 0.949 | [`2026-08-28-policy-selection-is-the-lever-and-it-costs-the-small-model.md`](../notebook/2026-08-28-policy-selection-is-the-lever-and-it-costs-the-small-model.md) |

The generalisation the record supports is narrow: a scenario compact enough to
fit one prompt and answerable in one call is not, for a current model, hard.
Nothing measured here tests volume, long context, delegation or work carried
across a conversation, and the failures the six procedures describe mostly live
there.

## 2. What the harness found wrong with its own answer key

Four defects in the answer key, each found by the harness about itself, and
each the reason a refusal now exists.

**A ruler scored 89%.** The first trigger corpus had positives at a median of
18 words and negatives at 8. The rule "fire if the turn is 18 words or longer"
scores 0.890 on the version 2 key, against 0.9795 and 0.9863 for the best arms
measured on that key, so every result on that corpus was competing for about
<!-- de:fact headroom-points -->nine points<!-- /de:fact --> over a ruler.
The figure was first published as six points against 0.956, which set the
version 2 ruler beside a version 1 arm that was not the best at either
version; the correction is appended in
[`STATUS.md`](STATUS.md), "a second reading of that through-line". The
rebuilt corpus holds the best model-free shortcut, a stump over eight trivial
features, at <!-- de:fact word-trick-ceiling -->0.7054<!-- /de:fact --> against
a majority baseline of 0.6667.
[`2026-08-13-the-corpus-is-89-percent-solved-by-counting-words.md`](../notebook/2026-08-13-the-corpus-is-89-percent-solved-by-counting-words.md);
[`SCORECARD.md`](../SCORECARD.md) carries both figures.

**One label moved and four arms improved.** On 2026-08-13 one turn moved from
the positives to the negatives, on a maintainer decision that was correct.
Re-scored against the new labels with no call re-made, the shipped skill's
recall went from 0.878 to 0.929, three other arms rose 3 to 5 points, and
`opener-only` fell by 0.003. The checkpoint was valid, the parse rate was
100%, and nothing in a record
distinguishes a label correction from a model result. Every record now carries
`set_version`, and `label_versions_comparable` in
[`trigger_arms.py`](../evals/src/decision_evals/trigger_arms.py) refuses a
comparison across two of them.
[`2026-08-13-one-label-moved-and-every-arm-improved.md`](../notebook/2026-08-13-one-label-moved-and-every-arm-improved.md).

**Twenty-one of twenty-one scored failures were the key.** On the first control
run, 15 of 15 zeros over 280 traces were item defects, each auto-labelled
`agent_wrong` and each, on reading, a case where the model's answer was
defensible and the ground truth was not. The count across three corpora reached
21 of 21, which is why `de check` now refuses an answer key carrying an item
with no three-judge blind record.
[`FAILURE_TAXONOMY.md`](FAILURE_TAXONOMY.md);
[`WHY_THESE_RULES.md`](WHY_THESE_RULES.md#why-an-unadjudicated-answer-key-is-refused).

**The scorer refused a control token, and the paper read the refusals as
findings.** `ollama/qwen3:1.7b` reads `/think` as a switch for its thinking
mode and wrote it back after its answer: `ANSWER: monitor /think`. The scorer
matched the text after `ANSWER:` against the option list and refused each as
an option not on the menu. Over the five-arm study, 87 of 3,640 readings
carried the token: 56 on GEPA's winner, 29 on the empty prompt, one each on
`on` and `skillopt`, none on `placebo`. Eighty-four of the 87 named the key.
The two non-null readings the first write-up carried, the placebo above an
empty prompt on the seen set and GEPA's winner below one on the unseen set,
were both made of those refusals. The check that found it printed the answer
line of every refused row, took a minute, and is now the seventh item on the
paper's list of checks.
[`2026-09-01-the-scorer-refused-a-control-token-and-the-paper-read-the-refusals-as-findings.md`](../notebook/2026-09-01-the-scorer-refused-a-control-token-and-the-paper-read-the-refusals-as-findings.md);
[the run README](../results/evolution-study/2026-08-27-53b4965-five-arm/README.md),
corrections of 2026-09-01.

## 3. Two inputs the venue was varying

Two inputs the venue was quietly varying, both found by a registered falsifier.

**Concurrency changes every answer on a batching server.** 40 items on
`ollama/qwen3:4b` at temperature 0, byte-identical prompts, three arms. Within
one process invocation a serial repeat agreed with serial on the exact text of
31 of 40, then 13 of 40 on replication; the concurrent pass at eight workers
agreed on 0 of 40 both times. The replication also found that two serial runs
an hour apart agree on 0 of 40, and the register in `runner.py` records the two
cross-invocation serial pairs available at 0 of 40 and 7 of 40, so serial is
not a way to make the backend reproducible either, and no two runs on it may be
compared by text. On
the parsed answer, the quantity that reaches a published number, the two
concurrent passes agree with serial on 0.850 and 0.825 of items against 0.875
between two serial invocations, which at n = 40 separates nothing. The refusal in
[`runner.py`](../evals/src/decision_evals/runner.py) is therefore a register of
venue prefixes, `CONCURRENCY_UNSAFE`, and it shrinks by measurement.
[`2026-08-19-concurrency-changes-every-answer-on-a-batching-server.md`](../notebook/2026-08-19-concurrency-changes-every-answer-on-a-batching-server.md);
[`2026-08-19-the-replication-moved-the-floor-and-found-a-worse-problem.md`](../notebook/2026-08-19-the-replication-moved-the-floor-and-found-a-worse-problem.md).

**Model residency is now pinned on every request, because it was an input
nobody recorded.** The same skill body scored 15 to 19 of 21 across a day and
was called noise. Twelve passes alternating warm and freshly loaded found 19 of
21 items bit-identical across the eleven passes after the first, and two items
in perfect antiphase for all eleven: one correct only while resident, the other
correct only just after a load. Ollama evicts after five minutes by default,
and inside a search every validation pass is followed by a reflector call that
takes longer than that, so a search sampled both states in an order nothing
chose. `keep_alive: 60m` now goes out with each call
([`providers/openai_compatible.py`](../evals/src/decision_evals/providers/openai_compatible.py)),
and the five-arm study's A/A pass, the check that entry planned for the pin,
came back 728 of 728 identical on one arm run in a block. The value is still
not written into `run.json`; the run README says so.
[`2026-08-27-the-venue-is-deterministic-and-one-of-its-inputs-was-not-in-the-record.md`](../notebook/2026-08-27-the-venue-is-deterministic-and-one-of-its-inputs-was-not-in-the-record.md).

## 4. A coverage floor is not a wiring check

A coverage floor says a module's failure would corrupt a number. It does not
say the module runs. The harness found the two conflated three times and now
refuses the two shapes it can see.
`decision_evals.triggers` was tested to 100% and called by nothing while a
trigger set described a skill that no longer existed. `prereg.py` carried every
refusal `PROTOCOL.md` promised, under a 100% line-and-branch floor, and no
caller reached it while four pre-registration slips happened in one day.
`benjamini_hochberg` was implemented, exported, property-tested, and never
invoked, and that third one the wiring gate cannot see, because the module is
import-reachable and the function is not call-reachable.
[`wiring.py`](../evals/src/decision_evals/wiring.py) refuses a floored module no
entry point imports;
[`2026-08-13-the-gate-that-was-documented-and-never-ran.md`](../notebook/2026-08-13-the-gate-that-was-documented-and-never-ran.md);
[`2026-08-14-the-checklist-ticked-a-function-nothing-calls.md`](../notebook/2026-08-14-the-checklist-ticked-a-function-nothing-calls.md);
[`WHY_THESE_RULES.md`](WHY_THESE_RULES.md#why-a-coverage-floor-is-not-a-wiring-check).

## 5. The one real study, and its arithmetic

The five-arm study of 2026-08-27 is the only run here that asks whether a
skill helps. Every other run asks whether it fires. It ran with a placebo.
[The run](../results/evolution-study/2026-08-27-53b4965-five-arm/README.md).

**Design.** 4,368 calls on `ollama/qwen3:1.7b`, temperature 0, 16,384-token
window, `keep_alive: 60m`. Five arms over the same 728 items: no document,
the shipped skill, a placebo matched to it on word count within 15% and on
structure, and the winners of two automated skill-evolution engines, GEPA and
SkillOpt, each run on a matched budget over seven training templates. Two item
sets, never pooled: 336 items from three held-out templates, 392 from the seven
trained ones at holdout seeds. Each comparison is McNemar's exact test against
the placebo, one-sided, Holm over the registered family of three.

**Result.** No arm rejects on either set. The best showing is SkillOpt's
winner at +0.041 on the seen set, raw p = 0.034, Holm 0.102. GEPA's winner
scored 0.6280 on the unseen set against 0.6845 for no document, the widest
shortfall against an empty prompt in the study. The shipped skill is below an
empty prompt on that set too, 0.6786 against 0.6845. The A/A control returned 728 of 728 items
identical between two scorings of the placebo, which bounds venue drift
without removing it, since the pass repeats one arm and the arms ran in blocks.
[`2026-08-27-two-engines-evolved-a-skill-and-neither-one-beat-a-placebo.md`](../notebook/2026-08-27-two-engines-evolved-a-skill-and-neither-one-beat-a-placebo.md).

**Memorisation, corroborated by reading the bodies.** GEPA's winner carries a
rules table asserting renewal at 61% utilisation and capacity headroom at 37%,
with a worked example using 2818 and 2032. SkillOpt's carries 63% and 213/300.
Those are values from single training items, and the corpus draws the
utilisation floor per item from a range and states it in every prompt, so an
arm carrying 61% contradicts a fact its own prompt supplies on almost every
item. The write-up counted three of six frozen winners carrying such
constants; the later audit records that the split cannot be enumerated from
any record now that the bodies are gone, and the paper says so where it makes
the claim. For the earlier matched-budget pair, every number in SkillOpt's
appended examples was checked value by value against the 70 training items and
found there.
[`2026-08-27-two-engines-evolved-a-skill-and-neither-one-beat-a-placebo.md`](../notebook/2026-08-27-two-engines-evolved-a-skill-and-neither-one-beat-a-placebo.md),
"What GEPA's winner did" and prediction 2;
[`2026-08-27-both-engines-wrote-the-answer-key-into-the-skill.md`](../notebook/2026-08-27-both-engines-wrote-the-answer-key-into-the-skill.md);
[`2026-08-31-the-paper-described-a-search-we-did-not-run-and-a-test-that-could-not-fail.md`](../notebook/2026-08-31-the-paper-described-a-search-we-did-not-run-and-a-test-that-could-not-fail.md).

**The arithmetic that now runs before a call.** Items come from templates and
the template is the independent unit. The unseen set is three templates, and a
one-sided sign-flip test over three clusters cannot return a p below
2^-3 = 0.125, so the three unseen primaries could not have rejected at any
outcome. `cluster_sign_flip` in
[`stats/cluster.py`](../evals/src/decision_evals/stats/cluster.py) now reports
that floor as a property of the design. The pre-registered minimum detectable
effect was 0.081 unseen and 0.075 seen at a design effect of 1.0; at the
design effect of about 2.0 that [`PROTOCOL.md`](PROTOCOL.md) specifies it is
0.1137 and 0.1054, about 2.6 times the largest gain observed.
[`2026-08-27-prediction-the-five-arm-study-before-the-first-call.md`](../notebook/2026-08-27-prediction-the-five-arm-study-before-the-first-call.md);
[`2026-08-31-the-paper-described-a-search-we-did-not-run-and-a-test-that-could-not-fail.md`](../notebook/2026-08-31-the-paper-described-a-search-we-did-not-run-and-a-test-that-could-not-fail.md).

**The re-read, reported beside the registered figures and promoted over
none of them.** With the control token stripped, from the same records, GEPA's
winner reads 0.7440 on the unseen set against 0.7024 for no document, and
0.8112 on the seen set against the placebo's 0.7679: 37 wins to 20, raw
p = 0.0166, Holm q = 0.0497 at the registered item unit, and p = 0.0469 at the
template unit, uncorrected, against the Holm worst-case threshold of 0.0167 the
prediction entry registered. The
placebo over no document on the seen set falls from 44/24 to 21/24. It is a
scoring rule chosen after the data on the arm it helps most, so the registered
null stands and both readings are reported.
[`STATUS.md`](STATUS.md), correction of 2026-09-01.

**What is lost.** Both searches wrote into `results/evolution/`, which
`.gitignore` excluded outright at the time, nothing was committed, and the
directories are gone. A content-hash search of 40,936 files on the machine
found neither body. Their SHA-256 hashes are on every record of the arms they
drove, so each arm is provably one fixed body that nobody can obtain
([`STATUS.md`](STATUS.md), appended 2026-08-28). Since 2026-09-02 the rule
re-includes each search's `winner.md`, `winner.json`, `lineage.jsonl`,
`run.json` and `search.log`, which would have kept both bodies had it landed
before the run. A re-run with the winners' bodies committed and seven or more
unseen templates is being prepared. Its prediction entry is not yet committed,
no study call has been made, and nothing here predicts its result.

## 6. The opener sentence

The one finding that recurs. The skill's description opens with a trigger
sentence full of illustrative quotes, "help me think this through", "should I
take it", and it is the part of the description that reads as the most
important. In every run that varied it, the opener cost false positives and
its recall contribution never separated from zero.

| run | key | what the opener did |
| --- | --- | --- |
| L5 | v1 | +1.8pp false-positive rate; `opener-only` against `full` on the 55 negatives, 7 items differ, 7 up, 0 down, p = 0.016; on the 18 positives, 3 differ, p = 0.11 |
| L7 | v2 | `no-opener` at FPR 0.0036 against `opener-only` at 0.1286 |
| N6 | v4 | `opener-only`'s pooled FPR 0.250, with the `l` band at 0.524 |
| N7 | v4 | `no-opener` the top arm at 0.9496, FPR 0.0756 |
| N10 | v6 | `full` FPR 0.1432 against `no-opener` 0.0818, 57 discordant negatives split 42 to 15, exact McNemar p = 0.0005; recall paired on 220 positives is one discordant call, p = 1.0000 |

Sources: [L5](../results/decision-making/2026-08-12-fe24180-l5/README.md),
[L7](../results/decision-making/2026-08-13-abb6862-l7-stakes/README.md),
[N6](../results/decision-making/2026-08-18-e632659-n6-confirmatory/README.md),
[N7](../results/decision-making/2026-08-19-d52236a-n7-remaining-arms/README.md),
[N10](../results/decision-making/2026-08-25-5ed5d38-n10-six-arms-v6/README.md).

The scope is as narrow as the finding is consistent. One description, one model
(Haiku), the screen tier, four answer-key versions that
`label_versions_comparable` refuses to compare against each other, and in N10
fifteen pairwise comparisons with no multiplicity control registered. L5 also
ruled out length as the mechanism: false-positive rate is not monotone in
description length across its four arms. In N10 the `full` and `no-opener` arms
were both collected as single processes, so the collection-load confound that
qualifies the other four arms of that run does not touch this comparison. The
confirm hypothesis is registered in the other direction, on a private holdout
that does not exist yet, and a v3 pre-registration would have to start from the
false-positive result.

## 7. What the harness now refuses

Each refusal below is the shape of an incident above, and
[`WHY_THESE_RULES.md`](WHY_THESE_RULES.md) holds the dated record behind each.

- **Pre-registration by git ancestry.** `assert_runnable` in
  [`prereg.py`](../evals/src/decision_evals/prereg.py) refuses a confirmation
  run whose pre-registration is uncommitted, is not an ancestor of `HEAD`, or
  postdates any result for that skill, and refuses again when the skill body or
  the analysis script hashes differently from the lock. It reaches a caller
  through `de confirm`, which is the change the wiring incident forced.
- **Run provenance.** A published run's README declares its answer-key version,
  matching the `set_version` in the records beside it, and names a prediction
  whose first commit is an ancestor of the run's commit. Two pre-convention runs
  are baselined, on a list that may only shrink.
- **Answer-key adjudication.** A trigger set on disk carrying an item with no
  three-judge blind record turns the gate red until the item is adjudicated.
- **Version comparability.** `label_versions_comparable`, `models_comparable`
  and `venue_comparable` in
  [`trigger_arms.py`](../evals/src/decision_evals/trigger_arms.py) each return
  the reason two arms may not be compared.
- **Wiring.** A module carrying a coverage floor that no entry point imports is
  refused, and an intentional gap is declared with the condition that would
  close it, in a register that errors when the entry becomes reachable.
- **A budget that can bind.** `BudgetLedger` in
  [`budget.py`](../evals/src/decision_evals/budget.py) refuses at construction
  on a venue that reports no cost and carries neither a call cap nor a clock cap.
- **Concurrency.** `run_arm` refuses more than one worker on a venue prefix
  measured to return different text under concurrency, with an escape only the
  falsifier uses.
- **Drift.** A living document with no review on record, or one whose named
  files have moved more than ten commits past the last review, is refused, and
  `de drift` prints the worklist furthest-behind first.
- **Claims.** A figure a page or a document publishes is bound to one sentence
  in one repository file through `site/claims.json`, and the gate refuses a
  figure whose sentence no longer exists.
- **The same 23 steps in CI.** `de check` is offline and deterministic, and
  [`.github/workflows/check.yml`](../.github/workflows/check.yml) runs it on a
  clean checkout, which is the arena that found `main` unable to import, two
  documents linking ignored paths, and a manifest built from a file that was
  never committed.

## What a reader can take

Two things are reusable whatever becomes of the skill.

The placebo arm. SkillOpt's winner took 21 of 21 validation items against the
seed skill's 18; the first score the lineage recorded for GEPA's winner was
over three items, GEPA's own return rule as cited evaluates on the validation
pool, and the records that would say which score it accepted on are gone.
Neither winner cleared a control matched on word count and structure on either
item set at the registered bar. The placebo has no
training history, so where it moved between the two item sets it showed that
"held out" and "different scenarios" were confounded in the design, from inside
the design. Run one.

The pre-run arithmetic. The sign-test floor of 2^-k for k clusters, the minimum
detectable effect at the design effect the protocol specifies, the per-item
ceiling computed from the items about to run, and the sentence naming what will
be computed from which records over which denominator by which function. Every
one of those was computable before the first call here, and each was computed
after. `cluster_sign_flip`, `minimum_detectable_effect` and `required_pairs` in
[`stats/`](../evals/src/decision_evals/stats/) are the functions, and the
[README](../README.md) shows them running.

What nothing here reached is the repository's own bar. A verdict comes from the
`confirm` arena, which has never run, on a holdout that does not exist, against
a corpus that a current model would have to be able to fail. Every number above
is either about firing, or scoped to one 1.7B model in a `dev` arena that emits
no verdict. [`SCORECARD.md`](../SCORECARD.md) is empty, and it is empty because
the instruments that would fill it kept finding their own defects first.
