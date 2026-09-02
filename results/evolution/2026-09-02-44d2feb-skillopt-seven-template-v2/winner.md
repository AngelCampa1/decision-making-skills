# Decision making

Six procedures. **Read one.** Which one depends on what is hard about this
particular decision — not on its subject.

| What is hard | Read | What it produces |
|---|---|---|
| A pile of context arrived and it is unclear which already-known fact decides it — the choice itself, not what acting on it would set off | `ledger.md` | what bears on it, what was set aside, and why |
| The advice may be generically right and wrong for this person | `fit.md` | the generic answer, and the facts that would overturn it |
| The action looks fine and the worry is what it starts, or what it spends | `cascade.md` | the chain, what it forecloses, and the order |
| The direction is settled and the question is when | `timing.md` | the undo price, the real deadline, what waiting buys |
| Several positions are each defensible, and whichever was argued first has the advantage | `council.md` | the case for each, argued fairly, and which one survives |
| The fact the decision actually turns on was never given, not just buried in what's already known, and it's unclear whether asking for it is worth the wait | `hinge.md` | which gaps would change the answer, and the answer now or the one question to ask |

## Abort if

- It is a lookup, a calculation, or a technical diagnosis.
- The work is creative or exploratory rather than a decision.
- They want information, not a recommendation. Give them the information.

## Choosing

## Threshold Validation

## Automated Numeric Threshold Evaluation

### Handling Derived Thresholds (headroom, percentages, and compound conditions)

Many policies express thresholds in terms of a derived baseline rather than a flat number. Typical patterns include:
- *Require X % headroom above a projected peak*, e.g. "**25 % headroom above forecast peak**."
- *Limit to Y % of a target*, e.g., "**must remain below 8 % error rate**."
- *Add a fixed cushion*, e.g., "**additional 30 days cushion**."

The agent should:
1. Detect expressions that combine a numeric constant with a word such as "%", "percent", "percentage", or "cushion".
2. Parse the arithmetic that defines the derived threshold. For a head‑room policy, compute `required_threshold = forecast_peak × (1 + headroom_fraction)`. For a percentage upper bound, interpret the percentage as a rate and compare the current value directly to the percentage number.
3. Apply the same comparison logic (`≥`/`>`/`≤`/`<`) as in the basic numeric‑threshold step.
4. If the derived comparison yields a decisive outcome, skip the rest of the decision chain; otherwise continue as normal.

This addition covers use‑cases such as deciding whether to scale a cache tier before a campaign, or whether to accept a refund under a staged‑window policy.

**Purpose** – When a user’s background contains a numeric value that can be directly compared against a policy‑defined threshold, the agent must evaluate that comparison first and return the resulting action immediately. Only if no applicable numeric threshold is detected does the agent proceed to the full decision chain (ledger → fit → cascade → timing).

**Procedure**
1. **Extract thresholds** – Scan the background for explicit numeric statements that appear to define a cutoff. Typical patterns include phrases such as ``threshold of X``, ``X months from purchase``, ``X days before breach``, or ``X points or higher``. Capture the numeric value and the implied policy rule (e.g., *"honour claim if purchase < X months*", *"expedite if delay > X days"*).
2. **Identify the client’s value** – Locate the corresponding value from the user’s context that needs to be compared against the extracted threshold (e.g., miles shipped, months since purchase, credit score).
3. **Apply the comparison** – Use the rule semantics that the policy document states. Common forms are:
   * **>=** threshold → positive outcome (e.g., honour, expedite, auto‑approve)
   * **>** threshold → positive outcome
   * **<=** threshold → negative outcome
   * **<** threshold → negative outcome
   When multiple thresholds apply (e.g., a priority contract vs. a standard contract), choose the one that matches the explicit context attribute.
4. **Return the action** – If a comparison produces a definitive outcome, record that decision and **skip** the rest of the decision chain. If no valid numeric comparison can be made, continue with the existing four‑step ledger → fit → cascade → timing sequence.

**Examples**
- *Warranty* – Coverage of 23 months, 22 months elapsed ⇒ 22 < 23 → *honour_claim*.
- *Shipping* – Priority contract allows a 4‑day delay; consignment 10 days late ⇒ 10 > 4 → *expedite*.
- *Loan Review* – Auto‑approve threshold 665, score 737 ⇒ 737 ≥ 665 → *auto_approve*.

**Fallback** – In the absence of an explicit numeric threshold, or if the background does not provide a clear numeric value, the agent must proceed with the standard decision flow.
- **Identify all numeric thresholds** in the background (e.g., days late vs SLA, months covered vs elapsed months).  Explicitly calculate the current value and compare it to the threshold.
- If the comparison favors one option over the other, treat that as the deciding evidence before any further procedural checks.
- If the comparison is ambiguous (e.g., a value lies exactly on the threshold or the data is incomplete), ask the user for clarification before proceeding.

