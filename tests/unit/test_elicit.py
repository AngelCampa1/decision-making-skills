"""Tests for the elicitation loop.

Three properties carry most of the weight here.

**The record cannot hold a score.** Five of these tests assert the exact field
names on :class:`~decision_evals.elicit.ElicitationItem`, on
:class:`~decision_evals.elicit.ElicitationRecord` and on each of the three ask
types. That reads as pedantry until the day someone adds ``expected`` to the
item "just to keep it together", at which point the extractor downstream can
see the answer key and the blindness this design is built on is gone with no
test failing. The ask types get the same treatment because the union is where
a family-specific answer key would now be easiest to hide.

**A record is scoreable from the file alone.** ``TestACouncilRun`` computes
both of ``council``'s candidate estimators out of a loaded checkpoint and
nothing else: the second-position rate from single records, and the
recommendation flip rate the registration names from records paired on their
cluster. Neither opens the item that produced a row.

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
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import pytest

from decision_evals.budget import BudgetLedger
from decision_evals.elicit import (
    ASK_KINDS,
    ASK_TYPES,
    Ask,
    CallAsk,
    CommonItemSet,
    ElicitationItem,
    ElicitationRecord,
    ExclusionRow,
    MembershipAsk,
    ScalarAsk,
    common_item_set,
    exclusion_counts,
    format_exclusion_counts,
    load_elicitation,
    print_exclusion_report,
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


def _item(
    cluster: str,
    ask: Ask | None = None,
    *,
    construct: str = "ledger",
    condition_label: str = "unaided",
    repeat: int = 0,
) -> ElicitationItem:
    ask = ask if ask is not None else ScalarAsk(role="base", unit="days")
    item_id = f"{construct}|{cluster}|{condition_label}|r{repeat}"
    return ElicitationItem(
        item_id=item_id,
        construct=construct,
        cluster_id=cluster,
        condition_label=condition_label,
        repeat=repeat,
        ask=ask,
        prompt=f"How many days? [{item_id}]",
        set_version=1,
    )


def _label_for(ask: Ask) -> str:
    """A council record's condition label is its ordering, and the record says so."""
    return ask.ordering if isinstance(ask, CallAsk) else "unaided"


def _items(count: int) -> list[ElicitationItem]:
    return [_item(f"t{index:02d}") for index in range(count)]


