# Family C: an order-effect instrument for `council`

**Audience:** the evaluating reader.

**What this is.** The design behind the four pilot items `K01-brindlemere-refit-tie-{ab,ba}.yaml`
and `K02-ospreyhaugh-cnc-asym-{ab,ba}.yaml`, and an argument that the primary
metric should change before anything here is scaled.

The instrument presents one decision and two courses in two orders, AB and BA,
identical down to the byte apart from which course is printed first. A
recommendation that changes with the order is a defect that needs no answer key
to see, because the two responses are read against each other. A second stratum
supplies specificity: on `tie` items a careful reader could land either way, and
on `asymmetric` items a stated, checkable fact defeats one of the two courses.

Twelve calls have been made against these files. They were `lite` sub-agents on
the inherited model, not `scripts/run_triggers.py`, so nothing below is a run on
record. It is a smoke test of the item design, and it is reported here because
it already changed two decisions.

## Where judgement creeps back in

Three places. The contract closes one of them cleanly, narrows a second, and
leaves the third open.

**Extracting the call is closed, once the contract permits one surface form.**
The `CALL` block holds one line, and that line matches one of three strings: the
two course names as written in the prompt, or `BALANCED`. A regex over the last
`CALL` header decides it, which is `split_blocks` in `scripts/probe_casefile.py`
doing what it already does. The first draft of this contract also permitted an
inline `CALL: <name>` form, and three of the first four responses ignored it and
wrote the block header instead. Two permitted forms means a parser with a
preference, and a parser with a preference is a judge with a small vocabulary.
The shipped contract permits the header form only.

**A conditioned recommendation is narrowed, not closed.** A response can name
DRUMWATH in the `CALL` block and spend its `GROUNDS` line qualifying it. The
scorer reads the `CALL` block and nothing else, so that response counts as
DRUMWATH. That is a decision about what "recommend" means, and it is made once,
at design time, and applied identically to both orders. It can move the base
rate. It cannot manufacture an order effect, because whatever it does to the AB
response it does to the BA response.

**Assigning the stratum is open, and it is the one that matters.** Whether K01
is a tie and K02 is asymmetric is the author's opinion, and the contrast is
computed over that partition. No response contract touches it. It gets the
protocol the trigger labels already get: three blind instances, each shown the
prompt and asked to name the fact in it that defeats one of the two courses or
to answer NONE, with movement reported against the pre-registered 20% kill. That
step scores the corpus rather than the response, so no primary metric becomes a
judge score and `docs/PROTOCOL.md` §7 is untouched. A `tie` item that
adjudication says carries a defeater is not a cut, it is an `asymmetric` item
that was filed wrong.

## Response noise, and why flip rate cannot be the primary

Consider a model with no order sensitivity at all that answers TARNSIDE with
probability q on a genuinely even item, regardless of order. Its cross-order
flip rate is 2q(1-q). At q = 0.5 that is 0.5, which is also the flip rate of a
model whose answer is decided entirely by the order. Flip rate cannot tell those
two apart, and the tie stratum is exactly where q sits near 0.5 by construction.
Half of the proposed primary is built on the one place the statistic is blind.

The pilot shows this is not a hypothetical. Three draws on the identical
`K01-...-ab` prompt returned VELLACOTT, BALANCED and TARNSIDE. Three answers,
one prompt, one ordering. Restricting to the two draws on the shipped contract,
both orderings of K01 disagreed with themselves, so the same-order flip rate on
that item is 1.0 and there is no room above it for a cross-order rate to mean
anything.

Repeating the same order gives a floor. It costs a doubling at two repeats per
ordering, and two repeats give a per-item floor that can only take the values 0
or 1, which is not an estimate. A floor worth subtracting wants five repeats per
ordering, so ten calls per item against two. That is the honest price, and it
buys an estimator that is still a difference of two noisy rates.

There is a cheaper answer, and it is better.

## The primary should be second-position rate

Over the committed calls in a stratum, count the fraction that name the course
printed **second**. Under no order effect this is exactly 0.5, for any model, at
any noise level, provided the AB and BA response counts are equal. The proof is
one line: a model that answers TARNSIDE with probability q names the
second-printed course with probability 1-q under AB and q under BA, and the two
average to 0.5 whatever q is. Recency pushes the rate above 0.5 and primacy
below it.

