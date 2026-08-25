# `ledger` triplet authoring brief, yield probe

**Audience:** an authoring sub-agent. Read `docs/TAILORING_CORPUS_SPEC.md` in full
first. This brief adds to it and overrides it only where it says so.

You are authoring **one** triplet. Four other agents are authoring one each, in
different domains. You will not see theirs and they will not see yours.

## What this measures

The registered kill: **if fewer than 3 of 5 triplets survive blind
re-derivation and an adversarial review briefed to prove the matched fact
governs, the volume dial does not solve the yield problem.** At the measured
one-in-five yield on `fit`, a powered corpus is unaffordable. This probe decides
whether the venue gets built.

Write the best triplet you can. Do not write a triplet that is easy to defend by
being trivial; a trivial item passes the gates and kills the venue at the next
stage instead.

## The form

Three files sharing one base scenario, differing by exactly one inserted bullet.

- **base** — the scenario, no insert.
- **governing** — one inserted fact that **changes** the elicited quantity.
- **matched** — one inserted fact of equal salience that **leaves it unchanged**.

Only the `prompt` block is model-visible. Everything under `key` and `meta` is
answer key and must never reach a call.

## What `ledger` is, and how it differs from `fit`

`fit` buys difficulty from the matched arm's neutraliser: the matched fact is
made non-obvious, which is what made it actually govern in two of three
first-pass triplets. That mechanism is why `fit`'s yield is one in five.

**`ledger` buys difficulty from volume instead.** The base carries a causal chain
and **K = 10 sibling facts in the same register**, all dated, all about the same
matter. The governing arm perturbs the one fact feeding the chain. The matched
arm applies **the same kind of edit, of the same magnitude, to a sibling fact
that is off the chain.**

The difficulty is that there are ten plausible facts and one of them matters. No
fact needs to be made subtle, so nothing is being hidden, so the matched label
stays defensible. That is the whole hypothesis this probe tests.

## The two design rules, fixed before you start

**R1 — actor routing.** Both inserts name the actor that the base's causal rule
sentence names, or neither does. Not one and not the other.

**R2 — skeleton identity.** Both inserts are the **same sentence skeleton** with
a bounded set of tokens substituted. Identical token count where you can manage
it, and the two inserts should differ in the object and a proper noun and in
close to nothing else.

R2 exists because the first authoring pass was separable 6 of 6 by a single
surface feature: every governing insert named a penalty attached to a status
change and every matched insert was procedural. Identical skeletons make that
class of leak impossible by construction.

## Requirements

**The chain.** The base states the rule as one verbatim sentence. You will record
that sentence exactly in `key.causal_rule_sentence`, and it must occur in the
base prompt **exactly once**, character for character.

**Volume.** Ten sibling facts under a heading like `Also on file:`, each dated,
each plausible, each in the same register. Two of them are the ones your inserts
perturb.

**Dates.** Every date in `YYYY-MM-DD` or `D Month YYYY`. Nothing else, in the
core and in the padding both. A corpus whose padding uses a different date
format from its core is separable by format alone.

**Today is 2026-08-25.** Say so in the first line of the prompt.

**Integrality.** The answer must be a whole number in its stated unit, from the
stated today. Write the rounding convention and the tolerance into the key. All
three first-pass triplets failed this with answers like 7.71 months.

**Non-zero.** The quantity can never be zero in any arm.

**Invented everything.** Invented people, companies, places, instruments,
jurisdictions. No real person or organisation. `datasets/probe/` uses "Meridian"
as house style.

## The seventeen disqualifiers

The fifteen in `docs/TAILORING_CORPUS_SPEC.md` §5 apply in full. Read them. Two
more were added on 2026-08-25 and are not in that file yet:

**16. The elicited question enumerates the constraints the answer is a minimum
over.** If your question names both binding constraints, a model can match two
nouns and be right with no domain reasoning. Ask for the quantity plainly.

