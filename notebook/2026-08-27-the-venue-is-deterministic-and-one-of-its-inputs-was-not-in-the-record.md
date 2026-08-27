# 2026-08-27 — The venue is deterministic, and one of its inputs was not in the record

Earlier today I wrote that this venue is not deterministic at temperature zero,
after the same skill body scored anywhere from 15 to 19 of 21 across a day. That
[entry](2026-08-27-one-skill-four-numbers-and-only-one-of-them-was-the-skills.md)
already retracted one explanation. It needs a second retraction, and this time
the replacement is a measurement rather than a hypothesis.

**The venue is deterministic. It has an input nobody was recording.**

## The design

Twelve passes of the seed body over the same 21 validation items, alternating
two conditions:

- **warm** — the pass immediately after the previous one, model resident
  throughout
- **reload** — the model evicted (`keep_alive: 0`) and loaded again before the
  pass

Target `ollama/qwen3:1.7b` at a 16,384-token window through Ollama's native
surface, output capped at 4,096, temperature zero, one process, nothing else
running. 252 calls, notional cost $0.

## The result

Every pass after the first scored **18 of 21**, in about 117 seconds, warm and
reloaded alike. A flat line. And underneath the flat line:

```
rel-002-deploy-window#v0-d1-early    [0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
rel-005-security-patch#v0-d4-early   [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
                                      ^warm ^reload alternating
```

**Two items in perfect antiphase, for eleven consecutive passes.** `rel-002` is
correct when the model is warm and wrong when it has just been loaded.
`rel-005` is the exact opposite. Neither ever broke the pattern.

Everything else held still: **19 of the 21 items returned the same answer on
every one of the eleven passes.**

Under a null where each item is a coin flip, one item tracking its condition
eleven times running is p ≈ 0.0005, and two of them independently is beyond
anything this corpus can resolve. This is not a rate. It is a switch.

## What that means about every number measured here today

The seed body scored 15, 15, 17, 17, 17, 18, 19, 19, 19, 19 of 21 across the
day, and I called it four items of run-to-run noise. It is not noise. It is a
**state variable that was never in the record**: whether the model had been
freshly loaded when each item was asked.

Which closes the loop on why searches and standalone passes disagreed so badly:

- **Standalone**, calls are back to back. Ollama's `keep_alive` defaults to five
  minutes and nothing gets close to it, so the model stays resident and every
  pass is taken in one state. Ten passes gave 18, 19, 19, 19, 19, 19, 19, 19,
  19, 19 — one item's worth of movement, on the first pass.
- **Inside a search**, every validation pass is followed by a reflector call to
  a hosted endpoint that takes minutes. The five-minute residency expires, the
  model is evicted, the next pass reloads it. A search therefore samples *both*
  states, in an order nobody chose and nothing recorded.

Two engines were compared on a matched budget under a variable neither of them
controlled and neither run recorded.

## The retraction this forces

**"This venue is not deterministic, serially, at temperature zero" is wrong.**
It is deterministic. Nineteen of twenty-one items are bit-identical across
eleven passes spanning six evictions. What varies is a physical property of the
server — some difference in how the weights or the cache land in memory after a
load — and it decides borderline items the same way every time.

That is a better situation than noise, because a state variable can be pinned
and noise cannot.

## And the context-window claim does not survive either

Two commits ago I wrote that the unreadable answers in both matched runs were
generations that filled a 4,096-token window and pushed their own question out
of it. The correlational evidence was real: of 478 readable answers, **not one
ever exceeded 4,096 prompt-plus-output tokens**, and every long unreadable one
was past it.

The controlled test does not support the cause. At a **16,384**-token window —
four times the room — this probe produced **zero** unreadable answers in 231
calls after the first pass. The same body at a 4,096 window produced zero in 210
standalone calls. Widening the window changed nothing, and neither window
reproduces the failure.

So: the runaways are real, they happened inside searches and not outside them,
and **the window is not why**. The one pass that did produce them, pass 0, was
also the only pass overlapping other work on this machine — the repository's own
test suite was running — and it took 205 seconds against a steady 117. That is
one observation and a hypothesis, not a finding, and it is written here as one.

**The guard added for the wrong reason stays**, because it is right for a
different one: sending `max_tokens: 8192` at a model loaded with a 4,096-token
window asks for an answer the request has arranged not to be able to hold. That
is incoherent whether or not it caused this. The docstrings that assert it *did*
cause this are being corrected.

## What Phase 3 does with this

1. **Pin residency.** Every target call in the study sends a `keep_alive` long
   enough to span the reflector, so a run is taken in one state rather than
   sampling two. Cheap, and it removes the largest single source of movement
   measured here.
2. **Record the state anyway.** Pinning is a claim about the server, and a run
   that records residency can check the claim rather than assert it.
3. **Discard or account for the first pass after a load.** It differed in both
   experiments run today: 18 against a steady 19 in one, 15 with four unreadable
   answers against a steady 18 in the other.
4. **Do not size repeats from a flip rate.** There is no flip rate. There are
   two items that answer to a switch, and the fix is the switch, not more
   samples. Repeats stay in the design as a check that the switch is pinned —
   if 19 of 21 items are no longer constant across repeats, something else is
   loose.
