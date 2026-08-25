"""Tests for the scalar elicitation loop.

Two properties carry most of the weight here.

**The record cannot hold a score.** Two of these tests assert the exact field
names on :class:`~decision_evals.elicit.ScalarItem` and
:class:`~decision_evals.elicit.ElicitationRecord`. That reads as pedantry until
the day someone adds ``expected`` to the item "just to keep it together", at
which point the extractor downstream can see the answer key and the blindness
this design is built on is gone with no test failing.

**Backpressure has never been exercised against a real wall.** The entry of
2026-08-20 says so in its own words: no rate limit was hit during the run that
followed it, so the code that landed the day before was never run in anger.
The class at the bottom of this file injects the faults instead. Nothing
sleeps: the schedule is driven with zero delays, so what is exercised is the
retry, the breaker and the checkpoint rather than the wall time they would
cost.
"""

from __future__ import annotations

import json
import threading
from collections import Counter
from collections.abc import Callable
from dataclasses import fields
from pathlib import Path

import pytest

from decision_evals.budget import BudgetLedger
from decision_evals.elicit import (
    ElicitationRecord,
    ScalarItem,
    load_elicitation,
    run_elicitation,
)
from decision_evals.providers.claude_code import (
    AuthenticationError,
    CliError,
    CliResult,
    Elicited,
    InitReceipt,
    IsolationError,
    PromptTooLongError,
    RateLimitedError,
)
from decision_evals.runner import Backoff, RunError
from decision_evals.solvers.arms import build_arm

ARM = build_arm("off")

#: Zero delays. The schedule itself is tested in `test_backpressure.py`.
NO_WAIT = Backoff(attempts=5, base_delay=0.0, max_delay=0.0)


def _item(triplet: str, role: str = "base", repeat: int = 0) -> ScalarItem:
    item_id = f"ledger|{triplet}|{role}|r{repeat}"
    return ScalarItem(
        item_id=item_id,
        construct="ledger",
        triplet_id=triplet,
        role=role,  # type: ignore[arg-type]
        arm_label="unaided" if role == "base" else role,
        repeat=repeat,
        unit="days",
        prompt=f"How many days? [{item_id}]",
        set_version=1,
    )


def _items(count: int) -> list[ScalarItem]:
    return [_item(f"t{index:02d}") for index in range(count)]


def _elicited(text: str, *, cost: float = 0.001) -> Elicited:
    return Elicited(
        result=CliResult(
            text=text,
            model="claude-haiku-4-5-20251001",
            cost_usd=cost,
            input_tokens=100,
            output_tokens=20,
            duration_ms=1000,
            session_id="session-1",
        ),
        receipt=InitReceipt(),
    )


class _Backend:
    """A stub isolated backend that can be told to refuse scheduled calls.

    ``refuse`` sees the prompt and how many times that prompt has been sent,
    counting from one, and returns the exception to raise or ``None`` to let
    the call through. Counting per prompt rather than per run is what makes
    "fail the first attempt at every item" expressible, which is the shape a
    quota window actually has.
    """

    def __init__(
        self,
        refuse: Callable[[str, int], BaseException | None] | None = None,
        *,
        cost: float = 0.001,
    ) -> None:
        self.calls: list[str] = []
        self._refuse = refuse
        self._cost = cost
        self._seen: Counter[str] = Counter()
        self._lock = threading.Lock()

    def __call__(self, prompt: str, system_prompt: str, in_situ: bool) -> Elicited:
        del system_prompt, in_situ
        with self._lock:
            self._seen[prompt] += 1
            attempt = self._seen[prompt]
            self.calls.append(prompt)
        if self._refuse is not None and (failure := self._refuse(prompt, attempt)) is not None:
            raise failure
        return _elicited(f"answer to {prompt}", cost=self._cost)

    @property
    def item_ids(self) -> list[str]:
        """The item id out of each prompt, in the order the calls were made."""
        return [prompt.split("[")[1].rstrip("]") for prompt in self.calls]


def _run(
    items: list[ScalarItem],
    backend: _Backend,
    checkpoint: Path,
    **overrides: object,
) -> list[ElicitationRecord]:
    settings: dict[str, object] = {
        "model": "haiku",
        "backend": "claude",
        "arena": "dev",
        "checkpoint": checkpoint,
        "call": backend,
        "ledger": BudgetLedger(limit_usd=10.0),
        "run_id": "run-1",
        "backoff": NO_WAIT,
    }
    settings.update(overrides)
    return run_elicitation(items, ARM, **settings)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# Nothing on these types can hold an answer
