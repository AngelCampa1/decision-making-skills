# 2026-08-25 — Three exclusion rules, and all three read high on the treatment

Three adversarial reviews ran against the three repaired Family B and C
instruments, before any measurement call was spent on any of them. All three
instruments were found unfit to fail anything, and the defect is the same shape
in all three.

**Every one of them excludes records from a denominator on a rule that is
correlated with doing the task well, and in every one the exclusion counts were
reported without an arm breakdown, so the attrition would have been invisible in
the published output.**

## What each one was

**`cascade`** gates specificity on attention: a control reply that never engages
the target leaves the denominator rather than banking a correct rejection. From
the shipped source,

```
youden_j         = sens - FA/(FA+CR)
youden_j_ungated = sens - FA/(FA+CR+U)
attention_rate   = (FA+CR)/(FA+CR+U)
```

so `J_gated = sens - FAR_ungated / attention_rate` exactly. The gate divides the
false-alarm rate by the attention rate. And because the scorer enforces
`accepts ⊆ attention`, a false alarm is *always* attended, so the gate can only
ever remove correct rejections. Same model, same four misfiles in twenty control
replies, verbosity alone: terse J = 0.500, verbose J = 0.800. Measured skill
effect +0.300, true change in the error rate zero. `cascade.md` Step 2 instructs
the model to enumerate, so the treatment arm attends more by construction. It
also ranks a 19-of-20 terse model below a 17-of-20 verbose one.

**`hinge`** keeps `OFF_LIST` in the denominator as a zero and lets `NO_BLOCK`
leave it. With behaviour held identical and arm-invariant in both arms, dropout
asymmetry alone moves the primary. Its battery carried no `NO_BLOCK` case in any
of five populations, so it could not see this.

**`council`** is the interesting one. Its estimator is clean and its author's
argument for that is correct: `BALANCED` leaves both numerator and denominator,
so the commit rate cancels out of the expectation under the null. The commit
rate comes back in through the **reporting gate**. The Manski bound has
`low = ρ·c`, and reporting requires `low > 0.5`, so

```
REPORTABLE  ⟺  c > 0.5 / ρ
```

The subtler the true effect, the more fluent the model must be to be allowed to
exhibit it. At the registered alternative ρ = 0.65 a model must commit on 76.9%
of draws; one that abstains more cannot produce a reportable result at any sample
size. `council.md` calls a tie that survived argument a finding, so abstention is
the competent behaviour, and the gate is tuned against it. Two models put through
the shipped scorer: one with a true effect of +0.10 and a 100% commit rate
reports; one with +0.25 and a 50% commit rate is refused.

## What the convergence is worth, stated honestly

It is not three independent discoveries and it would be easy to write it up as
though it were.

The `cascade` reviewer found it cold, with no prompt to look for it. I confirmed
the identity from the source myself, then **sent it to the other two reviewers
mid-review as an explicit instruction to attack their own exclusion rules.** So
the second and third are directed confirmations.

What survives that discount is still the part worth keeping. Each reviewer had to
find a different mechanism, and none of the three is the same as the others: a
division inside an index, an asymmetry between two zero classes, and a gate
sitting downstream of a correct estimator. The third is the strongest evidence
that this is a real law rather than one coding habit repeated three times,
because the `council` author had explicitly reasoned about the exclusion, got the
estimator right for the right reason, and the quantity still came back through a
door they were not watching.

## The rule that comes out of it

For every rule that removes a record from a denominator, three questions:

1. What makes a record leave?
2. Is that correlated with doing the task well?
3. Which direction does it push?

**A rule that cannot answer all three does not ship.** Across the three
instruments, six of the rules examined could not answer the third.

The corollary is about reporting rather than estimation, and it is what would
have caught all three at zero cost: **every exclusion class is printed by arm.**
None of the three did this. `council` computes five such fields and prints none
of them, and its module docstring claims one of them is printed.

## What else the three reviews found

Each also found item defects that had nothing to do with the law, which is worth
recording because it says what a review is for.

`hinge`'s answer key applied a per-tonne-of-flour price to a through-the-stone
tonnage — £10,160 where the arithmetic gives £9,570 — and contradicted its own
`shortfall_tonnes` line. Its matched arm's decoy was claimed dominated, and does
in fact fork at L = 97: the cliff check had been run on one arm's decoy and not
the other's. Both re-derived here from the YAML before being acted on.

`council`'s K03 fails disqualifier 17. Line 6 says one vessel does all of it,
line 22 puts the replacement's availability at 2026-11-20, and line 34 holds the
valuation only until 2026-11-09, so the figure that makes the second course
defensible lapses eleven days before the earliest date the course can be taken.

`cascade`'s two recorded blind responses turn out not to exist as transcripts.
They are author-written reconstructions, and everything resting on them —
including the expectation that specificity would come in at 1.0 — is unauditable
and now says so.

## Two things this did not cost

No measurement call was spent on any of the three. The plan budgeted the reviews
as a gate on the corpus, and what they gated was three instruments that would
each have produced a clean, publishable, wrong number.

And the direction is the one that matters. All three defects push the same way:
they read **high on the treatment arm**, because the treatment is a procedure that
makes a model enumerate more, commit more carefully, and write longer. An
instrument biased toward the null wastes a run. These were biased toward the
result the project wants, which is the failure that does not announce itself.
