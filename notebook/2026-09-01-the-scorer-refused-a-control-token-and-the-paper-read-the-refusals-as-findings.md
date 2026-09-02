# The scorer refused a control token, and the paper read the refusals as findings

**2026-09-01.** An assessment of what this repository had produced, run as
three inventories and two adversarial reviews over the whole tree, came back
with three defects in the paper. Checking the first against the raw records
turned it into a fourth, larger than the other three, and this entry records
all four and what changed.

## What the reviewer found

The seen-set claim that "the placebo is not inert", which sat in the abstract
and in contribution 1, decomposed to one template. Placebo over `off` on the
seen set is 44 wins to 24; `rel-003-oncall-escalate` alone is 23 to 0 and the
other six templates sum to −3. Every one of the 23 was an `off` answer with
`parse_status: unlisted_option`. The template-level sign-flip over the seven
seen templates gives p = 0.344. The reviewer read this as "any text in the
system prompt stops one template's off-menu answers" and stopped there.

## What the records say

The 23 answers are `ANSWER: monitor /think`, and the key for all 23 is
`monitor`. Qwen3 reads `/think` and `/no_think` as a switch for its thinking
mode, and the model wrote the switch back after its answer. The scorer matches
the text after `ANSWER:` against the option list after stripping punctuation
and markup, `/think` is neither, and the answer was refused as an option not
on the menu. Over the whole study:

| arm | answers carrying the token | of which the key's option |
|---|---|---|
| `gepa` | 56 | 54 |
| `off` | 29 | 29 |
| `on` | 1 | 1 |
| `skillopt` | 1 | 0 |
| `placebo` | 0 | 0 |

Eighty-seven of 3,640 readings, 84 naming the key. By the harness's own
vocabulary (`ZeroCause` in `scorers/answer.py`) that is a `verifier_defect`,
and the rule that every zero is classified before it is believed was applied
to the first control run on 2026-08-10 and not to this one. The 41 GEPA
refusals on `rel-001-vendor-outage` are the "parse failure selective on the
answer key" the paper reported: 39 of them are the model answering `wait`,
which the key wanted, with the token after it.

## What it moves

Re-read with the token stripped, from the same records:

| set | arm | as scored | re-read | vs placebo, re-read |
|---|---|---|---|---|
| unseen | `off` | 0.6845 | 0.7024 | |
| unseen | `gepa` | 0.6280 | 0.7440 | 59/40, p = 0.0350, Holm q = 0.1049, clustered 0.2500 |
| seen | `off` | 0.7168 | 0.7755 | |
| seen | `gepa` | 0.7730 | 0.8112 | 37/20, p = 0.0166, Holm q = 0.0497, clustered 0.0469 |

`placebo` over `off` on the seen set goes from 44/24, p = 0.010, to 21/24.
`on`, `placebo` and `skillopt` do not move. The three low-signal templates are
the same three. So: the two non-null readings the paper carried, the placebo
above an empty prompt and GEPA's winner below one, were both the scorer. And
the arm the registered figures placed last on the unseen set is, under the
re-read, the arm nearest to clearing the placebo on the seen set, at a Holm
q that crosses 0.05 at the item unit and does not at the template unit.

## What changed, and what did not

The registered primary is unchanged. `analysis.json`, the run README's
tables and every `\acc`, `\p`, `\q` and `\clustered` macro read exactly what
they read yesterday. `de figures` now also emits a `\rescored...` family and a
`\controlToken...` family from the same records, and the paper reports the
re-read beside the registered figures in a subsection that says why it is
not promoted: it is a scoring rule chosen after the data, on the arm it helps
most.

`scorers/answer.py` strips a trailing `/think` or `/no_think` from the answer
line from today, with the reasoning in a comment above the pattern and tests
beside it. A committed record's `correct` is what the scorer read at the
time, and nothing re-scores it; `figures.load_readings` re-reads the response
text for the comparison and that is the only place the re-read exists.

The abstract, introduction, contributions, results, discussion and
limitations were rewritten around this. The paper now also scores its six
registered predictions in the text (two missed, one unanswerable), which no
earlier version did.

## The other three defects, briefly

**"GEPA accepted its winner on three items" is most likely our logging.**
`evolution/adapter.py` writes a candidate to the lineage once, with the first
score it received, and GEPA scores a new candidate first on a three-item
reflection minibatch. `winner.json` falls back to that lineage score when the
engine chose. GEPA's documented return rule evaluates on the validation pool.
The records that would settle it are in the gitignored directory. The paper
now says this.

**The "mid-run amendment" is commit-dated after the run.** Prediction
committed 14:20 (`e882eff`), run at 15:03 (`53b4965`), amendment at 22:29
(`03f4df8`) in the same commit as the results write-up. The amendment
explains the failure of prediction 4. The method section now gives the commit
times, and the prediction is scored as written.

**The prediction scoring was in the notebook and not in the paper.** Now in
both.

## The lesson, which is an old one here

`docs/FAILURE_TAXONOMY.md` records that fifteen of fifteen zeros on the first
control run were item defects, and `AUTONOMOUS_WORK_ORDER.md` rule 3 says a
failure is adjudicated blind before it is believed. The five-arm study reported
87 zeros as the model's and built three paragraphs and an abstract sentence on
where they fell, and fourteen truth cycles read those paragraphs without once
opening a refused response. The check that found it was a script over the
records that printed the answer line of every `unlisted_option` row, which
took a minute. It is now the seventh item in the paper's list of checks.