# --------------------------------------------------------------------------- #


class TestTheTypesAreBlind:
    def test_the_item_carries_no_expected_value(self) -> None:
        """An exact set, not a subset check.

        A subset check passes when a field is added. The whole design rests on
        there being nowhere for an answer key to arrive, so the assertion has
        to fail when somewhere appears.
        """
        assert {field.name for field in fields(ScalarItem)} == {
            "item_id",
            "construct",
            "triplet_id",
            "role",
            "arm_label",
            "repeat",
            "unit",
            "prompt",
            "set_version",
        }

    def test_the_record_carries_no_quantity_and_no_score(self) -> None:
        assert {field.name for field in fields(ElicitationRecord)} == {
            "item_id",
            "construct",
            "triplet_id",
            "role",
            "arm_label",
            "repeat",
            "arm",
            "model",
            "backend",
            "arena",
            "set_version",
            "concurrency",
            "run_id",
            "call_status",
            "isolation_ok",
            "cost_usd",
            "input_tokens",
            "output_tokens",
            "duration_ms",
            "response",
            "schema_version",
            "conversation_id",
        }


# --------------------------------------------------------------------------- #
# The ordinary path
# --------------------------------------------------------------------------- #


def test_a_run_produces_one_record_per_item(tmp_path: Path) -> None:
    items = _items(3)
    records = _run(items, _Backend(), tmp_path / "e.jsonl")
    assert len(records) == 3
    assert {record.call_status for record in records} == {"ok"}
    assert all(record.isolation_ok for record in records)


def test_the_response_is_stored_verbatim(tmp_path: Path) -> None:
    """A changed extractor is re-run over the file rather than over the quota."""
    items = _items(1)
    records = _run(items, _Backend(), tmp_path / "e.jsonl")
    assert records[0].response == f"answer to {items[0].prompt}"


def test_the_resolved_model_id_reaches_the_record(tmp_path: Path) -> None:
    """`haiku` is not a version, so the record carries what the backend served."""
    records = _run(_items(1), _Backend(), tmp_path / "e.jsonl")
    assert records[0].model == "claude-haiku-4-5-20251001"