def _council_items(cluster: str, first: str, second: str) -> list[ElicitationItem]:
    """One scenario in both orderings.

    ``AB`` prints ``first`` then ``second``; ``BA`` prints the same two courses
    the other way round. The prompt names them in the order it printed them, so
    a stub can answer by position without being told which arm it is in.
    """
    items = []
    for ordering, (top, bottom) in (("AB", (first, second)), ("BA", (second, first))):
        item_id = f"council|{cluster}|{ordering}|r0"
        items.append(
            ElicitationItem(
                item_id=item_id,
                construct="council",
                cluster_id=cluster,
                condition_label=ordering,
                repeat=0,
                ask=CallAsk(
                    ordering=ordering,  # type: ignore[arg-type]
                    first_course=top,
                    second_course=bottom,
                    block="CALL",
                ),
                prompt=f"First: {top}\nSecond: {bottom}\n[{item_id}]",
                set_version=1,
            )
        )
    return items


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

    ``reply`` turns a prompt into the text that comes back, so a test can make
    the stub answer by position or by name.
    """

    def __init__(
        self,
        refuse: Callable[[str, int], BaseException | None] | None = None,
        *,
        cost: float = 0.001,
        reply: Callable[[str], str] | None = None,
    ) -> None:
        self.calls: list[str] = []
        self._refuse = refuse
        self._cost = cost
        self._reply = reply or (lambda prompt: f"answer to {prompt}")
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
        return _elicited(self._reply(prompt), cost=self._cost)

    @property
    def item_ids(self) -> list[str]:
        """The item id out of each prompt, in the order the calls were made."""
        return [prompt.split("[")[1].rstrip("]") for prompt in self.calls]


def _run(
    items: list[ElicitationItem],
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


def _rows(checkpoint: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in checkpoint.read_text(encoding="utf-8").splitlines()]


def _write_rows(checkpoint: Path, rows: list[dict[str, object]]) -> None:
    """Put edited rows back, so a test can damage one column and reload."""
    text = "".join(json.dumps(row) + "\n" for row in rows)
    checkpoint.write_text(text, encoding="utf-8")


def _ask_block(row: dict[str, object]) -> dict[str, object]:
    """The nested ask out of one written row, narrowed for the tests that edit it."""
    block = row["ask"]
    assert isinstance(block, dict)
    return block


# --------------------------------------------------------------------------- #
# Nothing on these types can hold an answer
# --------------------------------------------------------------------------- #


class TestTheTypesAreBlind:
    """Exact sets, not subset checks.

    A subset check passes when a field is added. The whole design rests on
    there being nowhere for an answer key to arrive, so each assertion has to
    fail when somewhere appears.
    """

    def test_the_item_carries_no_expected_value(self) -> None:
        assert {field.name for field in fields(ElicitationItem)} == {
            "item_id",
            "construct",
            "cluster_id",
            "condition_label",
            "repeat",
            "ask",
            "prompt",
            "set_version",
        }

    def test_the_record_carries_no_answer_and_no_score(self) -> None:
        assert {field.name for field in fields(ElicitationRecord)} == {
            "item_id",
            "construct",
            "cluster_id",
            "condition_label",
            "repeat",
            "ask_kind",
            "ask",
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

    def test_a_scalar_ask_carries_a_unit_and_no_quantity(self) -> None:
        assert {field.name for field in fields(ScalarAsk)} == {"role", "unit"}

    def test_a_membership_ask_carries_a_block_and_no_planted_candidate(self) -> None:
        """Which candidate was planted is the answer key and stays with the scorer."""
        assert {field.name for field in fields(MembershipAsk)} == {"role", "block"}

    def test_a_call_ask_carries_the_printed_order_and_no_correct_call(self) -> None:
        """Family C has no key: the printed order is the manipulation."""
        assert {field.name for field in fields(CallAsk)} == {
            "ordering",
            "first_course",
            "second_course",
            "block",
        }

    def test_every_ask_kind_is_declared(self) -> None:
        """Read off the union, so a fourth family cannot be half-added.

        Naming the three classes here instead would pass for a union that grew
        a member nothing else knows about, which is the failure that reaches
        the first run and spends the quota to report itself.
        """
        assert {variant.kind for variant in ASK_TYPES} == set(ASK_KINDS)
        assert set(ASK_TYPES) == {ScalarAsk, MembershipAsk, CallAsk}

    def test_no_ask_type_can_be_subclassed_into_a_record(self) -> None:
        """The hole an adversarial review opened on 2026-08-25.

        `asdict` reads the fields of the instance's own class, so a subclass
        carrying an answer key writes it to the checkpoint while
        `fields(ScalarAsk)` still reports two and every other test in this
        class still passes. mypy accepts it too. The refusal is a runtime type
        check in `_record`, and this is what holds it there.
        """

        # mypy refuses this, which is half the guard. The other half is that
        # Python does not, and a checkpoint is written at runtime.
        @dataclass(frozen=True, slots=True)
        class KeyedScalarAsk(ScalarAsk):  # type: ignore[misc]
            expected: float = 0.0

        smuggled = KeyedScalarAsk(role="base", unit="days", expected=42.0)
        assert "expected" in asdict(smuggled)
        assert "expected" not in {field.name for field in fields(ScalarAsk)}
        assert type(smuggled) not in ASK_TYPES

    def test_a_subclassed_ask_never_reaches_the_checkpoint(self, tmp_path: Path) -> None:
        """And the refusal is on the write path, so no row is spent finding out."""

        @dataclass(frozen=True, slots=True)
        class KeyedScalarAsk(ScalarAsk):  # type: ignore[misc]
            expected: float = 0.0

        checkpoint = tmp_path / "e.jsonl"
        item = _item("t01", KeyedScalarAsk(role="base", unit="days", expected=42.0))
        with pytest.raises(RunError, match="which is not one of"):
            _run([item], _Backend(), checkpoint)
        assert load_elicitation(checkpoint) == []


class TestTheAskCannotBeBuiltIncomplete:
    """The fields the design needs are required by the type, not by review."""

    def test_a_scalar_ask_needs_a_unit(self) -> None:
        with pytest.raises(TypeError, match="unit"):
            ScalarAsk(role="base")  # type: ignore[call-arg]

    def test_a_call_ask_needs_an_ordering(self) -> None:
        """The manipulation, so there is no defaulting it to AB."""
        with pytest.raises(TypeError, match="ordering"):
            CallAsk(first_course="expand", second_course="hold", block="CALL")  # type: ignore[call-arg]

    def test_one_course_named_twice_is_refused(self) -> None:
        """It would score every call as a second-position call."""
        with pytest.raises(RunError, match="both courses of this call ask are 'hold'"):
            CallAsk(ordering="AB", first_course="hold", second_course="hold", block="CALL")

    @pytest.mark.parametrize(("first", "second"), [("", "hold"), ("expand", "")])
    def test_an_empty_course_identifier_is_refused(self, first: str, second: str) -> None:
        """An unparseable reply would otherwise match it."""
        with pytest.raises(RunError, match="non-empty"):
            CallAsk(ordering="AB", first_course=first, second_course=second, block="CALL")

    @pytest.mark.parametrize("bad", [None, "", "ab", "AB ", 7])
    def test_an_ordering_outside_the_two_is_refused(self, bad: object) -> None:
        """A `Literal` binds a type checker, and a resumed run reads JSON.

        Every one of these loaded clean before the check existed, and each is
        a record that cannot say which ordering produced it.
        """
        with pytest.raises(RunError, match="ordering is"):
            CallAsk(
                ordering=bad,  # type: ignore[arg-type]
                first_course="expand",
                second_course="hold",
                block="CALL",
            )

    @pytest.mark.parametrize("role", [None, "", "banana", "Base"])
    def test_a_role_outside_the_annotation_is_refused(self, role: object) -> None:
        with pytest.raises(RunError, match="role is"):
            ScalarAsk(role=role, unit="days")  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("ask", "field"),
        [
            (lambda: ScalarAsk(role="base", unit="  "), "unit"),
            (lambda: MembershipAsk(role="treatment", block=""), "block"),
            (lambda: CallAsk("AB", "expand", "hold", ""), "block"),
        ],
    )
    def test_a_blank_identifier_is_refused(self, ask: Callable[[], Ask], field: str) -> None:
        """An empty `block` turns the extractor's prefix into a bare colon."""
        with pytest.raises(RunError, match=f"{field} is"):
            ask()

    def test_a_council_item_has_nowhere_to_put_a_unit(self) -> None:
        """The property a widened item type would have given up."""
        assert "unit" not in {field.name for field in fields(CallAsk)}
        with pytest.raises(TypeError, match="unit"):
            CallAsk(  # type: ignore[call-arg]
                ordering="AB",
                first_course="expand",
                second_course="hold",
                block="CALL",
                unit="days",
            )

    def test_a_membership_item_has_nowhere_to_put_a_unit(self) -> None:
        """The same property, on the other member the union closed against.

        A scalar quantity and a named candidate are not the same kind of
        answer, and `unit` widened onto `MembershipAsk` would let an
        extractor read a number out of a family that never asked for one.
        """
        assert "unit" not in {field.name for field in fields(MembershipAsk)}
        with pytest.raises(TypeError, match="unit"):
            MembershipAsk(role="treatment", block="MISSING", unit="days")  # type: ignore[call-arg]


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
    rows = _rows(checkpoint)
    assert len(rows) == 4
    assert {row["concurrency"] for row in rows} == {2}
    assert {row["run_id"] for row in rows} == {"run-1"}
    assert {row["arena"] for row in rows} == {"dev"}


