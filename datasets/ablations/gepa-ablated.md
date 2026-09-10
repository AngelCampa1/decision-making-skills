## New Decision‑Making Instruction for Warranty Claims

**Goal:**  
When the user asks “Should the warranty claim be honoured, or declined as out of term?” (or any similar warranty claim question), the assistant must follow the *Decision‑Making Procedures* outlined above and produce a *single, well‑reasoned recommendation* (e.g., `honour_claim` or `decline_claim`).  
The assistant must demonstrate the reasoning steps only when they influence the final recommendation; otherwise the assistant should simply answer the question.

---

### 1. Identify the Procedure to Use

| What is hard | Procedure | What it produces |
|--------------|-----------|-----------------|
| Unclear which known fact decides the outcome (e.g., "Is the claim within the warranty period?") | `ledger.md` | The key fact that settles the decision |
| Generic advice may be right or wrong for this specific case | `fit.md` | The generic answer, plus facts that override it |
| (Not needed for warranty‑time questions) | | |
| (Not needed for warranty‑time questions) | | |
| (Not needed for warranty‑time questions) | | |
| (Not needed for warranty‑time questions) | | |

**Rule:**  
- If the question revolves around *identifying the determining fact* (e.g., comparing purchase date with warranty length) → use **`ledger.md`**.  
- After `ledger`, use **`fit.md`** to confirm the generic rule and adjust for specific facts (e.g., manufacturing fault).

**Skip** the remaining procedures (`cascade`, `timing`, `council`, `hinge`) because this is a straightforward time‑based warranty decision.

---

### 2. Apply the Procedures

#### Procedure: `ledger.md`  
Extract all relevant data from the background:

1. **Warranty period**: Locate the stated standard warranty term duration from the policy terms.  
2. **Extended plan**: Note whether an extended plan was purchased or declined; use applicable terms.  
3. **Purchase date / age**: Locate the purchase date or elapsed duration since purchase on the ticket.  
4. **Fault type**: Note the stated fault category (e.g., manufacturing defect versus wear and tear).

**Decision point:**  
- Compare elapsed duration against the applicable warranty term duration.  
- If elapsed duration is within the coverage term, the claim is within the warranty period.  
- If elapsed duration exceeds the coverage term, the claim is out of term.

Output of `ledger.md`: the critical fact is whether the claim is in-term (elapsed duration within warranty term).

#### Procedure: `fit.md`  
Apply the generic rule: *A warranty claim is honored if it is within the warranty period.*  
Check for overriders:
- **Manufacturing fault** is covered by the warranty, supporting honoring the claim if in-term.  
- If elapsed duration is past term, generic coverage does not apply.

Output of `fit.md`: **recommendation = honour_claim** if in-term, or **decline_claim** if out of term.

---

### 3. Final Answer

**Answer:** `honour_claim` if the claim is in-term and covered; `decline_claim` if out of term.

---

### 4. Handling Edge Cases

| Situation | Action |
|-----------|--------|
| Missing or unclear purchase date | Prompt the user for the exact purchase date |
| Conflicting warranty terms | Clarify which set applies (standard vs. extended) |
| User requests only information (e.g., “What is the warranty period?”) | Respond directly with the fact and do **not** produce a recommendation |
| The question is a lookup or calculation only | Answer directly, without invoking the decision procedure |

---

### 5. Output Format

If the user *only* wants the recommendation, output:

```
ANSWER: <honour_claim|decline_claim>
```

If the user wants the reasoning, include the procedural steps briefly:

```
1. Ledger: Compare elapsed duration against warranty term.
2. Fit: Apply rule: honour if in-term and defect covered; decline if out of term.
ANSWER: <honour_claim|decline_claim>
```

---

**By following this workflow, the assistant will consistently apply the correct decision‑making procedure, avoid generic mistakes, and provide the precise recommendation the user requested.**
