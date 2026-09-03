# What an eval harness found about itself

**Audience:** the evaluating reader.

A harness built to test whether a written decision procedure, a markdown file
dropped into a coding agent's context, improves that agent's decisions found
something else first: the scenarios it had authored could not be failed. A
current model solved every one of them with no help at all.

The harness caught that itself. It is the first of four breaks below, out
of <!-- de:fact broken-measurements -->eleven<!-- /de:fact --> the project has
now caught in its own measurements. Each was cheap to find once somebody
looked, and each would have produced a publishable number if nobody had.

## The corpus could not fail

Every single-prompt decision scenario authored here with a right answer was
solved by the control arm, the condition that holds the items and the model
fixed and loads no skill document at all.

The scalar scenarios, where the answer is a number, were read blind 99 times
across 18 arms in six domains. Every arm was unanimous and every arm equalled
the answer key, in a bare condition and a scaffolded one alike: Youden's J
= 1.000. J, also called informedness, is the true-positive rate plus the
true-negative rate minus one, so 1.000 is perfect and 0 is a coin flip. The
figure that would close the venue and abandon that whole family of scenarios,
0.70, was committed to git before the readings were taken, which is all
pre-registration means: the prediction is on the record before the data is. On
the hardest version of the item, all nine readers wrote out all five arithmetic
steps it was built to demand, and got it right anyway.

A second family used a different answer shape, naming the one unsettled fact
that would put you on the other course: +0.850 machine-scored over 40 blind
readings, and +0.950 when a blind adjudicator saw the same 40 answer blocks
with the arm labels stripped. Two registered validity checks failed in that
run, so the item says nothing about resistance to decoys. A third family of
three scenarios came back at +1.000, +1.000 and +0.850 over 40 readings each.
One of those +1.000s rests on a guard list the item's author wrote; without it
the machine score is +0.650. The blind judges ratified all seven affected
readings, and both figures are published.

The one scenario family with no answer key behaved differently, which is what
makes the rest hard to explain away. It scored two orderings of the same
material against each other, so no label was available to be easy: a
second-position rate of 0.4722 on 144 kept records, against a null of 0.5,
exact p 0.5598. A real null, with nothing for a procedure to fix.

The ceiling was not confined to one model. The corpus behind the controlled
study below was calibrated on a 1.7B model, where an empty prompt scores 0.702
over 728 items. A screen of hosted models given no skill at all found every one
measured solving it: seven rows, 0.933 to 1.000, in the file that screen wrote.

Four pre-registered predictions bet on headroom and all four lost. Two of them:
that a deliberately repaired scalar item would stop being unanimous, which came
back unanimous at 9 of 9, and that six harder templates, five written from
scratch for the purpose, would hold a 30B model between 0.60 and 0.75, which
came back at 111 of 117, or 0.949.

How this was found is what transfers. The control arm was run and read before
the corpus was accepted, ahead of any treatment arm producing a pleasing
number. A corpus nothing can fail still returns p-values.

## A ruler scored 89%

A second corpus asks a narrower question: does the agent load the skill at all
when it should? Its positive examples had a median length of 18 words and its
negatives had 8.

A rule with no model in it, fire if the turn is 18 words or longer, scores
0.890 against version 2 of that corpus's answer key. The two best arms measured
on that key score 0.9795 and 0.9863. So every result on that corpus was
competing for about <!-- de:fact headroom-points -->nine points<!-- /de:fact -->
over a ruler, and the corpus is
<!-- de:fact corpus-solvability -->89%<!-- /de:fact --> solvable by counting
words.

Corrections here are appended, never edited over the original, which is why
both readings of that figure are on the record: it was first published as six
points, arithmetic that set a version 2 ruler beside a version 1 arm.

The rebuilt corpus holds its best model-free shortcut, a one-split decision
tree over eight trivial surface features, to
<!-- de:fact word-trick-ceiling -->0.7054<!-- /de:fact -->, against 0.6667 for
always guessing the commoner label.

Scoring a new evaluation set with something that cannot possibly be doing the
task costs an afternoon, and it is the cheapest check here. Every trigger
measurement predating the rebuild still carries that caveat.

## Twenty-one of twenty-one scored failures were the answer key

On the first control run, 15 of 280 traces scored zero, and the scorer labelled
every one as the model being wrong. Read one at a time, all 15 were cases where
the model's answer was defensible and the ground truth was not. A later probe
added six more that went the same way: 21 of 21.