def test_a_council_row_also_says_what_concurrency_produced_it(tmp_path: Path) -> None:
    """A council row carries ``concurrency`` on the same terms as a scalar one."""
    checkpoint = tmp_path / "e.jsonl"
    _run(_council_items("s1", "expand", "hold"), _Backend(), checkpoint, concurrency=2)
    assert {row["concurrency"] for row in _rows(checkpoint)} == {2}


def test_the_item_travels_onto_the_record(tmp_path: Path) -> None:
    """The cluster is the resampling unit, so it has to survive to the file."""
    item = _item(
        "t07", ScalarAsk(role="treatment", unit="months"), condition_label="governing", repeat=1
    )
    records = _run([item], _Backend(), tmp_path / "e.jsonl")
    assert records[0].cluster_id == "t07"
    assert records[0].condition_label == "governing"
    assert records[0].repeat == 1
    assert records[0].set_version == 1
    assert records[0].arm == "off"
    assert records[0].ask == ScalarAsk(role="treatment", unit="months")
    assert records[0].ask_kind == "scalar"


@pytest.mark.parametrize("bad", [0, -1])
def test_a_non_positive_concurrency_is_refused(tmp_path: Path, bad: int) -> None:
    with pytest.raises(RunError, match="concurrency must be at least 1"):
        _run(_items(1), _Backend(), tmp_path / "e.jsonl", concurrency=bad)


def test_the_checkpoint_directory_is_created(tmp_path: Path) -> None:
    checkpoint = tmp_path / "deep" / "nested" / "e.jsonl"
    _run(_items(1), _Backend(), checkpoint)
    assert checkpoint.exists()