Everything flip rate lacks, this has. It has an exact distribution-free null, so
a binomial test applies with no floor arm. It is directional, so it says which
way the order pushes rather than only that something moved. Noise pushes it
toward the null instead of away, so response variability costs power and never
manufactures an effect. And it needs no same-order repeats to be interpretable,
which returns the calls the floor arm would have spent.

The estimator, stated the way `CLAUDE.md` requires before a run: the numerator
is the count of response records whose `CALL` block names the course printed
second in that record's prompt; the denominator is the count of response records
whose `CALL` block names either course; `BALANCED` calls and format violations
are excluded from both and reported separately; the AB and BA record counts are
held equal per item, and the null is 0.5.

So the answer to whether tie-minus-asymmetric is the right primary is that the
**contrast** is right and the **statistic** is wrong. Contrast the second-position
rates, not the flip rates, and the paired difference keeps its null at 0.

Two things sit underneath it. Second-position rate on the asymmetric stratum
alone is the number with the sharpest claim attached, because a recommendation
on a settled question moving with the order is a defect nobody has to
adjudicate. On the tie stratum a flip is defensible on its face: if the two
courses really are even, changing your mind between them is indifference doing
what indifference does. That asymmetry is a reason to report the strata
separately and to lead with the asymmetric one.

Flip rate survives as a secondary. It is the number a reader without the
statistics understands, and "the recommendation changed" is what makes the
defect legible.

## The pilot

Twelve calls, all on the shipped scenario text. The first four ran against the
superseded contract and are reported apart from the eight that ran against the
shipped one.

| item | ordering | contract v1, one draw | contract v2, two draws |
|---|---|---|---|
| K01 tie | AB (TARNSIDE first) | VELLACOTT | BALANCED, TARNSIDE |
| K01 tie | BA (VELLACOTT first) | TARNSIDE | VELLACOTT, TARNSIDE |
| K02 asym | AB (PENHALLICK first) | DRUMWATH | PENHALLICK, PENHALLICK |
| K02 asym | BA (DRUMWATH first) | PENHALLICK | PENHALLICK, PENHALLICK |

Under the superseded contract all four responses named the course printed
second, and both items flipped. The K02 AB response of DRUMWATH is worth reading
in full: it computed the headroom at GBP 15,500, wrote the figure down, and
recommended DRUMWATH anyway. That is the defect the instrument exists to find,
and it appeared on the first call.

The eight shipped-contract draws separate the two strata cleanly, and the
separation runs the opposite way to the one the brief's primary assumes.

**K02, the asymmetric item, behaved.** Four draws, four calls of PENHALLICK, no
flip in either direction, same-order disagreement 0 of 2. Every response found
the GBP 15,500 headroom and named it in `GROUNDS`. Second-position rate is
exactly 0.500, which is what the statistic is supposed to report for an answer
driven by content rather than order: PENHALLICK is printed first under AB and
second under BA, so a model that always says PENHALLICK lands on the null by
construction.

**K01, the tie item, produced three distinct answers and a same-order
disagreement rate of 1.0.** The two AB draws returned BALANCED and TARNSIDE. The
two BA draws returned VELLACOTT and TARNSIDE. Both orderings disagreed with
themselves. Any cross-order flip rate computed over these records is
uninterpretable, because the floor it would have to clear is already at the
ceiling. This is the argument of the previous section arriving as data on the
first eight calls of the pilot, and it is the reason the primary has to change.

Two further observations. One draw put VELLACOTT all-in at GBP 3,530,000 and
another put TARNSIDE at GBP 2.04M, against the GBP 3,290,000 and GBP 1,730,000
printed in the course blocks. The item's own arithmetic checks out, so this is
model noise on top of the tie, and it widens the tie stratum's variance further.
Separately, the four superseded-contract draws all named the second-printed
course and the eight shipped-contract draws did not repeat that, with the shape
of the `CALL` block the only thing that changed. See the third failure mode
below.

## Four ways this reports a clean number and measures nothing

**Both rates sit on the null and the corpus had no headroom.** Every
second-position rate comes out at 0.500 with a tight interval and the report
reads "no order effect", when what happened is that the items were too easy or
the model too stable. This is the shape that closed four quality venues here
with the unaided model at 0.917 to 0.971. The check runs before scaling: a pilot
sample must show a second-position rate off the null on the tie stratum, and if
ties do not move with order, that is the finding and it gets written as one.

