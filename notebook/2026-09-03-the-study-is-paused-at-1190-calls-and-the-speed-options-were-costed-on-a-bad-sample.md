# 2026-09-03 — The study is paused at 1,190 calls, and the speed options were costed on a bad sample

The re-run registered on
[2026-09-02](2026-09-02-prediction-the-five-arm-study-run-again-with-the-bodies-kept.md)
is collecting, at the registered configuration, and is paused pending one
decision by the maintainer: whether to spend part of the design to finish
sooner. Nothing is discarded. Nothing in the registration has moved since the
[cap amendment and its retraction](2026-09-02-prediction-the-five-arm-study-run-again-with-the-bodies-kept.md).

## The state

1,190 calls into 14,700, about 8%, in
`results/evolution/2026-09-03-514dd6c-study-seven-unseen-v2/`. That directory
is **untracked and on disk only**: it is a live checkpoint, not a published
run, and it is what a resume reads. `RESUMABLE_CAPS` refuses a resume that
changes anything but a raised cap, so it can only be resumed at the
configuration below, and any other choice starts from zero.

The exact command, which lived in `/tmp` and belongs here instead:

```bash
cd .claude/worktrees/evolution-rerun
caffeinate -dims uv run de study \
  --target ollama/qwen3:1.7b \
  --templates-root datasets/templates,datasets/templates-hard \
  --only-templates hrd-001-warranty-claim,hrd-002-shipping-escalation,hrd-003-deposit-notice,hrd-005-customs-clearance,hrd-006-appeal-window,hrd-008-deposit-notice-costed,rel-001-vendor-outage,rel-002-deploy-window,rel-003-oncall-escalate,rel-006-refund-request,rel-005-security-patch,rel-007-capacity-scale,rel-008-contract-renew,rel-010-loan-review \
  --holdout-ids hrd-003-deposit-notice,hrd-005-customs-clearance,hrd-008-deposit-notice-costed,rel-001-vendor-outage,rel-002-deploy-window,rel-005-security-patch,rel-008-contract-renew \
  --passphrase evolution-study-v2 --unseen-seeds 3 --seen-seeds 2 \
  --winner gepa=results/evolution/2026-09-02-4dcd13f-gepa-seven-template-v2/winner.md \
  --winner skillopt=results/evolution/2026-09-02-44d2feb-skillopt-seven-template-v2/winner.md \
  --winner-placebo gepa=datasets/placebos/placebo-gepa.md \
  --winner-placebo skillopt=datasets/placebos/placebo-skillopt.md \
  --passes 2 --chunk 8 --num-ctx 16384 --max-tokens 4096 \
  --max-calls 16000 --max-seconds 604800 \
  --slug seven-unseen-v2 --out results/evolution/2026-09-03-514dd6c-study-seven-unseen-v2
```

Wrap it in a loop that restarts on a non-zero exit and runs
`brew services start ollama` when `/api/version` does not answer. The run died
once at 40 minutes taking Ollama with it, and nothing restarted either.
**Do not commit in that worktree while it runs**: before `--out` existed, a
commit changed the directory name mid-run and orphaned 71 calls.

## The speed options were costed on a bad sample, and the numbers are wrong

The first estimate of this run, and the menu of ways to shorten it, came off
the first 83 calls. Those 83 are all `hrd-003-deposit-notice`, the item-major
order's first template and the one the screen read at 0.714 with a parse rate
of 0.857 — the hardest and the most verbose in the corpus. Over 1,190 calls
spanning several templates:

| arm | n | mean s | truncated | share of model time |
| --- | --- | --- | --- | --- |
| `on` | 174 | 19.9 | 14.4% | 19.0% |
| `placebo-skillopt` | 168 | 17.7 | 10.7% | 16.4% |
| `gepa` | 168 | 15.2 | 8.3% | 14.1% |
| `skillopt` | 168 | 14.6 | 5.4% | 13.5% |
| `placebo` | 168 | 14.0 | 5.4% | 13.0% |
| `off` | 176 | 12.6 | 7.4% | 12.2% |
| `placebo-gepa` | 168 | 12.8 | 4.2% | 11.9% |

Three things the 83 got wrong:

- **15.3 seconds a call, not 24.** The run projects to **62 hours**, not 98.
- **8.0% of calls truncate, not 20%.** Still arm-dependent — `on` is 14.4%
  against `placebo-gepa`'s 4.2%, a spread worth reporting — but not the
  dominant failure the small sample suggested. Truncated calls are 95 of
  1,190 and 37% of model time at 70 seconds each.
- **The longest reply that ends on its own is 3,252 tokens.** A cap of 2,048
  was the headline saving in the costing, and it would cut genuine answers.
  It is off the table. Any cap that clears 3,252 with margin saves little,
  because it does not shorten the runaways by much.

So the honest menu is shorter than the one it replaces. At 62 hours as
registered: one pass instead of two is about 31, concurrency 2 is about 31,
and both together about 16. Only the first two are decisions about this study;
the third overrides `CONCURRENCY_UNSAFE`, whose own falsification found
concurrent and serial agreeing on the exact text of 0 of 40 items — and two
serial runs agreeing on 0 and 7 of 40, with nothing separating the arms on the
parsed answer, which is the object this study scores.

Nothing is decided here and nothing has been amended. The registration stands
as written, the checkpoint holds 1,190 calls made under it, and the decision
is the maintainer's.

## Why this entry exists

An estimate from 83 calls of one template was presented as a costing of the
whole run, with a recommended option attached. It was wrong by a third on
wall clock and it recommended a cap that would have corrupted answers. The
record of that is worth more than the correction: a rate read off the first
chunk of an item-major run is a rate for that chunk, and this run orders its
items so that the first chunk is one template by construction.
