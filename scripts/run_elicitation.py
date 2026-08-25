"""Run a four-arm elicitation over an item corpus, checkpointed and resumable.

This is the runner :mod:`decision_evals.elicit` did not have. The module
computes the record, the exclusion table and the closed union; nothing called
any of it. ``run_elicitation`` had no caller anywhere in the repository, and a
runner nothing invokes is the same defect as a report nothing prints, one
layer up -- this closes both at once, because the second call this script
makes after every arm is :func:`~decision_evals.elicit.print_exclusion_report`.

**What this is not.** It knows nothing about ``council``, ``hinge`` or
``cascade``. The arms are :data:`~decision_evals.solvers.arms.ARM_NAMES`, read
off ``solvers/arms.py`` rather than named here, and the items are read off
disk in a corpus format this script defines and nothing else has opinions
about (see :func:`load_item_corpus`). Authoring an item corpus for a
particular instrument -- deciding what a ``council`` scenario says, or what a
``hinge`` triplet's governing fact is -- is a different job, upstream of this
one. This script is the part that was missing: given items and an arm, make
the calls, write the checkpoint, print the attrition.

## The corpus format

One JSON object per line, the same shape :class:`~decision_evals.elicit.ElicitationItem`
serialises to, so an authoring script can write it with ``dataclasses.asdict``
plus the two columns the item itself does not carry:

.. code-block:: text

    {"item_id": "council|s1|AB|r0", "construct": "council", "cluster_id": "s1",
     "condition_label": "AB", "repeat": 0, "ask_kind": "call",
     "ask": {"ordering": "AB", "first_course": "expand", "second_course": "hold",
             "block": "CALL"},
     "prompt": "...", "set_version": 1}

``ask_kind`` selects which of :data:`~decision_evals.elicit.ASK_TYPES` ``ask``
is built from -- the same discriminator the checkpoint itself uses, so a
corpus row and a written record are one format read two ways.

## What this runner guarantees, and why each one is here

**Checkpointed and resumable.** Every arm shares one checkpoint file; the
resume key is ``(item_id, arm)``, so a second invocation with the same
``--checkpoint`` fills in whatever the first one did not finish and re-issues
nothing. That is :func:`~decision_evals.elicit.run_elicitation`'s own
contract, inherited rather than reimplemented.

**A changed corpus cannot silently resume.** ``scripts/calibrate.py`` learned
this the hard way: a checkpoint keyed on item id resumes cleanly against a
*rewritten* item at the same id, and the run reports a number computed half on
one item and half on another with nothing anywhere raising an eyebrow.
:func:`assert_checkpoint_matches` hashes every item next to the checkpoint and
refuses a mismatch before the first call.

**Isolation is asserted per call, not assumed.** Every call goes through
:func:`~decision_evals.providers.claude_code.run_isolated`, which asserts the
CLI's own receipt before the result counts. A contaminated call answers
exactly like a clean one, so this is checked on every row rather than spot
sampled.

**Concurrency is recorded, not just used.** ``elicit.py``'s ``concurrency``
column is required with no default, and every row this script writes carries
the value that was actually in flight when it was produced.

**A failure is recorded with its kind and never retried into a different
denominator.** ``prompt_too_long`` and infrastructure failures are written as
their own ``call_status`` rather than silently retried until something parses;
an authentication failure or an isolation violation stops the run instead,
because retrying either would produce a few hundred identical rows or a
result from a venue the run does not license. All three behaviours are
``run_elicitation``'s, not this script's -- this file adds no retry logic of
its own.

**The budget is cumulative across arms, in one invocation.** ``BudgetLedger``
is frozen and ``run_elicitation`` returns records, not an updated ledger, so a
naive loop that passed the same ledger to all four arms would authorise the
budget once per arm instead of once per run. This script folds each arm's
produced cost into the ledger before the next arm starts, and seeds the
starting balance from whatever the checkpoint already holds -- so a resumed
run is not handed the budget again either.

**Two processes cannot write one checkpoint.** ``scripts/run_triggers.py`` --
the runner behind every trigger call on record -- has no such guard: its
``collect()`` appends to its checkpoint with no lock of any kind, and neither
does :func:`~decision_evals.runner.run_arm`, which every other script that
makes model calls goes through. That gap is real and this script does not
close it anywhere but here. It matters because on 2026-08-25 two runners
raced on one append-only records file in a 40-call screen and left 47 records
across 29 ids; it was recoverable only because the resume key happened to
make it so, which is a different thing from a guard. The run this script
drives is 1,320-3,784 calls resumed across quota windows, which is far more
exposure to the same race, so here it gets one: :class:`RunLock` holds an OS
advisory lock (``msvcrt`` on Windows, ``fcntl`` on POSIX) on a file beside the
checkpoint for the whole of ``main``'s write path. A second invocation against
the same checkpoint refuses immediately rather than interleaving with the
first -- see :class:`RunLockError`. Nothing here guesses whether the first
holder is still alive: the lock is tied to its open file handle, and the OS
releases that handle the moment the holding process exits, crash included, so
a dead holder never has to be told apart from a live one.

**A duplicate ``(item_id, arm)`` on disk has one resolution, stated instead
of improvised.** Before the lock existed, that race left exactly this shape
of duplicate, and the fix that day was applied by a human reading the file.
:func:`deduplicate` is that fix, written down: file order is completion
order, so the first row written for a key is the one this script counts, and
every row after it is appended whole to ``<checkpoint>.parked`` rather than
discarded. A rescoring dispute can still recover a parked row; nothing here
ever deletes one.

Usage::

    python scripts/run_elicitation.py --arena dev --model haiku \\
        --items path/to/corpus.jsonl --checkpoint results/.../run.jsonl \\
        --skill-body path/to/skill.md --placebo-body path/to/placebo.md \\
        --arms off,on,placebo,cot --budget 5.0
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import socket
import sys
import tempfile
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Final

from decision_evals.arenas import ArenaError, assert_model_allowed
from decision_evals.budget import BudgetLedger
from decision_evals.elicit import (
    ASK_TYPES,
    Ask,
    ElicitationItem,
    ElicitationRecord,
    IsolatedCallFn,
    load_elicitation,
    print_exclusion_report,
    run_elicitation,
)
from decision_evals.providers.claude_code import Elicited, IsolationError, run_isolated
from decision_evals.runner import RunError, preflight
from decision_evals.solvers.arms import ARM_NAMES, ArmError, ArmName, ArmPrompt, build_arm

REPO_ROOT = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------- #
# One writer at a time
# --------------------------------------------------------------------------- #

if sys.platform == "win32":
    import msvcrt

    def _try_lock(handle: int) -> bool:
        try:
            msvcrt.locking(handle, msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True

    def _unlock(handle: int) -> None:
        os.lseek(handle, 0, os.SEEK_SET)
        with contextlib.suppress(OSError):
            msvcrt.locking(handle, msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _try_lock(handle: int) -> bool:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return False
        return True

    def _unlock(handle: int) -> None:
        with contextlib.suppress(OSError):
            fcntl.flock(handle, fcntl.LOCK_UN)


class RunLockError(RuntimeError):
    """Another process already holds the lock beside this checkpoint."""


class RunLock:
    """An OS advisory lock beside one checkpoint, held for the write path.

    ``msvcrt.locking`` on Windows and ``fcntl.flock`` on POSIX are both tied
    to the open file handle, not to a pid or a timestamp this process has to
    trust. That is the property this needs: a second process opening the same
    lock path gets its own handle and the OS refuses it a lock the first
    handle already holds, and when the first handle's owner exits for any
    reason -- a clean return, an uncaught exception, a kill -9 -- the OS
    closes that handle and the lock goes with it. There is no stale state for
    this class to reason about, because staleness is not a state an OS
    advisory lock can be in.

    The file itself carries a pid, a hostname and a timestamp, written after
    the lock is acquired. Diagnostic only: a human reading a refusal wants to
    know who to ask about it, but nothing here parses that content back to
    decide whether the lock is held. The lock decides that.
    """

    def __init__(self, checkpoint: Path) -> None:
        self._path = checkpoint.with_name(checkpoint.name + ".lock")
        self._handle: int | None = None

    def __enter__(self) -> RunLock:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        handle = os.open(str(self._path), os.O_CREAT | os.O_RDWR)
        if not _try_lock(handle):
            os.close(handle)
            raise RunLockError(
                f"{self._path} is held by another process. Two runners writing one "
                "checkpoint is how 47 records across 29 ids happened on 2026-08-25; "
                "this run refuses rather than repeating it. If the holder already "
                "exited, its lock went with it -- this refusal means something is "
                "still running."
            )
        os.ftruncate(handle, 0)
        os.write(handle, f"pid={os.getpid()} host={socket.gethostname()}\n".encode())
        self._handle = handle
        return self

    def __exit__(self, *exc_info: object) -> None:
        if self._handle is not None:
            _unlock(self._handle)
            os.close(self._handle)
            self._handle = None


def deduplicate(records: list[ElicitationRecord], *, parked_path: Path) -> list[ElicitationRecord]:
    """Resolve a duplicate ``(item_id, arm)`` on disk, parking the rest.

    File order is completion order, so the first row written for a key is
    the one this run counts; every later row for the same key is a repeat of
    a call that was already recorded, not a second measurement. Nothing here
    decides that by looking at which row is "better" -- there is no such
    rule, which is exactly how a race in 2026-08-25 left this same shape of
    duplicate to a human's judgement instead of the program's.

    A parked row is appended to ``parked_path`` whole rather than dropped, so
    a rescoring dispute can still read exactly what was set aside instead of
    trusting that discarding it was safe.
    """
    kept: list[ElicitationRecord] = []
    seen: set[tuple[str, str]] = set()
    parked: list[ElicitationRecord] = []
    for record in records:
        key = (record.item_id, record.arm)
        if key in seen:
            parked.append(record)
            continue
        seen.add(key)
        kept.append(record)
    if parked:
        parked_path.parent.mkdir(parents=True, exist_ok=True)
        with parked_path.open("a", encoding="utf-8") as handle:
            for record in parked:
                handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
    return kept


def load_checkpoint(checkpoint: Path) -> list[ElicitationRecord]:
    """The checkpoint's records, deduplicated by :func:`deduplicate`.

    Every read this script does after the first call goes through here rather
    than through :func:`~decision_evals.elicit.load_elicitation` directly, so
    the exclusion report, the budget already spent and the corpus check all
    see the same resolved set of rows instead of three chances to disagree.
    """
    if not checkpoint.exists():
        return []
    records = load_elicitation(checkpoint)
    return deduplicate(records, parked_path=checkpoint.with_name(checkpoint.name + ".parked"))


#: ``ask_kind`` to the dataclass it builds, read off the closed union itself
#: rather than listed by hand -- a family added to :data:`~decision_evals.elicit.Ask`
#: is a family this dispatch already knows, because :data:`ASK_TYPES` is
#: ``get_args(Ask)``.
_ASK_BY_KIND: Final[dict[str, type[Ask]]] = {cls.kind: cls for cls in ASK_TYPES}


class ItemCorpusError(RuntimeError):
    """A corpus file could not be read as a sequence of elicitation items."""


def _build_ask(kind: object, payload: object) -> Ask:
    if not isinstance(kind, str) or kind not in _ASK_BY_KIND:
        raise ItemCorpusError(f"unknown ask_kind {kind!r}; expected one of {sorted(_ASK_BY_KIND)}")
    if not isinstance(payload, dict):
        raise ItemCorpusError(f"ask must be an object, got {payload!r}")
    try:
        return _ASK_BY_KIND[kind](**payload)
    except TypeError as exc:
        raise ItemCorpusError(f"ask of kind {kind!r} does not match its fields: {exc}") from exc


def load_item_corpus(path: Path) -> list[ElicitationItem]:
    """Read a corpus file into items, dispatching each row's ``ask`` by kind.

    Raises:
        ItemCorpusError: A line is not a JSON object, names an ``ask_kind``
            outside the closed union, or is missing a field
            :class:`~decision_evals.elicit.ElicitationItem` requires. Refused
            here rather than left for ``run_elicitation`` to discover mid-run,
            because a corpus defect found after the first call has already
            spent quota on a run that cannot be scored.
    """
    items: list[ElicitationItem] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ItemCorpusError(f"{path}:{line_number} is not valid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ItemCorpusError(f"{path}:{line_number} is not a JSON object")
        row = dict(row)
        ask = _build_ask(row.pop("ask_kind", None), row.pop("ask", None))
        try:
            item = ElicitationItem(ask=ask, **row)
        except TypeError as exc:
            raise ItemCorpusError(
                f"{path}:{line_number} does not match ElicitationItem: {exc}"
            ) from exc
        if item.item_id in seen_ids:
            raise ItemCorpusError(f"{path}:{line_number} repeats item_id {item.item_id!r}")
        seen_ids.add(item.item_id)
        items.append(item)
    if not items:
        raise ItemCorpusError(f"{path} contains no items")
    return items


def corpus_fingerprint(items: list[ElicitationItem]) -> str:
    """A hash of everything a call actually depends on.

    Item ids are coordinates -- construct, cluster, condition, repeat -- and
    stay identical when the content at those coordinates changes underneath
    them. Hashing ``prompt`` and the ask's own fields, not just the id, is what
    lets a resumed run notice that the corpus it is resuming into is not the
    one that produced the checkpoint on disk.
    """
    digest = hashlib.sha256()
    for item in sorted(items, key=lambda item: item.item_id):
        digest.update(item.item_id.encode())
        digest.update(item.ask.kind.encode())
        digest.update(json.dumps(asdict(item.ask), sort_keys=True).encode())
        digest.update(item.prompt.encode())
        digest.update(str(item.set_version).encode())
    return digest.hexdigest()


class CorpusMismatchError(RuntimeError):
    """The checkpoint on disk was produced from a different corpus."""


def assert_checkpoint_matches(checkpoint: Path, items: list[ElicitationItem]) -> None:
    """Refuse to resume a checkpoint that a different corpus produced.

    The sidecar's own existence is what is checked, not the checkpoint's --
    a run that stops before its first row lands (an authentication failure,
    say) leaves ``checkpoint`` absent but the corpus it was about to run
    already recorded, so a retry against a changed corpus is still caught
    instead of reading as a first run and overwriting the fingerprint.
    """
    sidecar = checkpoint.with_name(checkpoint.name + ".corpus")
    fingerprint = corpus_fingerprint(items)

    if not sidecar.exists():
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        sidecar.write_text(fingerprint, encoding="utf-8")
        return

    recorded = sidecar.read_text(encoding="utf-8").strip()
    if recorded != fingerprint:
        raise CorpusMismatchError(
            f"{checkpoint} was produced from a different corpus.\n"
            f"  recorded: {recorded[:16]}\n"
            f"  current:  {fingerprint[:16]}\n"
            "Resuming would score some records against one corpus and the rest "
            "against another. Move the checkpoint aside and start a fresh run."
        )


def make_call(model: str) -> IsolatedCallFn:
    """The isolated call this run makes, closed over the model it is measuring.

    ``run_isolated`` is what asserts the receipt; this wraps it to the three
    positional arguments :func:`~decision_evals.runner._call_with_backoff`
    calls a :data:`~decision_evals.elicit.IsolatedCallFn` with -- prompt, the
    arm's system prompt, and whether it is appended rather than replacing the
    CLI's own.

    Claude only. :class:`~decision_evals.providers.claude_code.Elicited` is
    typed to :class:`~decision_evals.providers.claude_code.InitReceipt`, the
    Claude backend's own receipt, and ``agy``'s :class:`AgyReceipt` is not
    that type -- widening ``Elicited`` to accept either is a change to
    ``elicit.py``, not to a runner that calls it, so this script does not make
    it. Antigravity support for this instrument family is unclaimed rather
    than silently unsupported.
    """

    def call(prompt: str, system_prompt: str, in_situ: bool) -> Elicited:
        return run_isolated(prompt, system_prompt=system_prompt, model=model, in_situ=in_situ)

    return call


def _parse_arms(raw: str) -> list[ArmName]:
    names = [name.strip() for name in raw.split(",") if name.strip()]
    unknown = [name for name in names if name not in ARM_NAMES]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown arm(s) {unknown}; choose from {list(ARM_NAMES)}")
    return names  # type: ignore[return-value]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="haiku")
    parser.add_argument(
        "--arena",
        required=True,
        choices=("dev", "screen", "confirm"),
        help="which arena this model is pinned to; refused if it is pinned elsewhere",
    )
    parser.add_argument(
        "--items", type=Path, required=True, help="path to a corpus file; see module docstring"
    )
    parser.add_argument(
        "--checkpoint", type=Path, required=True, help="JSONL file every arm appends to"
    )
    parser.add_argument(
        "--arms",
        type=_parse_arms,
        default=["off", "on", "placebo", "cot"],
        help=(
            "comma-separated arm names from solvers/arms.py, default the four "
            "non-in_situ arms. 'in_situ' is included by naming it explicitly"
        ),
    )
    parser.add_argument(
        "--skill-body", type=Path, help="text file for the 'on'/'in_situ' arms' skill body"
    )
    parser.add_argument(
        "--placebo-body", type=Path, help="text file for the 'placebo' arm's matched filler"
    )
    parser.add_argument("--budget", type=float, default=5.0, help="notional USD, across all arms")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0, help="cap items, for a smoke run")
    parser.add_argument(
        "--run-id", help="defaults to a fresh id; pass one back in to tag a resumed invocation"
    )
    args = parser.parse_args()

    try:
        assert_model_allowed(args.arena, args.model, backend="claude_code")
    except ArenaError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1

    try:
        items = load_item_corpus(args.items)
    except ItemCorpusError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1
    if args.limit:
        items = items[: args.limit]

    skill_body = args.skill_body.read_text(encoding="utf-8") if args.skill_body else None
    placebo_body = args.placebo_body.read_text(encoding="utf-8") if args.placebo_body else None
    try:
        arm_prompts = [
            build_arm(name, skill_body=skill_body, placebo_body=placebo_body) for name in args.arms
        ]
    except ArmError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1

    try:
        with RunLock(args.checkpoint):
            return _run(args, items, arm_prompts)
    except RunLockError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 2


def _run(
    args: argparse.Namespace, items: list[ElicitationItem], arm_prompts: list[ArmPrompt]
) -> int:
    """The write path, called with :class:`RunLock` already held.

    Split out from :func:`main` so the lock's scope is visible at the call
    site rather than implied by indentation depth: everything that touches
    ``args.checkpoint`` -- the corpus check, every arm, the final report --
    happens in here, and nothing that touches it happens outside it.
    """
    try:
        assert_checkpoint_matches(args.checkpoint, items)
    except CorpusMismatchError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 2

    run_id = args.run_id or uuid.uuid4().hex[:12]
    already = load_checkpoint(args.checkpoint)
    ledger = BudgetLedger(limit_usd=args.budget, spent_usd=sum(r.cost_usd for r in already))

    with tempfile.TemporaryDirectory(prefix="de-elicit-preflight-") as scratch:
        print(f"preflight against {args.model} ...", flush=True)
        try:
            preflight(model=args.model, cwd=scratch)
        except RunError as exc:
            print(f"\n{exc}", file=sys.stderr)
            return 2

    call = make_call(args.model)
    print(
        f"run {run_id}: {len(items)} item(s) x {len(arm_prompts)} arm(s), "
        f"checkpoint {args.checkpoint}",
        flush=True,
    )
    for arm in arm_prompts:
        print(f"  arm {arm.arm} ...", flush=True)
        try:
            produced = run_elicitation(
                items,
                arm,
                model=args.model,
                backend="claude",
                arena=args.arena,
                checkpoint=args.checkpoint,
                call=call,
                ledger=ledger,
                run_id=run_id,
                concurrency=args.concurrency,
            )
        except (RunError, IsolationError) as exc:
            print(f"\nrun stopped in arm {arm.arm}: {exc}", file=sys.stderr)
            print("checkpoint is intact; rerun to resume", file=sys.stderr)
            return 2
        ledger = BudgetLedger(
            limit_usd=ledger.limit_usd,
            spent_usd=ledger.spent_usd + sum(record.cost_usd for record in produced),
        )
        print(f"    {len(produced)} new record(s), ${ledger.spent_usd:.3f} spent so far")

    print()
    print_exclusion_report(load_checkpoint(args.checkpoint))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
