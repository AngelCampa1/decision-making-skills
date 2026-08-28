# 2026-08-27 — The verdict tier is reachable, and the corpus is not hard enough for it

The five-arm study runs on `ollama/qwen3:1.7b`. `arenas.py` registers `ollama`
as `dev`, and a `dev` run emits no verdict however well controlled it is. NVIDIA
Build is registered `screen`, which does carry one. So the obvious question:
move the study there, or add a second target that carries the claim.

The plan had this as a parenthetical, "budget permitting". It should have been
settled before the registration rather than after the run started.

The answer is no, and the reason is headroom rather than the venue.

## What the key can actually call

The catalogue at `/v1/models` lists 84 models. This account can call **15** of
them. Every small instruct model returns 404 `Not found for account`:
`mistralai/mistral-7b-instruct-v0.3`, `google/gemma-3-4b-it`,
`nvidia/mistral-nemo-minitron-8b-8k-instruct`, and the rest of that size class.

A catalogue listing is not an entitlement. That belongs next to the existing
note in `evolution/venues.py` that NVIDIA Build offers no model card and so no
isolation receipt: two things this venue will tell you that are not true of it.

## The screen

Four reachable models under a registered `nvbuild/` prefix, 30 items from the
three held-out templates at validation seed 1000, arm `off`, no skill at all.
About 150 calls, notional cost $0.

| model | returned | correct | no-skill accuracy |
| --- | --- | --- | --- |
| `openai/gpt-oss-20b` | 30 | 30 | 1.000 |
| `meta/muse-glimmer-30b` | 30 | 30 | 1.000 |
| `nvidia/nemotron-3-nano-30b-a3b` | 30 | 29 | 0.967 |
| `google/diffusiongemma-26b-a4b-it` | 10 | 10 | 1.000 |

`diffusiongemma` first read 25/30. That number was wrong in the direction that
would have mattered: the five missing calls were 429s and empty-content
responses, and counting an API failure as a wrong answer makes a ceilinged model
look like it has room. Re-run with retries it returns 10 of 30 under the rate
limit and gets all ten right.

## What it means

**Every model this key can reach solves the corpus with an empty prompt.** The
items are two-option comparisons calibrated for a 1.7B model, where `off` scores
0.702 over the study's 728 items. A 26B model finds them free.

A five-arm study on any of these would spend 4,368 calls failing to reject,
because no arm can beat a control that is already perfect. The same fact kills
the transfer question: asking whether an evolved skill still helps on a model it
was not evolved against needs a model with something left to gain.

So the local study stands as the study, and its ceiling on what it may claim is
now measured rather than assumed. It is scoped to one 1.7B model and it emits no
verdict. That is a real limit and it goes in the results.

`openai/gpt-oss-20b` was screened for the ceiling and is disqualified as a target
regardless: it is the reflector that wrote both winners, and scoring a skill on
the model that authored it is not a transfer test.

## What would change the answer

A harder corpus, not a different venue. The generators already carry the knobs:
more distractors, more collision, more steps between the facts and the
comparison. Recalibrating the corpus so a mid-size model sits near 0.7 would put
the whole study in `screen` and let it carry a verdict.

That is a corpus change, which is a governed path and a fresh answer key, and it
is not a thing to start while a registered run is mid-flight. Recording it as
the next move rather than doing it now.
