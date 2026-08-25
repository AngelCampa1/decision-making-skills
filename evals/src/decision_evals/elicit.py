"""Scalar elicitation: the half of a run that generates, and cannot score.

Track H asks whether a governing fact moves a number the model states. That
question needs two halves, and the whole design here is that they are two:
this module gets a response out of the model and writes it down, and something
downstream reads a quantity out of that response.

**The record holds no quantity and no score.** :class:`ElicitationRecord` stops
at ``response``, and :class:`ScalarItem` carries no expected value and no
arithmetic. There is nowhere on either type for an answer key to arrive, so an
extractor reading these files is blind to what the answer was supposed to be by
construction rather than by discipline. That is the ``probe_casefile``
precedent one step further: every run there writes the model's full response
beside its score, which makes a scorer change re-checkable for nothing, and the
same property here also makes the *generation* unrepeatable-for-free rather
than the scoring.

The loop itself is :func:`~decision_evals.runner._run_loop`, shared with
:func:`~decision_evals.runner.run_arm` rather than written again. The batch
drain in it took twelve trials producing three different checkpoints to get
right, and a second copy would be a second place to get it wrong.

Three failure modes are told apart rather than pooled, and ``call_status``
carries the distinction into the file:

``ok``
    A response came back and the isolation receipt permitted the venue.
``infrastructure``
    The call failed for a reason that clears on its own. Retrying the item is
    the right answer.
``prompt_too_long``
    The assembled prompt does not fit the window. Deterministic, so it will not
    fit next time either: it is a construction defect in the item and it is
    recorded as one rather than retried.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from decision_evals.budget import BudgetLedger, estimate_cost_usd
from decision_evals.providers.claude_code import (
    AuthenticationError,
    CliError,
    Elicited,
    IsolationError,
    PromptTooLongError,
)
from decision_evals.runner import (
    Backoff,
    Backpressure,
    RunError,
    _call_with_backoff,
    _run_loop,
    completed_keys,
)
from decision_evals.solvers.arms import ArmPrompt
from decision_evals.telemetry import RECORD_SCHEMA_VERSION

#: How one isolated call is made. Injected so the loop is testable without a
#: model. It returns an :class:`~decision_evals.providers.claude_code.Elicited`
#: rather than a bare result, because a response whose receipt was never read
#: cannot be told apart from one produced in a venue the experiment forbids.
IsolatedCallFn = Callable[[str, str, bool], Elicited]

#: Which role in a triplet an item plays.
Role = Literal["base", "treatment", "control"]


@dataclass(frozen=True, slots=True)
class ScalarItem:
    """One (triplet, role, repeat) elicitation.

    Carries no expected value, no arithmetic, no ``key`` block and no ``meta``
    block. There is nothing on this type for an answer key to arrive in.

    Attributes:
        item_id: ``"<construct>|<triplet>|<role>|r<repeat>"``, and the column
            the checkpoint resumes on.
        triplet_id: The cluster label. The triplet is the unit of resampling,
            so it travels on the item rather than being recovered from the id.
        arm_label: What this role is called in this construct's report. Names
            differ between constructs while ``role`` does not, so the reporting
            name and the structural one are separate fields.
        unit: What the number the model is being asked for is measured in.
            Recorded here so the extractor downstream is told rather than
            guessing.
    """

    item_id: str
    construct: str
    triplet_id: str
    role: Role
    arm_label: str
    repeat: int
    unit: str
    prompt: str
    set_version: int


@dataclass(frozen=True)
class ElicitationRecord:
    """One call, and everything needed to re-derive a number from it later.

    The response is stored whole. On 2026-08-12 a parser whitelist discarded
    every answer in a 365-call run and the records kept nothing to recover
    from, so the run had to be repeated; keeping the text means a changed
    extractor is re-run over the file instead of over the quota.

    Attributes:
        arm: Which experimental arm produced it, from
            :data:`~decision_evals.solvers.arms.ARM_NAMES`.
        concurrency: How many calls were in flight. Written on every row and
            never left to a default: the register of models measured to return
            different text under concurrency exists because that varied once,
            and a row that does not say cannot be excluded from a comparison.
        isolation_ok: Whether the CLI's own receipt was read and permitted the
            venue. ``False`` on a failed call, where no receipt arrived.
        call_status: ``ok``, ``infrastructure`` or ``prompt_too_long``.
        response: What the model said, verbatim. No quantity is read out of it
            here, and no score is written beside it.
    """

    item_id: str
    construct: str
    triplet_id: str
    role: str
    arm_label: str
    repeat: int
    arm: str
    model: str
    backend: str
    arena: str
    set_version: int
    concurrency: int
    run_id: str
    call_status: str
    isolation_ok: bool
    cost_usd: float
    input_tokens: int
    output_tokens: int
    duration_ms: int
    response: str

    schema_version: int = RECORD_SCHEMA_VERSION
    conversation_id: str | None = None


def run_elicitation(
    items: Sequence[ScalarItem],
    arm: ArmPrompt,
    *,
    model: str,
    backend: str,
    arena: str,
    checkpoint: Path,
    call: IsolatedCallFn,
    ledger: BudgetLedger,
    run_id: str,
    concurrency: int = 1,
    backoff: Backoff | None = None,
    expected_cost_usd: float | None = None,
) -> list[ElicitationRecord]:
    """Elicit one arm over a set of items, resuming from any checkpoint.

    Args:
        model: The tier to ask for. The record carries the id the backend
            resolved it to, because ``haiku`` is not a version.
        backend: Which harness the model was reached through. Together with
            ``arena`` and the resolved model it is what identifies a venue, and
            one binary has already turned out to serve three of them.
        run_id: What ties these rows to the run that made them.
        expected_cost_usd: What to authorise per call. ``None`` derives it from
            the length of the prompt about to be sent.
        concurrency: How many calls may be in flight. ``1`` is the sequential
            loop.
        backoff: How rate limits are waited out, shared across every worker.

    Returns:
        The records produced by this invocation. Rows already on disk are left
        where they are rather than re-read, so the count is what this call
        spent.

    Raises:
        RunError: The budget was reached, authentication failed, or
            ``concurrency`` was not positive. The checkpoint survives all
            three.
        IsolationError: The CLI declared a capability the experiment does not
            permit. The run stops rather than recording a response from a venue
            it was not measuring.
    """
    if concurrency < 1:
        raise RunError(f"concurrency must be at least 1, got {concurrency}")

    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    done = completed_keys(checkpoint)
    pending = [item for item in items if (item.item_id, arm.arm) not in done]

    def cost_of(item: ScalarItem) -> tuple[str, float]:
        """The prompt to send and what to authorise for it.

        The prompt is on the item. It was written by whoever authored the
        triplet, and rendering it again here would make the string that was
        reviewed a different string from the one that is sent.
        """
        amount = (
            expected_cost_usd
            if expected_cost_usd is not None
            else estimate_cost_usd(prompt_chars=len(item.prompt) + len(arm.system_prompt))
        )
        return item.prompt, amount

    def dispatch(item: ScalarItem, prompt: str, backpressure: Backpressure) -> ElicitationRecord:
        return _elicit_one(
            item,
            arm,
            model=model,
            backend=backend,
            arena=arena,
            call=call,
            prompt=prompt,
            run_id=run_id,
            concurrency=concurrency,
            backpressure=backpressure,
        )

    with checkpoint.open("a", encoding="utf-8") as handle:
        return _run_loop(
            pending,
            cost_of=cost_of,
            dispatch=dispatch,
            ledger=ledger,
            handle=handle,
            to_row=asdict,
            cost_of_record=lambda record: record.cost_usd,
            concurrency=concurrency,
            backoff=backoff,
        )


def _elicit_one(
    item: ScalarItem,
    arm: ArmPrompt,
    *,
    model: str,
    backend: str,
    arena: str,
    call: IsolatedCallFn,
    prompt: str,
    run_id: str,
    concurrency: int,
    backpressure: Backpressure,
) -> ElicitationRecord:
    """One call, and the four things that can come back from it.

    A rate limit never reaches here: ``_call_with_backoff`` waits it out, and
    the shared pause means a wall one worker meets is a wall every worker
    observes. What arrives is a response, a revoked credential, a venue the
    experiment forbids, a prompt that does not fit, or an ordinary failure.

    The first three stop the run. Authentication does because a revoked token
    returns a well-formed refusal on every call, so retrying it is a few
    hundred identical failures. Isolation does because the call would have
    succeeded and what is wrong is what it was measuring. The last two are
    recorded and the run continues, under statuses that mean opposite things
    about the corpus.
    """
    try:
        elicited = _call_with_backoff(arm, call=call, prompt=prompt, backpressure=backpressure)
    except AuthenticationError as exc:
        raise RunError(
            f"authentication failed at {item.item_id}. The run is stopped rather than "
            f"recording the failures: {exc}"
        ) from exc
    except IsolationError:
        raise
    except PromptTooLongError as exc:
        return _record(
            item,
            arm,
            model=model,
            backend=backend,
            arena=arena,
            run_id=run_id,
            concurrency=concurrency,
            call_status="prompt_too_long",
            elicited=None,
            response=str(exc),
        )
    except CliError as exc:
        return _record(
            item,
            arm,
            model=model,
            backend=backend,
            arena=arena,
            run_id=run_id,
            concurrency=concurrency,
            call_status="infrastructure",
            elicited=None,
            response=str(exc),
        )
    return _record(
        item,
        arm,
        model=model,
        backend=backend,
        arena=arena,
        run_id=run_id,
        concurrency=concurrency,
        call_status="ok",
        elicited=elicited,
        response=elicited.result.text,
    )


def _record(
    item: ScalarItem,
    arm: ArmPrompt,
    *,
    model: str,
    backend: str,
    arena: str,
    run_id: str,
    concurrency: int,
    call_status: str,
    elicited: Elicited | None,
    response: str,
) -> ElicitationRecord:
    """Assemble a row. Every number on it comes from the call or is zero."""
    result = elicited.result if elicited else None
    return ElicitationRecord(
        item_id=item.item_id,
        construct=item.construct,
        triplet_id=item.triplet_id,
        role=item.role,
        arm_label=item.arm_label,
        repeat=item.repeat,
        arm=arm.arm,
        model=result.model if result else model,
        backend=backend,
        arena=arena,
        set_version=item.set_version,
        concurrency=concurrency,
        run_id=run_id,
        call_status=call_status,
        isolation_ok=elicited is not None,
        cost_usd=result.cost_usd if result else 0.0,
        input_tokens=result.input_tokens if result else 0,
        output_tokens=result.output_tokens if result else 0,
        duration_ms=result.duration_ms if result else 0,
        response=response,
        schema_version=RECORD_SCHEMA_VERSION,
        conversation_id=(result.session_id or None) if result else None,
    )


def load_elicitation(checkpoint: Path) -> list[ElicitationRecord]:
    """Read a checkpoint back for extraction.

    A JSON parse failure on the *final* line is tolerated: a run killed
    mid-write leaves a partial line, and that is both expected and
    recoverable. Everything else is refused, including a well-formed line that
    does not fit the current schema. Skipping those silently would mean adding
    a column makes every earlier record disappear, and the extraction then
    reports a run that did not happen.

    Raises:
        RunError: A record does not match the current schema, or a line is
            unparseable somewhere other than at the end of the file.
    """
    if not checkpoint.exists():
        return []

    lines = checkpoint.read_text(encoding="utf-8").splitlines()
    records: list[ElicitationRecord] = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            if number == len(lines):
                break  # a partial final write; the run was killed here
            raise RunError(
                f"{checkpoint}:{number} is not JSON and is not the last line, so it is "
                f"corruption rather than an interrupted write: {exc}"
            ) from exc
        try:
            records.append(ElicitationRecord(**payload))
        except TypeError as exc:
            raise RunError(
                f"{checkpoint}:{number} does not match the current ElicitationRecord "
                f"schema: {exc}\nMove the checkpoint aside and re-run rather than "
                "extracting from a subset."
            ) from exc
    return records