def test_the_discriminator_cannot_disagree_with_the_ask(tmp_path: Path) -> None:
    """Two columns that can disagree need something that stops them."""
    record = _run(_items(1), _Backend(), tmp_path / "e.jsonl")[0]
    with pytest.raises(RunError, match="ask_kind is 'call' while the ask is a ScalarAsk"):
        ElicitationRecord(**{**vars(record), "ask_kind": "call"})


# --------------------------------------------------------------------------- #
# Family C: both candidate estimators, computed from the file alone
# --------------------------------------------------------------------------- #


def _named_call(record: ElicitationRecord) -> str | None:
    """Read the call out of the block the record says its own prompt required.

    This is the shape of the extractor downstream: it is handed a loaded
    record and never the item that produced it.
    """
    assert isinstance(record.ask, CallAsk)
    prefix = f"{record.ask.block}:"
    for line in record.response.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _calls(records: list[ElicitationRecord]) -> list[tuple[str, CallAsk, str]]:
    """Every record that named one of its own two courses, with what it named.

    A reply naming neither is not a call and leaves the denominator, which is
    why the first course is on the record as well as the second. `BALANCED`
    leaves it here.
    """
    found: list[tuple[str, CallAsk, str]] = []
    for record in records:
        ask = record.ask
        if not isinstance(ask, CallAsk):
            continue
        named = _named_call(record)
        if named is not None and named in (ask.first_course, ask.second_course):
            found.append((record.cluster_id, ask, named))
    return found


def _second_position_rate(records: list[ElicitationRecord]) -> float | None:
    """The per-record marginal: the share of calls that name the second course.

    `None` where no record named a course. An all-`BALANCED` corpus is legal
    and this used to divide by zero on one, which matters because this helper
    is the shape the real extractor will be written from.
    """
    calls = _calls(records)
    if not calls:
        return None
    named_second = [named == ask.second_course for _, ask, named in calls]
    return sum(named_second) / len(named_second)


def _flip_rate(records: list[ElicitationRecord]) -> float | None:
    """The registered primary: did the named course change between the orderings.

    Paired on `cluster_id`, which is the column that makes the pairing possible
    without opening an item. A scenario where either ordering produced no call
    is not a pair and leaves the denominator.
    """
    by_cluster: dict[str, dict[str, str]] = {}
    for cluster_id, ask, named in _calls(records):
        by_cluster.setdefault(cluster_id, {})[ask.ordering] = named
    pairs = [side for side in by_cluster.values() if len(side) == 2]
    if not pairs:
        return None
    return sum(side["AB"] != side["BA"] for side in pairs) / len(pairs)


