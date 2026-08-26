# 2026-08-26 — The two engines install, and one of them needs an attribute the protocol calls optional

Phase 0 of the evolution study: get the venue and both engines standing up
before any of the harness is touched. Two things worth recording, one of them a
defect that would have cost a day inside Phase 1.

## What is pinned

| Package | Version | Licence | Role |
| --- | --- | --- | --- |
| `gepa` | 0.1.4 | MIT | Engine under test |
| `skillopt` | 0.2.0 | MIT | Engine under test |

Both from PyPI, both pointing at their published repositories
(`gepa-ai/gepa`, `microsoft/SkillOpt`). `evoskill` is not on PyPI and is
deferred. They live in a `[dependency-groups] evolve` that `de check` never
installs, because they are the *subject* of the study and must not become a
dependency of the instrument.

## The venue

`qwen3:4b` on the RTX 5060 Laptop, 8 GB, driver 592.82. Ollama 0.32.14, the
standalone zip from the 2026-08-19 dev-arena run, still on disk with its model
store. `preflight` returned ready, the card read `system=0 chars,
template=1506 chars`, `assert_isolated` passed, and a first call answered `4` in
2028 ms for 32 in / 146 out at zero cost.

**The install is in a scratch directory belonging to a session that has ended.**
It works and nothing was re-downloaded, and it is not a durable arrangement: the
next machine, or a cleared temp, and the fast loop has no venue. Recorded here
because a run that cannot be restarted is a run that cannot be reproduced.

## The defect: `propose_new_texts`

`GEPAAdapter` documents three required responsibilities and lists
`propose_new_texts` under "Optional instruction proposal", with a default
implementation supplied by the engine. An adapter that omits it is what the
protocol describes.

An adapter that omits it does not work. `reflective_mutation.py:176` reads

```python
self.adapter.propose_new_texts is not None
```

with no `getattr` default, so every proposal raises `AttributeError`, the engine
catches it, retries per task, fails again, and reports

```
Iteration 8: Reflective mutation did not propose a new candidate
```

The run completes. It exits zero. It reports a best score, and the best
candidate is the seed, because nothing ever mutated. **A run that explored one
candidate and a run whose search failed entirely are the same output**, and the
only signal is a warning in a stream that a checkpointed run would not be
watching.

The fix is one line — `propose_new_texts = None` as a class attribute — and the
reason it is here rather than in a commit message is that the failure mode
generalises. The whole study rests on comparing engines by the artefacts they
produce, and this is an engine reporting a completed search that never
searched. Whatever the adapter ends up looking like in Phase 1, something has to
assert that the number of candidates explored exceeded one before any score from
it is read.

## The smoke, once it was fixed

Four prime-or-not items, seed instruction "Answer the question.", 24 metric
calls, reflection LM the same local `qwen3:4b`:

```
best score: 1.0        (from 0.75)
candidates explored: 3
best candidate: "Given a question string about whether a number is prime
  (e.g., 'Is 17 prime?'), output 'Y' if the number is prime, 'N' otherwise. The
  output must be a single line containing only the letter 'Y' or 'N' with no
  extra characters, spaces, newlines, or formatting."
```

So the integration path Phase 1 depends on is real: GEPA drives
`providers/openai_compatible.py` as both task model and reflection LM, the loop
closes, and it costs nothing. Note what the engine actually fixed — the
*format contract*, not the reasoning. The seed lost points to replies whose last
line was not a bare letter. That is worth remembering when the real corpus runs,
because `solvers/arms.py` already puts a `FORMAT_CONTRACT` in every arm, and an
engine that can only win by restating it would show a gain that says nothing
about decision quality.

## What `optimize()` gives us for free

Reading the installed signature rather than the paper:

- `max_metric_calls` is a call budget, which is the budget unit this repository
  now needs on a venue where dollars read zero.
- `acceptance_criterion="strict_improvement"` is the default, and it is the same
  gate SkillOpt describes. Both engines therefore accept on an unrepeated
  comparison by construction, which is the thing the study exists to measure.
- `run_dir` persists frontier state, so a long run is resumable without the
  harness re-implementing it.
- `seed` is threaded through.

## Next

Phase 1: the `candidate` arm, `seed` and `candidate_sha` on `RunRecord`, the
call-and-wall-clock budget, and the `evolution/` package. No prediction is
registered yet; the first one is due before the Phase 2 runs, and it will have
to name the candidate-count check above as a validity condition rather than a
nicety.