**17. The governing arm's answer is infeasible against the base's own
information timeline.** If a deadline in the governing arm precedes the arrival
of information the decision needs, the right answer is "commit blind" in both
arms and the contrast disappears.

The four that kill the most items, in the order they killed them:

- **Disqualifier 10.** Before you call a fact non-governing, enumerate **every**
  date, commencement, waiting period and precondition in the base that could
  delay the moment that fact starts to bite. One triplet died because a 30-day
  lead time was neutralised against a slot 40 days out, while the plan carrying
  the clause did not commence until a date that pushed the filing past the slot.
- **Disqualifier 11.** Compute where the matched fact would land the answer if it
  did govern. If that lands near where the governing fact lands it, there is no
  contrast. One triplet died at 8.29 against 7.71.
- **Disqualifier 15.** The governing arm must admit **one** reading. One triplet
  died because a reader may decline to read "30-litre returnable containers" as
  kegs; another because a slot was *offered* rather than accepted against a base
  saying "that is the one I hold". This is the worst failure of the set, because
  it biases the primary toward zero and makes a null unreadable.
- **Disqualifier 14.** The base must not pre-announce that a catch is coming.
  "On the face of it", "nothing in it requires more", "it is not urgent" all
  appeared in first-pass bases and all bias toward movement.

## Two sentences you must be able to write

**The professional's sentence.** One sentence saying why the generic answer is
wrong in the governing arm, citing only the governing fact. If you cannot write
it in one sentence, the item is vague rather than hard, and it is cut.

**The mirror sentence.** One sentence saying why the matched fact leaves the
answer alone, citing the base sentence that neutralises it. If you cannot write
it, you do not know that your matched fact is non-governing.

Both go in the key.

## Output

Three files in this directory, named `<your id>-<slug>-{base,governing,matched}.yaml`.

```yaml
set_version: 1
construct: ledger
triplet: <your id>
arm: base | governing | matched
role: base | treatment | control
domain: <your assigned domain>
mechanism_type: <your assigned mechanism>
k_siblings: 10
spec_variant: A
elicited:
  question: <the question, verbatim from the prompt>
  unit: <days | weeks | months>
  kind: scalar
prompt: |
  <the model-visible text, ending in the question and
   "Answer with a single number of <unit>.">
key:
  causal_rule_sentence: >-
    <verbatim from the base prompt, occurring there exactly once>
  rule_actor: <the person or body that sentence names, or NONE>
  insert_skeleton: <the shared skeleton both inserts substitute into>
  delta_kind: inserted_bullet
  fact: <the inserted sentence, verbatim>
  governs: true | false
  expected_direction: up | down | none
  expected_value: <integer>
  arithmetic: >-
    <every quantity used, where in the prompt it came from, the operation,
     and the final count. A reader must be able to check this against the
     prompt without trusting you.>
  rounding: <the convention, and the tolerance>
  professional_one_sentence: >-     # governing arm only
    <...>
  mirror_one_sentence: >-           # matched arm only
    <...>
  preconditions_enumerated:         # matched arm only
    - <every date/gate in the base that could make this fact bite, and why
       each one does not>
  salience_match: >-                # matched arm only
    <how the two inserts match on object class, surface form, magnitude,
     alarm, length, position and deontic register. Name any dimension you
     did NOT fully close. An honest seven of eight beats an asserted
     eight of eight.>
meta:
  personas_invented: true
  real_personal_data: false
```

## Your assignment

Read it from the message that dispatched you. It fixes your domain, your
direction of movement, and your mechanism type. Do not change them: they are
balanced across the five authors so the probe is not five copies of one
scenario.

## Before you report

Re-derive all three answers yourself from the `prompt` text alone, without
looking at your own key. If you cannot recover the base value, the base is
under-specified and disqualifier 6 fires. If the matched arm does not land
exactly on the base value, you have a governing matched fact and the item is
cut before it costs anyone else a call.