Ask what would most change the answer if you got it wrong. That names the
procedure. If nothing obvious separates them, that ambiguity is itself
information: reread each candidate's *Abort if* list and take whichever one
nothing on it rules out, rather than defaulting to one procedure by habit.

**If no procedure fits, that is the answer.** Not being able to name one is
usually a sign this is a lookup, a technical judgement, or a request for
information wearing a decision's phrasing — go back to *Abort if* and answer
directly.

`council.md` and `hinge.md` sit outside the four-chain, and outside each other
— each runs alone. Both, when they apply, run before `ledger`, `fit`, `cascade`
and `timing`: until the positions are settled or the missing fact is asked for
or guessed at out loud, there is no single action or answer for the other four
to work on. Where both seem to apply, resolve the missing fact first — it can
collapse a disagreement `council.md` would otherwise have to argue out.

Within the four, more than one can apply. Run them in this order, because each
one feeds the next: **ledger → fit → cascade → timing.** You cannot tell what
fits a person until you know what is on the table; you cannot follow
consequences until you know which action you are considering; timing is last
because it is a question about an action already chosen.

Two is usually the most that earns its place. Three means the decision probably
needs breaking into two decisions.

## The point is the decision

These are working procedures, not an output format. **Do the procedure, then
answer.** A reply that hands back four labelled blocks and no recommendation has
turned someone's question into an audit of their question.

Show the working only where it changes what you would say, or where the person
would reasonably want to check it. The person asked what to do.

If a procedure is producing worse answers than thinking directly, say so. That
is worth more than politely using it.

## Threshold‑Based Decision

When a decision hinges on a numeric value crossing a hard boundary, use a direct comparison:

1. **Identify** the relevant number(s) in the background (e.g., credit score, days since delivery, percent error rate, forecast demand).
2. **Locate** the supporting threshold(s) provided in the background or in the policy (e.g., approval threshold, appeal window, warranty duration, capacity headroom, error‑rate trigger).
3. **Compute** any derived figures (e.g., % headroom: `forecast × 1.25`, time‑delta: `current_date – past_event`).
4. **Apply** the comparison rule: `value ≥ threshold` → one choice, else the alternative.

When a single numeric comparison suffices, skip the more elaborate four‑step ledger→fit→cascade→timing flow. If multiple thresholds interact (e.g., a lower and an upper bound), evaluate them in order of significance.

### Example
- **Credit approval**: `score = 737`, `approval_threshold = 665`. Since 737 ≥ 665, choose *auto‑approve*.
- **Appeal court**: `days_since_result = 44`, `window = 56`. Since 44 ≤ 56, accept the appeal.
- **Warranty**: `months_since_purchase = 22`, `coverage = 23`. Since 22 < 23, honour the claim.

This pattern captures all the single‑step numeric decisions seen in the batch and complements the existing procedural flow.

## Handling Sub-Policy Threshold Selection

Many policies bundle several threshold values that apply to different groups (e.g., priority vs. standard shipping contracts, research vs. taught appeal windows).  To avoid applying an irrelevant threshold, the agent should:

1. **Extract the identifying context** from the user’s background (e.g., `contract_type = "priority"`, `programme = "research"`).  These are usually explicit labels or adjectives.
2. **Collect all candidate thresholds** that mention that identifier or fall under a generic “else” clause.
3. **Select the threshold that matches the extracted context**—if more than one matches, choose the one that is most specific or the strictest rule.
4. **Apply the numeric comparison** using the chosen threshold as in the generic threshold logic.
5. **If the comparison resolves the decision, return the outcome immediately and skip the rest of the decision chain.**

This logic must be applied **before** any generic threshold evaluation to ensure the correct sub‑policy is used.

## Interpreting Directional Qualifiers in Thresholds

Threshold expressions often come with qualifiers that indicate the intended comparison direction.  The agent should map these common qualifiers to operators before evaluating numeric values:

| Qualifier Phrase | Operator |
|-------------------|----------|
| more than / greater than | `>` |
| at least / minimum | `≥` |
| less than / under | `<` |
| up to / maximum / at most | `≤` |

Implementation steps:

1. Normalise the qualifier text by removing punctuation and converting to lowercase.
2. Map the qualifier to its operator as above.
3. Use the resulting operator in the comparison between the user’s numeric value and the extracted threshold.
4. If the qualifier is missing or ambiguous, fall back to the operator defined by the policy text itself.

Correct handling of qualifiers prevents mis‑application in scenarios such as “12‑day refund window” vs. “up to 42 days” or “more than 8 % error rate”.