class TestACouncilRun:
    """Two orderings of one scenario, scored out of the checkpoint."""

    def test_a_model_that_always_picks_second_scores_one(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "e.jsonl"
        items = _council_items("s1", "expand", "hold")
        backend = _Backend(
            reply=lambda prompt: "CALL: " + prompt.split("Second: ")[1].split("\n")[0]
        )
        _run(items, backend, checkpoint)

        loaded = load_elicitation(checkpoint)
        assert len(loaded) == 2
        assert _second_position_rate(loaded) == 1.0

    def test_a_model_that_always_picks_the_same_course_scores_a_half(self, tmp_path: Path) -> None:
        """The point of the instrument: it reads position, not identity.

        The same reply is a second-position call under AB and a first-position
        call under BA, so an order-blind model lands at 0.5 and only an order
        effect moves it.
        """
        checkpoint = tmp_path / "e.jsonl"
        _run(
            _council_items("s1", "expand", "hold"),
            _Backend(reply=lambda prompt: "CALL: hold"),
            checkpoint,
        )
        assert _second_position_rate(load_elicitation(checkpoint)) == 0.5

    def test_a_balanced_reply_leaves_the_denominator(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "e.jsonl"
        items = _council_items("s1", "expand", "hold") + _council_items("s2", "buy", "lease")
        _run(
            items,
            _Backend(
                reply=lambda prompt: (
                    "CALL: BALANCED"
                    if "s1" in prompt
                    else "CALL: " + prompt.split("Second: ")[1].split("\n")[0]
                )
            ),
            checkpoint,
        )
        loaded = load_elicitation(checkpoint)
        assert len(loaded) == 4
        assert _second_position_rate(loaded) == 1.0

    def test_the_ordering_round_trips_through_the_checkpoint(self, tmp_path: Path) -> None:
        """Typed on the way out, and typed again on the way back in."""
        checkpoint = tmp_path / "e.jsonl"
        _run(_council_items("s1", "expand", "hold"), _Backend(), checkpoint)

        rows = _rows(checkpoint)
        assert {row["ask_kind"] for row in rows} == {"call"}
        assert {_ask_block(row)["ordering"] for row in rows} == {"AB", "BA"}

        by_ordering = {
            record.ask.ordering: record.ask
            for record in load_elicitation(checkpoint)
            if isinstance(record.ask, CallAsk)
        }
        assert by_ordering["AB"] == CallAsk("AB", "expand", "hold", "CALL")
        assert by_ordering["BA"] == CallAsk("BA", "hold", "expand", "CALL")

    def test_the_two_estimators_are_not_the_same_statistic(self, tmp_path: Path) -> None:
        """Why the record has to serve both.

        A model that always names the same course flips nothing and still
        names the second course half the time. Reporting the marginal as
        though it were the registered flip rate would call that model an
        order effect of 0.5 when its order effect is zero.
        """
        checkpoint = tmp_path / "e.jsonl"
        _run(
            _council_items("s1", "expand", "hold") + _council_items("s2", "buy", "lease"),
            _Backend(reply=lambda prompt: "CALL: hold" if "s1" in prompt else "CALL: buy"),
            checkpoint,
        )
        loaded = load_elicitation(checkpoint)
        assert _flip_rate(loaded) == 0.0
        assert _second_position_rate(loaded) == 0.5

    def test_a_model_that_answers_by_position_flips_every_scenario(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "e.jsonl"
        _run(
            _council_items("s1", "expand", "hold") + _council_items("s2", "buy", "lease"),
            _Backend(reply=lambda prompt: "CALL: " + prompt.split("Second: ")[1].split(chr(10))[0]),
            checkpoint,
        )
        loaded = load_elicitation(checkpoint)
        assert _flip_rate(loaded) == 1.0
        assert _second_position_rate(loaded) == 1.0

    def test_an_all_balanced_corpus_has_no_rate_rather_than_a_zero(self, tmp_path: Path) -> None:
        """`BALANCED` is a legal call, so a corpus of them is legal too."""
        checkpoint = tmp_path / "e.jsonl"
        _run(
            _council_items("s1", "expand", "hold"),
            _Backend(reply=lambda prompt: "CALL: BALANCED"),
            checkpoint,
        )
        loaded = load_elicitation(checkpoint)
        assert _second_position_rate(loaded) is None
        assert _flip_rate(loaded) is None

    def test_a_resumed_council_run_re_issues_nothing_that_landed(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "e.jsonl"
        items = _council_items("s1", "expand", "hold") + _council_items("s2", "buy", "lease")
        _run(items[:3], _Backend(), checkpoint)

        second = _Backend()
        made = _run(items, second, checkpoint)
        assert second.item_ids == [items[3].item_id]
        assert [record.item_id for record in made] == [items[3].item_id]
        assert len(load_elicitation(checkpoint)) == 4


# --------------------------------------------------------------------------- #
# Family B
# --------------------------------------------------------------------------- #


def test_a_membership_record_round_trips(tmp_path: Path) -> None:
    checkpoint = tmp_path / "e.jsonl"
    items = [
        _item(
            "h01",
            MembershipAsk(role="treatment", block="MISSING"),
            construct="hinge",
            condition_label="pivotal",
        ),
        _item(
            "h01",
            MembershipAsk(role="control", block="MISSING"),
            construct="hinge",
            condition_label="matched",
        ),
    ]
    _run(items, _Backend(), checkpoint)

    loaded = load_elicitation(checkpoint)
    assert [record.ask for record in loaded] == [
        MembershipAsk(role="treatment", block="MISSING"),
        MembershipAsk(role="control", block="MISSING"),
    ]
    assert {record.condition_label for record in loaded} == {"pivotal", "matched"}
    assert {record.ask_kind for record in loaded} == {"membership"}


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


def test_a_council_prompt_that_does_not_fit_is_told_apart_too(tmp_path: Path) -> None:
    """The three statuses stay three for every family."""
    checkpoint = tmp_path / "e.jsonl"
    items = _council_items("s1", "expand", "hold")
    doomed = items[0].prompt
    backend = _Backend(
        lambda prompt, attempt: (
            PromptTooLongError("Prompt is too long")
            if prompt == doomed
            else CliError("the process died")
        )
    )
    records = _run(items, backend, checkpoint)
    assert {record.item_id: record.call_status for record in records} == {
        items[0].item_id: "prompt_too_long",
        items[1].item_id: "infrastructure",
    }
    assert len(backend.calls) == 2


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
# Attrition, and which arm it came from
# --------------------------------------------------------------------------- #


class TestExclusionCounts:
    """Three instruments were found on 2026-08-25 reporting exclusions with no
    arm breakdown, all three reading high on the treatment arm. These say the
    breakdown is available from the checkpoint and nothing else."""

    def test_the_denominator_is_counted_too(self, tmp_path: Path) -> None:
        """An exclusion total with no `ok` beside it hides its own size."""
        rows = exclusion_counts(_run(_items(3), _Backend(), tmp_path / "e.jsonl"))
        assert rows == [ExclusionRow("off", "ledger", "unaided", "ok", 3)]

    def test_every_status_is_broken_out_by_arm(self, tmp_path: Path) -> None:
        """The same item, overflowing in one arm and fitting in another.

        This is the asymmetry the design has to be able to see: the system
        prompt carries the skill body in `on` and nothing in `off`, so a long
        item can be excluded from one arm only, and the arms are then scored on
        different item sets.
        """
        checkpoint = tmp_path / "e.jsonl"
        items = _items(2)
        doomed = items[0].prompt

        _run(items, _Backend(), checkpoint)
        run_elicitation(
            items,
            build_arm("cot"),
            model="haiku",
            backend="claude",
            arena="dev",
            checkpoint=checkpoint,
            call=_Backend(
                lambda prompt, attempt: (
                    PromptTooLongError("Prompt is too long") if prompt == doomed else None
                )
            ),
            ledger=BudgetLedger(limit_usd=10.0),
            run_id="run-2",
            backoff=NO_WAIT,
        )

        assert exclusion_counts(load_elicitation(checkpoint)) == [
            ExclusionRow("cot", "ledger", "unaided", "ok", 1),
            ExclusionRow("cot", "ledger", "unaided", "prompt_too_long", 1),
            ExclusionRow("off", "ledger", "unaided", "ok", 2),
        ]

    def test_council_attrition_separates_the_two_orderings(self, tmp_path: Path) -> None:
        """An unpaired scenario shows up as two unequal ordering counts."""
        checkpoint = tmp_path / "e.jsonl"
        items = _council_items("s1", "expand", "hold")
        _run(
            items,
            _Backend(
                lambda prompt, attempt: (
                    CliError("the process died") if prompt == items[1].prompt else None
                )
            ),
            checkpoint,
        )
        assert exclusion_counts(load_elicitation(checkpoint)) == [
            ExclusionRow("off", "council", "AB", "ok", 1),
            ExclusionRow("off", "council", "BA", "infrastructure", 1),
        ]

    def test_the_overflow_union_is_reported_even_when_it_is_empty(self, tmp_path: Path) -> None:
        """A union assumed empty is the same claim with none of the evidence."""
        records = _run(_items(2), _Backend(), tmp_path / "e.jsonl")
        shared = common_item_set(records)
        assert shared.dropped == frozenset()
        assert shared.clusters_touched == frozenset()
        assert len(shared.kept) == 2
        assert shared.arms == ("off",)

    def test_an_item_overflowing_in_one_arm_leaves_every_arm(self, tmp_path: Path) -> None:
        """The repair for the one exclusion that correlates with the arm.

        The item fits in `off` and overflows in `cot`, so `off` has a record
        for it and `cot` does not. Scoring each arm on what survived in it
        would compare two different item sets.
        """
        checkpoint = tmp_path / "e.jsonl"
        items = _items(3)
        doomed = items[0].prompt

        _run(items, _Backend(), checkpoint)
        run_elicitation(
            items,
            build_arm("cot"),
            model="haiku",
            backend="claude",
            arena="dev",
            checkpoint=checkpoint,
            call=_Backend(
                lambda prompt, attempt: (
                    PromptTooLongError("Prompt is too long") if prompt == doomed else None
                )
            ),
            ledger=BudgetLedger(limit_usd=10.0),
            run_id="run-2",
            backoff=NO_WAIT,
        )

        loaded = load_elicitation(checkpoint)
        shared = common_item_set(loaded)

        assert shared.arms == ("cot", "off")
        assert shared.dropped == {items[0].item_id}
        assert shared.clusters_touched == {items[0].cluster_id}
        assert items[0].item_id not in shared.kept
        assert shared.kept == {items[1].item_id, items[2].item_id}

        # The row survives in `off`, which is exactly why the union is needed:
        # the arm that kept it would otherwise be scored on an extra item.
        surviving = [r for r in loaded if r.item_id == items[0].item_id and r.arm == "off"]
        assert len(surviving) == 1

    def test_the_union_reads_no_response(self) -> None:
        assert "response" not in {field.name for field in fields(CommonItemSet)}

    def test_counting_reads_no_response(self, tmp_path: Path) -> None:
        """Counting what dropped is not scoring what survived."""
        assert "response" not in {field.name for field in fields(ExclusionRow)}


class TestExclusionReport:
    """`exclusion_counts` computing the right numbers did not stop three
    instruments from publishing an aggregate with no arm breakdown -- the
    number existed and nothing printed it. These test the print, not the
    return value."""

    def _cot_and_off(self, tmp_path: Path) -> list[ElicitationRecord]:
        """`cot` overflows on one item and `off` fits everything: the case
        where `prompt_too_long` fires in one arm and is silent in the
        other, reused from `TestExclusionCounts`."""
        checkpoint = tmp_path / "e.jsonl"
        items = _items(2)
        doomed = items[0].prompt

        _run(items, _Backend(), checkpoint)
        run_elicitation(
            items,
            build_arm("cot"),
            model="haiku",
            backend="claude",
            arena="dev",
            checkpoint=checkpoint,
            call=_Backend(
                lambda prompt, attempt: (
                    PromptTooLongError("Prompt is too long") if prompt == doomed else None
                )
            ),
            ledger=BudgetLedger(limit_usd=10.0),
            run_id="run-2",
            backoff=NO_WAIT,
        )
        return load_elicitation(checkpoint)

    def test_a_status_silent_in_one_arm_still_prints_there(self, tmp_path: Path) -> None:
        """`off` never overflowed, so `exclusion_counts` has no row for it --
        the exact cell whose absence would hide the asymmetry between arms."""
        lines = format_exclusion_counts(self._cot_and_off(tmp_path))
        joined = "\n".join(lines)
        assert "off / ledger / unaided  (n=2)" in joined
        off_section = joined.split("off / ledger / unaided")[1]
        assert "prompt_too_long       0 / 2  (0.0%)" in off_section

    def test_every_rate_carries_its_raw_count(self, tmp_path: Path) -> None:
        """Never a rate alone: the count and the denominator sit beside it."""
        joined = "\n".join(format_exclusion_counts(self._cot_and_off(tmp_path)))
        assert "ok                    1 / 2  (50.0%)" in joined
        assert "prompt_too_long       1 / 2  (50.0%)" in joined
        assert "ok                    2 / 2  (100.0%)" in joined
        assert "prompt_too_long       0 / 2  (0.0%)" in joined

    def test_no_records_is_reported_rather_than_a_blank_table(self) -> None:
        assert format_exclusion_counts([]) == ["exclusion_counts: no records"]

    def test_print_exclusion_report_actually_prints(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Reading the return value is not the same as proving something
        prints it: this reads real stdout, captured by pytest."""
        records = self._cot_and_off(tmp_path)
        print_exclusion_report(records)
        captured = capsys.readouterr().out
        assert captured == "\n".join(format_exclusion_counts(records)) + "\n"
        assert "prompt_too_long       0 / 2  (0.0%)" in captured


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

    def test_a_line_that_is_not_an_object_is_refused(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "e.jsonl"
        checkpoint.write_text("[1, 2, 3]\n{}\n", encoding="utf-8")
        with pytest.raises(RunError, match="does not match the current ElicitationRecord"):
            load_elicitation(checkpoint)

    def test_a_council_row_missing_its_ordering_fails_loudly(self, tmp_path: Path) -> None:
        """The failure this whole union exists to make impossible to miss.

        Defaulting the absent field would score the row as an AB and put a
        second-position rate on record that no call supports.
        """
        checkpoint = tmp_path / "e.jsonl"
        _run(_council_items("s1", "expand", "hold"), _Backend(), checkpoint)

        rows = _rows(checkpoint)
        del _ask_block(rows[0])["ordering"]
        _write_rows(checkpoint, rows)

        with pytest.raises(RunError, match="ordering"):
            load_elicitation(checkpoint)

    def test_a_council_row_naming_one_course_twice_is_refused(self, tmp_path: Path) -> None:
        """The ask's own refusal reaches the loader, with the line that carried it."""
        checkpoint = tmp_path / "e.jsonl"
        _run(_council_items("s1", "expand", "hold"), _Backend(), checkpoint)

        rows = _rows(checkpoint)
        _ask_block(rows[0])["first_course"] = "hold"
        _write_rows(checkpoint, rows)

        with pytest.raises(RunError, match="both courses of this call ask are 'hold'"):
            load_elicitation(checkpoint)

    def test_a_row_whose_kind_disagrees_with_its_ask_block_is_refused(self, tmp_path: Path) -> None:
        """A council row relabelled ``scalar`` has no unit and no role to build one from."""
        checkpoint = tmp_path / "e.jsonl"
        _run(_council_items("s1", "expand", "hold"), _Backend(), checkpoint)

        rows = _rows(checkpoint)
        rows[0]["ask_kind"] = "scalar"
        _write_rows(checkpoint, rows)

        with pytest.raises(RunError, match="does not match the current ElicitationRecord"):
            load_elicitation(checkpoint)

    def test_an_unrecognised_field_in_the_ask_block_is_refused(self, tmp_path: Path) -> None:
        """The place an answer key would arrive if the loader shrugged at extras."""
        checkpoint = tmp_path / "e.jsonl"
        _run(_items(1), _Backend(), checkpoint)
        rows = _rows(checkpoint)
        _ask_block(rows[0])["expected"] = 42
        _write_rows(checkpoint, rows[:1])

        with pytest.raises(RunError, match="does not match the current ElicitationRecord"):
            load_elicitation(checkpoint)

    @pytest.mark.parametrize("bad", [None, "", "ab", 7])
    def test_a_council_row_whose_ordering_is_not_one_of_the_two_is_refused(
        self, tmp_path: Path, bad: object
    ) -> None:
        """Deleting the key was the one case the constructor happened to catch.

        These four are the cases it did not, and every one of them loaded
        clean until the ask started checking its own annotation at runtime.
        """
        checkpoint = tmp_path / "e.jsonl"
        _run(_council_items("s1", "expand", "hold"), _Backend(), checkpoint)
        rows = _rows(checkpoint)
        _ask_block(rows[0])["ordering"] = bad
        _write_rows(checkpoint, rows[:1])

        with pytest.raises(RunError, match="ordering is"):
            load_elicitation(checkpoint)

    def test_a_row_whose_condition_label_contradicts_its_ordering_is_refused(
        self, tmp_path: Path
    ) -> None:
        """For `council` they are one fact, so they are not allowed to differ."""
        checkpoint = tmp_path / "e.jsonl"
        _run(_council_items("s1", "expand", "hold"), _Backend(), checkpoint)
        rows = _rows(checkpoint)
        rows[0]["condition_label"] = "BA" if rows[0]["condition_label"] == "AB" else "AB"
        _write_rows(checkpoint, rows[:1])

        with pytest.raises(RunError, match="condition_label is"):
            load_elicitation(checkpoint)

    def test_a_row_with_no_schema_version_is_refused(self, tmp_path: Path) -> None:
        """No elicitation row predates the column, so a default would invent one."""
        checkpoint = tmp_path / "e.jsonl"
        _run(_items(1), _Backend(), checkpoint)
        rows = _rows(checkpoint)
        del rows[0]["schema_version"]
        _write_rows(checkpoint, rows[:1])

        with pytest.raises(RunError, match="does not match the current ElicitationRecord"):
            load_elicitation(checkpoint)

    def test_an_unknown_ask_kind_is_refused(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "e.jsonl"
        _run(_items(1), _Backend(), checkpoint)
        rows = _rows(checkpoint)
        rows[0]["ask_kind"] = "vibes"
        _write_rows(checkpoint, rows[:1])

        with pytest.raises(RunError, match="unknown ask_kind 'vibes'"):
            load_elicitation(checkpoint)

    def test_an_ask_that_is_not_an_object_is_refused(self, tmp_path: Path) -> None:
        checkpoint = tmp_path / "e.jsonl"
        _run(_items(1), _Backend(), checkpoint)
        rows = _rows(checkpoint)
        rows[0]["ask"] = "days"
        _write_rows(checkpoint, rows[:1])

        with pytest.raises(RunError, match="the 'ask' block is str"):
            load_elicitation(checkpoint)

    def test_every_family_survives_one_file(self, tmp_path: Path) -> None:
        """One checkpoint schema, and the loader dispatches per row.

        Checked against ``ASK_KINDS`` rather than against a literal list, so
        adding a family without teaching the loader about it fails here instead
        of at the first run.
        """
        checkpoint = tmp_path / "e.jsonl"
        asks: dict[str, Ask] = {
            "scalar": ScalarAsk(role="base", unit="days"),
            "membership": MembershipAsk(role="treatment", block="MISSING"),
            "call": CallAsk("AB", "expand", "hold", "CALL"),
        }
        assert set(asks) == set(ASK_KINDS)
        items = [
            _item(f"c{index}", ask, condition_label=_label_for(ask))
            for index, ask in enumerate(asks.values())
        ]
        _run(items, _Backend(), checkpoint)

        loaded = load_elicitation(checkpoint)
        assert [record.ask for record in loaded] == list(asks.values())
        assert [record.ask_kind for record in loaded] == list(ASK_KINDS)


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