A sharper version turned up in the controlled study. The 1.7B model reads
`/think` as a switch for its own reasoning mode, and wrote it back out after
its answer, as `ANSWER: monitor /think`. The scorer matched the text after
`ANSWER:` against the permitted options and refused each one as an option not
on the menu. Across the five arms, 87 of 3,640 readings carried the token, and
84 of the 87 named the correct answer. The two non-null results the study's
first write-up reported were made entirely of those refusals.

The check that found it prints the answer line of every refused row. It takes a
minute and now runs before any number from a run is read.

## The one controlled study, and the test that could not have rejected

One run here asks whether the skill helps rather than whether it fires: 4,368
calls on a 1.7B model at temperature 0, five arms over the same 728 items. No
document, the shipped skill, a placebo document, and the winners of two
automated skill-evolution engines, each on a matched budget.

The placebo arm is what makes that design worth describing: a real document
matched to the skill on word count within 15% and on structure, carrying none
of its content. Comparing a skill against no document at all measures the
presence of text.

No arm rejected on either item set. The best showing was one engine's winner at
+0.041 on the trained-template items, raw p 0.034, which becomes 0.102 after
Holm's correction for the three comparisons registered as one family. The other
engine's winner scored 0.6280 on the held-out items, meaning items from
templates it had never trained on, against 0.6845 for an empty prompt: the
widest shortfall against an empty prompt in the study. An A/A control, the
placebo scored against itself, returned 728 of 728 items identical, which
bounds venue noise without removing it.

Both winners had memorised. One carries a rules table asserting renewal at 61%
utilisation and headroom at 37%, worked through on 2818 and 2032; the other
carries 63% and 213/300. Those come from single training items, and the corpus
draws that utilisation floor per item from a range and states it in every
prompt, so an arm carrying 61% contradicts its own prompt on nearly every item.

The arithmetic is the worse finding. Items come from templates, and two items
from one template are not independent of each other, so the template is the
unit that actually varies. Statisticians call that a cluster. The held-out half
of the design was drawn from three templates, and a one-sided sign test over
three clusters cannot return a p below 2 to the power of minus 3, or 0.125, so
those three primary comparisons could not have rejected at any outcome. The smallest true effect the design could have detected was 0.0807
and 0.0748 assuming items were independent; at the clustering the project's own
protocol specifies it is 0.1137 and 0.1054, about 2.6 times the largest gain
the study observed.

Every one of those quantities was computable before the first call. All of them
were computed after.

## Where these numbers apply

The blind readings that closed those venues all ran on one model, Sonnet,
through isolated single-shot calls that carry no checkpoint and nothing for the
scorecard. The trigger runs ran on one cheap hosted model, Haiku, across four
answer-key versions the harness refuses to compare against each other. The
controlled study ran on a 1.7B local model in a development arena, the run tier
the harness refuses to draw a verdict from.

Nothing above clears this project's own bar. A verdict requires beating a
control at q below 0.10 with a placebo, replicated on a freshly generated
holdout that regenerates from a seed kept outside the repository and is
published only after the verdict. That arena has never run and the holdout does
not exist yet. The scorecard is empty because the instruments kept finding
their own defects first.

A re-run of the controlled study is under way, with the winners' bodies
committed this time and more held-out templates. Its results are not in, and
nothing here predicts them.

Nothing here tests volume, long context, delegation, or work carried across a
conversation. The generalisation the record supports is narrow: a scenario
compact enough for one prompt and answerable in one call is not, for a current
model, hard.

## Two things worth copying

**Run a placebo arm.** Both engine winners had a training history and the
placebo had none, so where the placebo itself moved between the two item sets
it showed that "held out" and "different scenarios" were confounded in the
design, from inside it. An empty-prompt control cannot produce that diagnostic.

**Do the arithmetic before the first call.** The sign-test floor of 2 to the
power of minus k for k clusters. The smallest detectable effect at the
clustering you actually have, not the one that makes the study look powered.
The per-item ceiling read off the control arm, computed from the items about to
run. And one written sentence naming what will be computed, from which records,
over which denominator, by which function. If that sentence cannot be written,
the run is not ready.

None of this is advice here any more. Twenty runs are published with their raw
transcripts, and a new one cannot land unless the first commit of its prediction
is an ancestor of the run's own. The check that gates every change turns red on
an answer key holding an item no blind panel of three has read. And a
confirmation run will refuse to start unless its pre-registration matches both
the skill body and the analysis script by hash, the lock most registered work
leaves open: a registered metric means nothing if the code that computes it can
be rewritten after the data.
