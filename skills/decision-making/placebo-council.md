---
matched_to: council.md
purpose: >
  The control arm for council.md. Matched on the three dimensions
  check_placebo_match measures, and matched in form: an opening case, an
  abort list, three worked sections and a fenced output block, so the on arm
  and the placebo arm arrive carrying the same amount of instruction and the
  same amount of requested structure.
plausible_because: >
  Every line is true and usable. It is about the manner of a written reply,
  and a model that follows it writes a better-mannered answer than one that
  ignores it, which is what keeps a model engaging with it rather than
  skimming it as filler.
empty_because: >
  Nothing in it operates on the decision. It never names the positions, never
  argues one, never puts two of them against each other, never says which
  survives and never says what to do when they tie. A model that follows
  every line still has to reach the answer by whatever it would have done
  unaided.
content_review: >
  Checked line by line against four constructs the structural guard cannot
  see, and clean on all four. Council's own mechanism, meaning naming
  positions, arguing each at its strongest, cross-examining them and
  reporting which survives or that neither did. Order effects, meaning any
  instruction to read fully, to read in a particular order, to enumerate
  before choosing or to hold judgement while reading. Layout deixis, meaning
  any reference to where an option sits, including letter or ordinal labels.
  Calibration, meaning any instruction to state or examine how sure the
  answer is. The existing placebo.md fails the first two and is documented
  in docs/DECISIONS.md as a separate finding; this file deliberately does
  not inherit its content strategy.
declared_in: pyproject.toml, tool.decision-evals.placebos
delivered: >
  This frontmatter is stripped before the body reaches a model. Load it with
  decision_evals.skills.delivered_body, which is what the match guard counts.
---

# Writing back to someone

A person has put a decision in front of you and is waiting for a reply. They
have lived with this thing for a while, and what reaches you is the tidied
version of something messier. The reply is a piece of writing addressed to
them, and they can tell the difference between one written to them and one
written near them.

## Leave it alone if

- They wanted a fact and would rather have the fact than a discussion of it.
- They are talking to themselves out loud and have not asked you for anything.
- The exchange is light, and a considered reply would land as heavy.

## Who is on the other end

Write to the person who wrote to you. Their situation is theirs, not a case,
and a reply pitched at a general audience will read to them as though it was
meant for somebody else.

They gave you particulars, so use them. A reply that could have been sent to
anybody tells them you were not really here for this one, and the particulars
are the cheapest way to show that you were.

Do not perform sympathy. If the thing is hard, say the thing; warmth arrives in
how plainly you speak, not in an announcement that you understand.

## The pitch of it

Match their level, not their agitation. Someone writing at speed under strain
still wants a reply that is steady, and answering in kind hands them one more
agitated voice where they wanted a calm one.

Say the thing you mean without a preamble that announces it. Openings that
warm up cost the reader attention they were going to spend on the answer.

## The words themselves

Use their vocabulary. A term of art earns its place only where the ordinary
word would be less exact, and where you do reach for one, use it once and
plainly.

Short beats long. A reply that covers every angle asks them to find the answer
inside it, which is work you were supposed to do.

## Output

```
WHAT THEY ASKED
  <the question, in the words they used>

WHAT YOU UNDERSTOOD
  <the situation as you now hold it>

WHAT YOU SAY
  <your reply to them>

HOW YOU LEAVE IT
  <the line you want them to keep>
```

Finish on the line they will still be holding tomorrow morning.