def test_every_row_says_what_concurrency_produced_it(tmp_path: Path) -> None:
    """Written on every row and never left to a default.

    Read off the file rather than off the object: a field that exists on the
    dataclass and never reaches the JSON is the failure this guards.
    """
    checkpoint = tmp_path / "e.jsonl"
    _run(_items(4), _Backend(), checkpoint, concurrency=2)
    rows = [json.loads(line) for line in checkpoint.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 4
    assert {row["concurrency"] for row in rows} == {2}
    assert {row["run_id"] for row in rows} == {"run-1"}
    assert {row["arena"] for row in rows} == {"dev"}


def test_the_item_travels_onto_the_record(tmp_path: Path) -> None:
    """The triplet is the cluster, so it has to survive to the file."""
    records = _run([_item("t07", role="treatment", repeat=1)], _Backend(), tmp_path / "e.jsonl")
    assert records[0].triplet_id == "t07"
    assert records[0].role == "treatment"
    assert records[0].repeat == 1
    assert records[0].set_version == 1
    assert records[0].arm == "off"


@pytest.mark.parametrize("bad", [0, -1])
def test_a_non_positive_concurrency_is_refused(tmp_path: Path, bad: int) -> None:
    with pytest.raises(RunError, match="concurrency must be at least 1"):
        _run(_items(1), _Backend(), tmp_path / "e.jsonl", concurrency=bad)


def test_the_checkpoint_directory_is_created(tmp_path: Path) -> None:
    checkpoint = tmp_path / "deep" / "nested" / "e.jsonl"
    _run(_items(1), _Backend(), checkpoint)
    assert checkpoint.exists()


# --------------------------------------------------------------------------- #
# What a failed call is recorded as
# --------------------------------------------------------------------------- #


def test_a_prompt_that_does_not_fit_is_a_construction_defect(tmp_path: Path) -> None:
    """Deterministic, so it is recorded rather than retried.

    The backoff here allows five attempts. One call is made, because waiting
    would never help: the item will overflow the window every time, and
    filing it under `infrastructure` would put a reproducible authoring
    mistake in the same bucket as a flaky network.
    """
    backend = _Backend(lambda prompt, attempt: PromptTooLongError("Prompt is too long"))
    records = _run(_items(1), backend, tmp_path / "e.jsonl")
    assert len(backend.calls) == 1
    assert records[0].call_status == "prompt_too_long"
    assert records[0].cost_usd == 0.0
    assert records[0].isolation_ok is False
    assert "too long" in records[0].response


def test_an_ordinary_failure_is_an_infrastructure_row(tmp_path: Path) -> None:
    backend = _Backend(lambda prompt, attempt: CliError("the process died"))
    records = _run(_items(1), backend, tmp_path / "e.jsonl")
    assert records[0].call_status == "infrastructure"
    assert records[0].response == "the process died"
    assert records[0].input_tokens == 0


def test_authentication_stops_the_run(tmp_path: Path) -> None:
    backend = _Backend(lambda prompt, attempt: AuthenticationError("please authenticate"))
    with pytest.raises(RunError, match="authentication failed"):
        _run(_items(3), backend, tmp_path / "e.jsonl")


def test_an_isolation_failure_stops_the_run_and_keeps_its_batch(tmp_path: Path) -> None:
    """The call would have succeeded. What is wrong is the venue it succeeded in.

    The batch is still drained, so the calls that landed beside the refusal
    are on disk and a resume does not pay for them twice.
    """
    checkpoint = tmp_path / "e.jsonl"
    items = _items(2)
    doomed = items[1].prompt

    def refuse(prompt: str, attempt: int) -> BaseException | None:
        return IsolationError("the CLI loaded 3 tools") if prompt == doomed else None

    with pytest.raises(IsolationError, match="loaded 3 tools"):
        _run(items, _Backend(refuse), checkpoint, concurrency=2)

    survived = load_elicitation(checkpoint)
    assert [record.item_id for record in survived] == [items[0].item_id]


# --------------------------------------------------------------------------- #
# Resume
# --------------------------------------------------------------------------- #


def test_a_resumed_run_skips_completed_work(tmp_path: Path) -> None:
    checkpoint = tmp_path / "e.jsonl"
    items = _items(3)
    _run(items[:2], _Backend(), checkpoint)

    second = _Backend()
    made = _run(items, second, checkpoint)
    assert [record.item_id for record in made] == [items[2].item_id]
    assert second.item_ids == [items[2].item_id]
    assert len(load_elicitation(checkpoint)) == 3


def test_the_same_item_runs_again_in_a_second_arm(tmp_path: Path) -> None:
    """Resume is keyed on the arm as well as the item, as `run_arm`'s is."""
    checkpoint = tmp_path / "e.jsonl"
    items = _items(1)
    _run(items, _Backend(), checkpoint)
    second = _Backend()
    made = run_elicitation(
        items,
        build_arm("cot"),
        model="haiku",
        backend="claude",
        arena="dev",
        checkpoint=checkpoint,
        call=second,
        ledger=BudgetLedger(limit_usd=10.0),
        run_id="run-2",
        backoff=NO_WAIT,
    )
    assert len(made) == 1
    assert made[0].arm == "cot"


# --------------------------------------------------------------------------- #
# Reading a checkpoint back
# --------------------------------------------------------------------------- #


class TestLoading:
    def test_an_absent_checkpoint_is_an_empty_one(self, tmp_path: Path) -> None:
        assert load_elicitation(tmp_path / "nothing.jsonl") == []

    def test_a_truncated_final_line_is_tolerated(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "e.jsonl"
        _run(_items(2), _Backend(), checkpoint)
        with checkpoint.open("a", encoding="utf-8") as handle:
            handle.write('{"item_id": "hal')
        assert len(load_elicitation(checkpoint)) == 2

    def test_blank_lines_are_ignored(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "e.jsonl"
        _run(_items(1), _Backend(), checkpoint)
        with checkpoint.open("a", encoding="utf-8") as handle:
            handle.write("\n\n")
        assert len(load_elicitation(checkpoint)) == 1

    def test_corruption_before_the_last_line_is_refused(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "e.jsonl"
        checkpoint.write_text("{oh no\n{}\n", encoding="utf-8")
        with pytest.raises(RunError, match="corruption rather than an interrupted write"):
            load_elicitation(checkpoint)

    def test_a_record_from_another_schema_is_refused_loudly(self, tmp_path: Path) -> None:
        """Skipping it silently makes a new column erase the run before it."""
        checkpoint = tmp_path / "e.jsonl"
        checkpoint.write_text(json.dumps({"item_id": "a"}) + "\n", encoding="utf-8")
        with pytest.raises(RunError, match="does not match the current ElicitationRecord"):
            load_elicitation(checkpoint)


# --------------------------------------------------------------------------- #
# Backpressure, with the faults injected
# --------------------------------------------------------------------------- #


class TestARateLimitedRun:
    """The wall this repository has never actually met.

    `notebook/2026-08-20-...` records that the run following the backpressure
    work hit no rate limit, so none of it ran. These four inject the refusals
    the quota never supplied.
    """

    def test_a_rate_limited_call_leaves_no_record_behind(self, tmp_path: Path) -> None:
        """It clears on its own, so it is waited out rather than written down.

        Two refusals then a success: three calls, one row, and the row says
        `ok`. Recording the refusal instead would put a model failure that
        never happened on the file and spend the item to do it.
        """
        checkpoint = tmp_path / "e.jsonl"
        backend = _Backend(
            lambda prompt, attempt: RateLimitedError("429") if attempt <= 2 else None
        )
        records = _run(_items(1), backend, checkpoint)

        assert len(backend.calls) == 3
        assert len(records) == 1
        assert records[0].call_status == "ok"
        assert len(checkpoint.read_text(encoding="utf-8").splitlines()) == 1

    def test_the_breaker_stops_the_run_with_the_checkpoint_intact(self, tmp_path: Path) -> None:
        """A wall that does not move is a window that closed.

        The first item gets through, the second never does. The breaker fires
        after `breaker_trips` consecutive refusals and the run stops rather
        than spending the rest of the corpus against a closed window; what
        landed before it is still on disk.
        """
        checkpoint = tmp_path / "e.jsonl"
        items = _items(3)
        doomed = items[1].prompt
        backend = _Backend(
            lambda prompt, attempt: RateLimitedError("429") if prompt == doomed else None
        )

        with pytest.raises(RunError, match="consecutive rate-limited"):
            _run(
                items,
                backend,
                checkpoint,
                backoff=Backoff(attempts=99, base_delay=0.0, max_delay=0.0, breaker_trips=3),
            )

        on_disk = load_elicitation(checkpoint)
        assert [record.item_id for record in on_disk] == [items[0].item_id]
        # Four refusals: three the breaker tolerated and the one that tripped it.
        assert backend.item_ids.count(items[1].item_id) == 4

    def test_a_resume_re_runs_exactly_the_calls_that_never_landed(self, tmp_path: Path) -> None:
        """Not one more, and not one fewer.

        Re-running a call that landed spends quota twice and puts two rows on
        one item. Skipping one that never landed leaves a hole the analysis
        reads as a completed run.
        """
        checkpoint = tmp_path / "e.jsonl"
        items = _items(4)
        doomed = items[1].prompt
        first = _Backend(
            lambda prompt, attempt: RateLimitedError("429") if prompt == doomed else None
        )
        with pytest.raises(RunError, match="consecutive rate-limited"):
            _run(
                items,
                first,
                checkpoint,
                backoff=Backoff(attempts=99, base_delay=0.0, max_delay=0.0, breaker_trips=2),
            )

        landed = {record.item_id for record in load_elicitation(checkpoint)}
        assert landed == {items[0].item_id}

        second = _Backend()
        made = _run(items, second, checkpoint)
        expected = [item.item_id for item in items if item.item_id not in landed]
        assert second.item_ids == expected
        assert [record.item_id for record in made] == expected
        assert len(load_elicitation(checkpoint)) == 4

    def test_a_drained_batch_releases_every_reserve(self, tmp_path: Path) -> None:
        """A batch mixing a call that got through with one that had to wait.

        The budget is reserved at dispatch and released when the record
        arrives. If a reserve outlived its call, the ledger would refuse a
        later dispatch that the limit plainly allows -- and the arithmetic here
        makes that visible rather than assumed. Six items at $0.01 each,
        against a $0.025 limit and two calls in flight: two live reserves are
        $0.020 and fit, three would be $0.030 and would not. Every call
        records $0.00, so nothing but a leaked reserve can stop the run.

        Every second item is refused once before it succeeds, so each batch
        holds one reserve that is released immediately and one that is held
        across a wait.
        """
        checkpoint = tmp_path / "e.jsonl"
        items = _items(6)
        waiting = {item.prompt for index, item in enumerate(items) if index % 2 == 1}
        backend = _Backend(
            lambda prompt, attempt: (
                RateLimitedError("429") if prompt in waiting and attempt == 1 else None
            ),
            cost=0.0,
        )

        records = _run(
            items,
            backend,
            checkpoint,
            ledger=BudgetLedger(limit_usd=0.025),
            expected_cost_usd=0.01,
            concurrency=2,
        )

        assert len(records) == 6
        assert {record.call_status for record in records} == {"ok"}
        assert len(backend.calls) == 9
