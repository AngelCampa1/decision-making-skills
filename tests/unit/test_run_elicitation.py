"""Tests for `scripts/run_elicitation.py`.

No model is called anywhere here. What is checked is the wiring this script
is responsible for and `elicit.py` is not: the corpus loader round-trips the
closed union, the corpus fingerprint refuses a resume into a changed item,
and -- the reason this file exists -- the cross-process lock actually
refuses a second writer and actually survives a crash without wedging a
later resume. `RunLock` is tested against a real OS lock, not a fake:
`de check` runs on both Windows and CI's POSIX runner, and a fake would
prove the wiring rather than the guarantee.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from types import ModuleType

import pytest

from decision_evals.elicit import (
    CallAsk,
    ElicitationItem,
    ElicitationRecord,
    MembershipAsk,
    ScalarAsk,
)


def _load() -> ModuleType:
    """Import ``scripts/run_elicitation.py``, which is not part of the package."""
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_elicitation.py"
    spec = importlib.util.spec_from_file_location("run_elicitation", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_elicitation"] = module
    spec.loader.exec_module(module)
    return module


runner = _load()


# --------------------------------------------------------------------------- #
# One writer at a time
# --------------------------------------------------------------------------- #


class TestRunLock:
    """Two runners raced on one checkpoint on 2026-08-25 and nothing in the
    harness stopped them; the resume key made the damage recoverable, which
    the incident's own write-up says is not the same thing as a guard. This
    is the guard, and it is tested against the real OS primitive."""

    def test_a_second_writer_is_refused_while_the_first_holds_it(self, tmp_path: Path) -> None:
        """Standing rule: show the refusal before believing it works."""
        checkpoint = tmp_path / "run.jsonl"
        with (
            runner.RunLock(checkpoint),
            pytest.raises(runner.RunLockError, match="held by another process"),
            runner.RunLock(checkpoint),
        ):
            pass  # pragma: no cover -- the context is never entered

    def test_the_lock_is_free_again_once_the_holder_releases_it(self, tmp_path: Path) -> None:
        """An ordinary exit -- no crash -- is the common case, not the one this
        class exists for, but it must not wedge either."""
        checkpoint = tmp_path / "run.jsonl"
        with runner.RunLock(checkpoint):
            pass
        with runner.RunLock(checkpoint):
            pass  # second acquisition after a clean release does not raise

    def test_a_held_lock_survives_an_exception_inside_the_block(self, tmp_path: Path) -> None:
        """The lock must release on an abnormal exit, not just a clean return,
        or a run that stops on a `RunError` would wedge every resume after it."""
        checkpoint = tmp_path / "run.jsonl"

        class _BoomError(Exception):
            pass

        with pytest.raises(_BoomError), runner.RunLock(checkpoint):
            raise _BoomError
        with runner.RunLock(checkpoint):
            pass  # did not wedge

    def test_a_crashed_holder_does_not_wedge_a_resume(self, tmp_path: Path) -> None:
        """The property this design leans on: staleness is not a state an OS
        advisory lock can be in. A holder killed with no chance to run its own
        cleanup still releases the lock, because the OS releases it when the
        process's file handle closes -- which a kill does too. Proven against a
        real second process, not a thread, because a second thread in this
        process would share its file-handle table and the lock is scoped to
        the handle, not the process.
        """
        checkpoint = tmp_path / "run.jsonl"
        holder_script = Path(__file__).resolve().parent / "_run_elicitation_lock_holder.py"

        import subprocess

        process = subprocess.Popen(
            [sys.executable, str(holder_script), str(checkpoint)],
            stdout=subprocess.PIPE,
            text=True,
        )
        try:
            line = process.stdout.readline() if process.stdout else ""
            assert line.strip() == "locked", f"holder did not report locked: {line!r}"

            with pytest.raises(runner.RunLockError), runner.RunLock(checkpoint):
                pass  # pragma: no cover

            process.kill()
            process.wait(timeout=10)
            time.sleep(0.2)  # let the OS finish reclaiming the handle

            with runner.RunLock(checkpoint):
                pass  # the crash did not wedge this
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)


# --------------------------------------------------------------------------- #
# Duplicate resolution
# --------------------------------------------------------------------------- #


def _record(item_id: str, arm: str, *, cost: float = 0.01) -> ElicitationRecord:
    return ElicitationRecord(
        item_id=item_id,
        construct="council",
        cluster_id="s1",
        condition_label="AB",
        repeat=0,
        ask_kind="call",
        ask=CallAsk(ordering="AB", first_course="expand", second_course="hold", block="CALL"),
        arm=arm,
        model="haiku",
        backend="claude",
        arena="dev",
        set_version=1,
        concurrency=1,
        run_id="run-1",
        call_status="ok",
        isolation_ok=True,
        cost_usd=cost,
        input_tokens=1,
        output_tokens=1,
        duration_ms=1,
        response="expand",
        schema_version=1,
    )


class TestDeduplicate:
    """The exact shape 2026-08-25 left: two rows for one `(item_id, arm)`, with
    no rule saying which one is the measurement. `deduplicate` is that rule,
    stated instead of applied by whoever happens to be looking."""

    def test_the_first_row_in_file_order_is_kept(self, tmp_path: Path) -> None:
        first = _record("i1", "off", cost=0.01)
        second = _record("i1", "off", cost=0.02)
        kept = runner.deduplicate([first, second], parked_path=tmp_path / "run.jsonl.parked")
        assert kept == [first]

    def test_the_repeat_is_parked_rather_than_dropped(self, tmp_path: Path) -> None:
        first = _record("i1", "off")
        second = _record("i1", "off", cost=0.02)
        parked_path = tmp_path / "run.jsonl.parked"
        runner.deduplicate([first, second], parked_path=parked_path)

        parked_rows = [json.loads(line) for line in parked_path.read_text().splitlines()]
        assert len(parked_rows) == 1
        assert parked_rows[0]["cost_usd"] == 0.02

    def test_no_duplicate_means_no_parked_file(self, tmp_path: Path) -> None:
        parked_path = tmp_path / "run.jsonl.parked"
        runner.deduplicate([_record("i1", "off"), _record("i2", "off")], parked_path=parked_path)
        assert not parked_path.exists()

    def test_the_same_item_under_two_different_arms_is_not_a_duplicate(
        self, tmp_path: Path
    ) -> None:
        """The key is `(item_id, arm)`, not `item_id` alone -- the whole point
        of one shared checkpoint across arms is that the same item recurs."""
        off = _record("i1", "off")
        on = _record("i1", "on")
        kept = runner.deduplicate([off, on], parked_path=tmp_path / "run.jsonl.parked")
        assert kept == [off, on]


# --------------------------------------------------------------------------- #
# The corpus format
# --------------------------------------------------------------------------- #


class TestLoadItemCorpus:
    def test_each_ask_kind_round_trips(self, tmp_path: Path) -> None:
        path = tmp_path / "corpus.jsonl"
        rows = [
            {
                "item_id": "ledger|t1|base|r0",
                "construct": "ledger",
                "cluster_id": "t1",
                "condition_label": "base",
                "repeat": 0,
                "ask_kind": "scalar",
                "ask": {"role": "base", "unit": "days"},
                "prompt": "how many days?",
                "set_version": 1,
            },
            {
                "item_id": "cascade|t1|treatment|r0",
                "construct": "cascade",
                "cluster_id": "t1",
                "condition_label": "treatment",
                "repeat": 0,
                "ask_kind": "membership",
                "ask": {"role": "treatment", "block": "MISSING"},
                "prompt": "name the missing step",
                "set_version": 1,
            },
            {
                "item_id": "council|s1|AB|r0",
                "construct": "council",
                "cluster_id": "s1",
                "condition_label": "AB",
                "repeat": 0,
                "ask_kind": "call",
                "ask": {
                    "ordering": "AB",
                    "first_course": "expand",
                    "second_course": "hold",
                    "block": "CALL",
                },
                "prompt": "First: expand\nSecond: hold",
                "set_version": 1,
            },
        ]
        path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

        items = runner.load_item_corpus(path)

        assert [item.item_id for item in items] == [row["item_id"] for row in rows]
        assert isinstance(items[0].ask, ScalarAsk)
        assert isinstance(items[1].ask, MembershipAsk)
        assert isinstance(items[2].ask, CallAsk)

    def test_an_unknown_ask_kind_is_refused(self, tmp_path: Path) -> None:
        path = tmp_path / "corpus.jsonl"
        path.write_text(
            json.dumps(
                {
                    "item_id": "x|t1|base|r0",
                    "construct": "x",
                    "cluster_id": "t1",
                    "condition_label": "base",
                    "repeat": 0,
                    "ask_kind": "essay",
                    "ask": {},
                    "prompt": "p",
                    "set_version": 1,
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(runner.ItemCorpusError, match="unknown ask_kind"):
            runner.load_item_corpus(path)

    def test_a_repeated_item_id_is_refused(self, tmp_path: Path) -> None:
        row = {
            "item_id": "ledger|t1|base|r0",
            "construct": "ledger",
            "cluster_id": "t1",
            "condition_label": "base",
            "repeat": 0,
            "ask_kind": "scalar",
            "ask": {"role": "base", "unit": "days"},
            "prompt": "p",
            "set_version": 1,
        }
        path = tmp_path / "corpus.jsonl"
        path.write_text(f"{json.dumps(row)}\n{json.dumps(row)}", encoding="utf-8")
        with pytest.raises(runner.ItemCorpusError, match="repeats item_id"):
            runner.load_item_corpus(path)

    def test_an_empty_corpus_is_refused(self, tmp_path: Path) -> None:
        path = tmp_path / "corpus.jsonl"
        path.write_text("\n\n", encoding="utf-8")
        with pytest.raises(runner.ItemCorpusError, match="no items"):
            runner.load_item_corpus(path)


def _item(item_id: str = "council|s1|AB|r0", prompt: str = "First: expand") -> ElicitationItem:
    return ElicitationItem(
        item_id=item_id,
        construct="council",
        cluster_id="s1",
        condition_label="AB",
        repeat=0,
        ask=CallAsk(ordering="AB", first_course="expand", second_course="hold", block="CALL"),
        prompt=prompt,
        set_version=1,
    )


class TestCorpusFingerprint:
    """`scripts/calibrate.py` learned this first: a checkpoint keyed on item id
    resumes cleanly against a rewritten item at the same id, scoring half the
    run on one corpus and half on another with nothing to notice."""

    def test_identical_items_in_a_different_order_fingerprint_the_same(self) -> None:
        a, b = _item("i1"), _item("i2")
        assert runner.corpus_fingerprint([a, b]) == runner.corpus_fingerprint([b, a])

    def test_a_changed_prompt_changes_the_fingerprint(self) -> None:
        original = runner.corpus_fingerprint([_item(prompt="First: expand")])
        changed = runner.corpus_fingerprint([_item(prompt="First: hold")])
        assert original != changed

    def test_a_fresh_checkpoint_records_the_fingerprint_without_refusing(
        self, tmp_path: Path
    ) -> None:
        checkpoint = tmp_path / "run.jsonl"
        runner.assert_checkpoint_matches(checkpoint, [_item()])
        assert checkpoint.with_name("run.jsonl.corpus").exists()

    def test_a_changed_corpus_is_refused_on_resume(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "run.jsonl"
        runner.assert_checkpoint_matches(checkpoint, [_item(prompt="First: expand")])
        with pytest.raises(runner.CorpusMismatchError, match="different corpus"):
            runner.assert_checkpoint_matches(checkpoint, [_item(prompt="First: hold")])

    def test_the_same_corpus_resumes_without_complaint(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "run.jsonl"
        runner.assert_checkpoint_matches(checkpoint, [_item()])
        runner.assert_checkpoint_matches(checkpoint, [_item()])  # does not raise


# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #


class TestParseArms:
    def test_a_comma_list_splits_and_orders_is_preserved(self) -> None:
        assert runner._parse_arms("on, off ,cot") == ["on", "off", "cot"]

    def test_an_unknown_arm_name_is_refused(self) -> None:
        import argparse

        with pytest.raises(argparse.ArgumentTypeError, match="unknown arm"):
            runner._parse_arms("off,made-up")


# --------------------------------------------------------------------------- #
# load_checkpoint composes load_elicitation with deduplicate
# --------------------------------------------------------------------------- #


class TestLoadCheckpoint:
    def test_a_missing_checkpoint_is_an_empty_list(self, tmp_path: Path) -> None:
        assert runner.load_checkpoint(tmp_path / "nope.jsonl") == []

    def test_a_duplicate_row_on_disk_is_parked_on_read(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "run.jsonl"
        first = _record("i1", "off", cost=0.01)
        second = _record("i1", "off", cost=0.02)
        with checkpoint.open("w", encoding="utf-8") as handle:
            for record in (first, second):
                handle.write(json.dumps(asdict(record)) + "\n")

        loaded = runner.load_checkpoint(checkpoint)

        assert len(loaded) == 1
        assert loaded[0].cost_usd == 0.01
        assert checkpoint.with_name("run.jsonl.parked").exists()