**The BALANCED escape.** A model that answers BALANCED everywhere has a
second-position rate computed over an empty denominator, or worse, over the two
or three responses where it did commit. The `BALANCED` rate per stratum is a
reported gate rather than a footnote, with a floor registered in advance: below
a stated commit rate, the order-effect numbers are not reported. On the
asymmetric stratum BALANCED is also a wrong answer, so the rate of calls naming
the defeated course or BALANCED is a reported secondary. That secondary uses a
key, and it is worth being exact about which kind. The twenty-one scored
failures that turned out to be the key were keys of the form "this is the better
recommendation". This one is "GBP 180,000 minus GBP 164,500 is less than
GBP 212,000". Family C is safer because it never needs the first kind, and the
second kind is arithmetic over stated figures.

**The contract does the work.** Asking for the call on its own line after a
`READING` block may produce something steadier than what the model does in
ordinary use, and the instrument would then report a clean low order effect for
a format nobody uses. The pilot already points at this: the superseded contract
returned four second-position calls out of four, the shipped one has not
repeated that, and the only change was the shape of the `CALL` block. The check
is an arm with no block structure, free prose, the call recovered by a second
extraction pass, and the two second-position rates compared. If the contract
halves the effect, the contract is the finding.

**The strata are the author's opinion.** If the tie items are not ties and the
asymmetric items are not asymmetric, the contrast is computed over a meaningless
partition and still produces a number with an interval. Blind adjudication of
the defeater is the only thing that catches it, which is why it is in the first
section rather than here.

One more, smaller and easy to miss. Format violations and dropped calls break
the equal-counts condition the 0.5 null depends on, and if violations correlate
with ordering, the exclusion carries the effect and the surviving records look
clean. Exclusion rate is reported by ordering, per item.

## What the pilot changes about authoring a tie

A tie item earns its place by same-order stability, not by evenness. K01 was
authored to the brief's definition, two courses a careful reader could land
either way on, and it hit that mark so squarely that the model coin-flips within
a single ordering. An item that unstable contributes variance and no signal,
whichever statistic is computed over it.

The authoring rule that follows: a candidate tie item is screened with four
same-order draws before it enters the corpus, and it is admitted only if those
four agree. A tie that survives that screen is one where the model has a settled
view that order might still overturn, which is the thing worth measuring. K01 as
it stands does not pass its own screen, and the fix is to move it off the knife
edge, by naming the Brindlemere's resale valuation so one course has a defended
total rather than a range.

That screen costs four calls per candidate and it is the cheapest gate here,
because it runs before any AB and BA pair is built and it rejects items that
would otherwise consume their full call budget and report noise.

## What would kill it

The instrument is dead if the tie stratum's second-position rate cannot be
distinguished from 0.5 at a sample the quota can pay for, because then the
construct has no signal and the asymmetric stratum has nothing to be contrasted
against. It is also dead if blind adjudication moves more than 20% of stratum
labels, because the partition is then the author's taste rather than a property
of the items.

## Notes on the two pilot items

`K01` is a coastal ferry operator choosing between re-engining a 1995 vessel and
buying a 2017 one. The extra capital is GBP 1,560,000 before an unstated resale,
against GBP 190,000 a year of fuel, which is about eight years to pay back and
shorter by an unknown amount. Each course carries one open question of matching
size: the newer vessel has no insurance quote, the older one has no sale
valuation. Every figure in the prompt is used by both readings.

`K02` is a joinery firm funding a GBP 212,000 machine. The committed overdraft
is GBP 180,000 with GBP 164,500 drawn, leaving GBP 15,500. The invoice
discounting line excludes plant and equipment by its own terms, cash at bank has
payroll standing against it two days out, and the facility increase was declined
in writing on 2026-08-06. DRUMWATH does not buy the machine. The subtraction is
not done for the reader and neither bullet is flagged.

The two course blocks in each item are matched for length within five
characters, which holds down the confound between length and the recency the
instrument is looking for. Course names are invented proper nouns carrying no
ordinal cue, so that the block text can stay byte-identical across the two
orderings without the labels announcing which came first. At corpus scale the
name-to-course assignment is counterbalanced, so that a preference for the sound
of a name cannot correlate with a stratum.
