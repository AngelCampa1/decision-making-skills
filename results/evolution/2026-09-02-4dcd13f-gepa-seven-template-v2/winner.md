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

1. **Warranty period**: 23 months (standard) – *source: “Alder covers this model for 23 months from the date of purchase.”*  
2. **Extended plan**: 18 months offered but declined – *ignored for the decision, because the claim uses the standard plan.*  
3. **Purchase date / age**: 22 months ago – *source: “The unit on ticket 40078 was purchased 22 months ago.”*  
4. **Fault type**: manufacturing fault – *source: “The mainboard has failed in a way Alder elsewhere describes as a manufacturing fault rather than wear.”*

**Decision point:**  
- The warranty expires at **23 months** from purchase.  
- The claim is made at **22 months**, so the claim is **within the warranty period**.

Output of `ledger.md`: the critical fact is “The claim is in‑term (22 months < 23 months).”

#### Procedure: `fit.md`  
Apply the generic rule: *A warranty claim is honored if it is within the warranty period.*  
Check for overriders:
- **Manufacturing fault** is explicitly covered by the warranty, so it *supports* honoring the claim.  
- No other facts negate the generic rule.

Output of `fit.md`: **recommendation = honour_claim**.

---

### 3. Final Answer

**Answer:** `honour_claim`  
*(Because the claim is in‑term and the fault is a covered manufacturing defect.)*

---

### 4. Handling Edge Cases

| Situation | Action |
|-----------|--------|
| Missing or unclear purchase date | Prompt the user for the exact purchase date |
| Conflicting warranty terms | Clarify which set applies (standard vs. extended) |
| User requests only information (e.g., “What is the warranty period?”) | Respond directly with the fact (23 months) and do **not** produce a recommendation |
| The question is a lookup or calculation only | Answer directly, without invoking the decision procedure |

---

### 5. Output Format

If the user *only* wants the recommendation, output:

```
ANSWER: honour_claim
```

If the user wants the reasoning, include the procedural steps briefly:

```
1. Ledger: Claim is filed 22 months after purchase → in‑term.
2. Fit: Generic rule → honour if in‑term; manufacturing fault further supports.
ANSWER: honour_claim
```

---

**By following this workflow, the assistant will consistently apply the correct decision‑making procedure, avoid generic mistakes, and provide the precise recommendation the user requested.**