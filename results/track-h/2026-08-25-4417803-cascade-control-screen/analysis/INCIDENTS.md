# Every failed call, every anomaly, and what was done about it

**Audience:** whoever audits this run's denominators.

## 1. Zero failed model calls

No `attempts*.jsonl` file exists for any item. Across every call in this run —
C01 40 readings, C02 40, C03 40, plus 360 judge calls — there were zero CLI
errors, zero rate limits, zero timeouts, zero retries, and zero isolation-receipt
violations. `attempts_before_this` is 0 on every record.

## 2. Two C03 runners raced, and 18 readings were sampled twice

**What happened.** `chain.sh` was launched in the background, produced no output
file, and appeared not to have started. A second C03 runner was started
directly. Both were alive and both appended to `readings-C03.jsonl`. The file
reached 47 records over 29 distinct reading ids before it was noticed.

**What was done.** Both runners were stopped. `dedupe_c03.py` deduplicated the
file under a rule stated in that file's docstring before it touched anything:
**keep the earliest record per reading id by its `at` timestamp** — not the
longer one, not the one that scores better, not the last writer. The 18
discarded records were parked in `readings-C03-duplicates.jsonl` rather than
deleted. The run was then resumed; the runner's resume key is the reading id, so
it filled only the missing ones.

**What it bought.** 18 identical prompts have two independent samples, which is
a free test-retest measurement of the primary. **17 of 18 agree; 1 disagrees**
(`ac33a96797a84a2c`, foreclosing, `miss` on one sample and `hit` on the other).
So roughly one reading in eighteen flips its verdict on a resample of the same
prompt, which is the reading-level sampling variance the interval over readings
is trying to express. That reading is also one of the two C03 accepts-list
failures in §5 below.

**What it does not excuse.** Nothing in the harness prevented two writers on one
append-only record. The resume key made the damage recoverable and the
timestamps made the rule applicable, but neither was a guard. A file lock, or a
runner that refuses to start when another holds the plan, is the missing piece.

## 3. A false alarm I raised and then withdrew

An intermediate check appeared to show `cascade_battery.py` producing seven
different md5s across four hash seeds, which would have meant the version 4
seed-independence repair had failed. **It had not.** The check globbed
`/tmp/b*.txt` and picked up unrelated files from other sessions. Re-run into a
clean directory, the battery exits 0 under `PYTHONHASHSEED` 0, 1, 42 and 99, all
four outputs are byte-identical to each other and to the published
`battery-output.txt`, md5 `0c2404dec6516ee839e63fa3da8fd14c`, and `diff` is
empty. Recorded because a withdrawn alarm that leaves no trace is how a real one
gets dismissed later.

## 4. The C02 and C03 answer keys were changed after their readings were seen

`still_can_exclusions` was absent from both. It is added by `patch_keys.py` from
a derivation rule stated in `../new-items/exclusions.json`, and every string
traces to a key field authored before any reply existed. Backups of all four
pre-change files are in `keybak-C0*.yaml`.

**This is not a blind key and the write-up says so.** The exclusion set fires
only inside `STILL CAN`, and in both items the control arm's `CANNOT` never
names the target, so a veto can only ever remove a treatment hit. Adding
exclusions is therefore **one-directional**: it can raise sensitivity, cannot
raise the false-alarm rate, and can only push J up. Numbers under the fixed key
are scorer diagnostics.

What is blind is the three-judge adjudication. The judges were asked what a
reply says about the target and never saw a key, so the same verdicts arbitrate
every key version rather than being arbitrated by one. Re-resolving C02 under
the fixed key needed **zero new judge calls**.

## 5. Two scorer defects that no registered threshold can see

**`chain_accepts` and `EXTRA_ENGAGEMENT` are module globals, not `Rules`
fields.** `score_response` reads them off the module, so C02 and C03 have their
engagement scanned against C01's vocabulary — the pneumatic hammer, the Craft
Trades Board, the 2027 round dates — plus their own accepts. Engagement for
those two items therefore collapses onto the accepts list itself, which makes
`misses_engaged` structurally near-zero and **renders threshold 2
(`accepts_list_gap`) inert for every item except C01**. C02 and C03 engagement
figures and `misses_engaged` are not comparable to C01's.

This is §5 of the v3 note recurring verbatim: a scoring choice that cannot be
expressed as a configuration cannot be falsified. Container precedence was
promoted to a `Rules` field for exactly this reason; these two were not.

**C03's two treatment misses are accepts-list failures, not model failures.**
`File a valid application to the Ashcombe Design Registry for Tidewrack` and
`File a registration for Tidewrack at the Ashcombe Design Registry` are both
correct and both score `miss`, because the accepts are contiguous phrases
(`application for tidewrack`, `tidewrack registration`) and the intervening
words break the match. Both have `engaged = False` for the reason above, so the
threshold designed to size this gap cannot count them.

Both misses land in the **negative** cell, which the registered adjudication does
not read.
