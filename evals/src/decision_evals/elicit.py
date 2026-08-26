"""Elicitation: the half of a run that generates, and cannot score.

The decision-quality track asks whether a governing fact changes what a model
says. That question needs two halves, and the whole design here is that they
are two: this module gets a response out of the model and writes it down, and
something downstream reads an answer out of that response.

**The record holds no answer and no score.** :class:`ElicitationRecord` stops
at ``response``. Every ask type below describes the shape of the question, and
none of them carries a key against which a response could be marked right or
wrong. There is nowhere on any of them for an answer key to arrive, so an
extractor reading these files is blind to what the answer was supposed to be
by construction rather than by discipline. That is
the ``probe_casefile`` precedent one step further: there the stored response
makes a scorer change free to re-check, and here it makes the generation itself
free to skip.

The loop itself is :func:`~decision_evals.runner._run_loop`, shared with
:func:`~decision_evals.runner.run_arm` rather than written again. The batch
drain in it took twelve trials producing three different checkpoints to get
right, and a second copy would be a second place to get it wrong.

## One loop, one checkpoint schema, and a closed union for what differs

Three instrument families elicit three different things, registered in
``notebook/2026-08-25-prediction-the-quality-venue-and-the-tau-rule.md``.
Family A asks for a quantity and the unit it is measured in. Family B asks
which candidate is named inside a required output block. Family C asks which
of two courses is recommended. The arm vocabularies differ as well: a scalar
triplet has a base, a treatment and a control, while ``council`` has two
orderings of one scenario and no base arm at all.

Everything about *making the call* is identical across the three, and
:func:`~decision_evals.runner._run_loop` is already generic over the item and
the record it produces. So the families share one loop, one checkpoint schema
and one loader, and the handful of fields that differ live behind a closed
union: :class:`ScalarAsk`, :class:`MembershipAsk`, :class:`CallAsk`.

**Every field the union moved came out with a narrower type than it went in
with.** ``role`` was a bare ``str`` on the record and is now a checked literal
reachable only through the ask. ``unit`` was required on the item type this one
replaces and is still required, on :class:`ScalarAsk`, which is now the only
place a unit can be set at all. A ``council`` item has no ``unit`` field to
fill in, where widening the item type would have made it optional and left an
extractor to guess whether a null unit meant a call or a scalar somebody forgot
to label. ``CallAsk.ordering`` is required by the same mechanism, so a council
record that cannot say which ordering produced it cannot be built and cannot be
loaded.

This follows the ``MovementThreshold``-over-``float`` decision in
``stats/track_h.py``, where a value carries which rule derived it so that it
cannot be scored against the wrong scale. The resemblance stops short of the
enforcement: every function there *that classifies movement* requires a
``MovementThreshold`` and will not type-check against a bare number, while the
extractor that will read these files has not been written and nothing refuses
anything on its behalf yet. What holds today is that the family is on every row
and the union is closed, so the cases an extractor has to handle are
enumerable, and an ``assert_never`` over :data:`Ask` **will** fail to
type-check when a family is added without it.

``role`` left the record because ``council`` has no base arm and no control
arm, so recording its BA ordering under ``role="control"`` would have written a
falsehood that reads back later as a fact. :class:`CallAsk` has no ``role``
field to put it in. ``triplet_id`` was renamed to ``cluster_id`` on the way,
because the resampling unit is a scenario for ``council`` and a triplet for
Family A, and ``stats/cluster.py`` already calls that column a cluster label.

## Where the ordering lives, and why the courses travel beside it

``council`` is scored on **which of the two printed courses the call names**,
and that per-record quantity is what this module has to make computable. Two
estimators are built on it and they are not the same statistic.

The **second-position rate** is the primary: the share of calls naming the
course printed second, a per-record marginal with an exact null at 0.5 under
balanced orderings. The **recommendation flip rate** is a secondary, paired per
scenario, and it is what the original registration named. It was superseded
because it has no floor: on an item whose two courses are genuinely even, a
model with no position dependence coin-flips within one ordering and lands near
0.5, which is also where a badly inconsistent model lands, so the statistic
cannot separate correct indifference from instability. That is the question
``council`` exists to ask. The entry that supersedes it is in
``docs/DECISIONS.md``, with the arithmetic.

The record serves both, deliberately: ``cluster_id`` with ``ordering`` pairs the
two records of one scenario for the flip rate, and ``first_course`` with
``second_course`` gives the position for the marginal. A superseded estimator
stays computable, because nothing here is deleted for having been replaced and
one checkpoint can be scored both ways.

Those two course identifiers sit on the record because **a record has to be
scoreable from the file alone**. Recovering the second course from ``ordering``
means opening the item definition, and needing the item definition is what
would stop a changed extractor from being re-run over a file instead of over
the quota.

None of this is an answer key. Family C has none: which course a model picks is
the measurement, and the printed order is the manipulation. ``second_course``
names one of the two courses the model may pick, so it is half of the option
menu, and the record says nothing about which half a correct answer would be.

## Two factors, and only one of them is the arm

Every row sits in a cell of a cross, and the two dimensions are independent.

``arm`` is the experimental condition from
:data:`~decision_evals.solvers.arms.ARM_NAMES`: which document is in the system
prompt, ``off`` through ``in_situ``. ``condition_label`` is the instrument's own
contrast: base against governing, pivotal against matched, AB against BA. One
call to :func:`run_elicitation` covers one arm over every condition, and the
resume key is ``(item_id, arm)``, so running the same items again under a
second arm fills the next column of the cross and re-issues nothing.

``council`` crosses cleanly. Its two orderings are a within-scenario
manipulation and the arms are a between-prompt one, so AB and BA each appear
under every arm, and the kill's arm comparison is a contrast of second-position
rates between two arms, at matched ordering. Nothing about AB/BA
needs a name in ``ARM_NAMES``, and nothing in ``ARM_NAMES`` needs to know about
orderings. Verified by running it: four arms over two scenarios in both
orderings fills eight cells, each carrying its own rows.

## Which records leave, and which arm they leave from

Three adversarial reviews on 2026-08-25 found the same defect in ``cascade``,
``hinge`` and ``council``: an exclusion correlated with competence, folded into a
primary, reading high on the treatment arm, and reported with no arm breakdown
so the attrition was invisible in the output. This section applies the same
three questions to the two exclusions this module can create. **Every exclusion
class here is reported by arm**, which the schema supports because ``arm`` and
``condition_label`` sit on the same row as ``call_status``, so a count of what
dropped needs no second file. :func:`exclusion_counts` is that count, and it
carries the ``ok`` rows too: an exclusion total with no denominator beside it
hides exactly what these three reviews found.

``ok``
    A response came back and the isolation receipt permitted the venue. This is
    the denominator.
``prompt_too_long``
    The assembled prompt does not fit the window.

    *What makes a record leave:* the length of ``item.prompt`` plus
    ``arm.system_prompt``. Both are fixed before the call, so nothing the model
    does can cause it and it cannot correlate with competence.

    *It does correlate with the arm.* The system prompt carries the skill body
    in ``on`` and ``in_situ`` and a matched document in ``placebo``, so a long item
    can overflow in those arms and fit in ``off``. The arms would then be scored
    on different item sets, and the items that overflow are the longest ones,
    which pushes the document-carrying arms **up** if length tracks difficulty.

    *Which makes it repairable rather than dangerous.* It is deterministic per
    (item, arm), so the overflowing set is knowable before any analysis: drop
    the union of items that overflow in **any** arm from **every** arm and the
    common item set is restored. :func:`common_item_set` computes that union
    and reports its size, including when it is empty. An empty union that was
    assumed rather than computed is the same claim with none of the evidence,
    and assuming it is how this class of attrition stays invisible.
``infrastructure``
    The call failed for a reason that clears on its own.

    *What makes a record leave:* a CLI failure. Intended as arm-independent
    noise, and mostly is.

    *One channel makes it behaviour-correlated,* so the claim is not that it is
    clean. A timeout or an output-length failure is a function of what the
    model produced, and verbosity is the exact channel that moved ``cascade``'s
    primary by 0.300 with the error rate unchanged. An ``infrastructure`` rate
    that differs across arms is therefore a measurement, not a nuisance, and
    its direction is unsigned: it depends on whether long responses score
    better, which is measured rather than assumed.

    *Retrying is the right answer and a resume does not do it.* The row
    occupies its ``(item_id, arm)`` key, so :func:`run_elicitation` counts the
    item as done and re-issues nothing. Verified by running it. Retrying means
    removing those rows from the checkpoint first; the checkpoint appends and
    never deduplicates, so a resume that re-issued them would put two rows on
    one key and double-count the item.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import ClassVar, Final, Literal, final, get_args

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

#: Which instrument family an ask belongs to, and the discriminator the loader
#: dispatches on. Written from the ask's own class, never authored by hand.
AskKind = Literal["scalar", "membership", "call"]

#: Which role in a scalar triplet an item plays.
ScalarRole = Literal["base", "treatment", "control"]

#: Which arm of a two-arm membership contrast an item plays. The reporting
#: names differ by construct, ``pivotal`` and ``matched`` for ``hinge`` against
#: ``foreclosing`` and ``effect`` for ``cascade``, and those live in
#: ``condition_label``.
MembershipRole = Literal["treatment", "control"]

#: Which of the two orderings of one ``council`` scenario a prompt printed.
Ordering = Literal["AB", "BA"]

#: The permitted values, read off the annotations above so the two cannot drift.
#: A ``Literal`` binds a type checker and says nothing at runtime, and every
#: value these fields ever hold on a resumed run arrived from JSON, where no
#: type checker has ever looked.
SCALAR_ROLES: Final[tuple[str, ...]] = get_args(ScalarRole)
MEMBERSHIP_ROLES: Final[tuple[str, ...]] = get_args(MembershipRole)
ORDERINGS: Final[tuple[str, ...]] = get_args(Ordering)


def _require_choice(value: object, allowed: tuple[str, ...], field: str) -> None:
    """Refuse a value outside the annotation's own set."""
    if value not in allowed:
        raise RunError(f"{field} is {value!r}, and the only values are {list(allowed)}")


def _require_text(value: object, field: str) -> None:
    """Refuse a blank where an identifier is needed.

    An empty ``block`` is the sharp case: it turns the extractor's prefix into
    a bare colon, which matches any line that starts with one.
    """
    if not isinstance(value, str) or not value.strip():
        raise RunError(f"{field} is {value!r}, and it has to be a non-empty string")


@final
@dataclass(frozen=True, slots=True)
class ScalarAsk:
    """Family A: a quantity, and what it is measured in.

    Attributes:
        role: Which role in the triplet this item plays.
        unit: What the number the model is being asked for is measured in.
            Recorded so the extractor downstream is told rather than guessing,
            and required, because a scalar elicitation with no unit is an
            authoring mistake and this is where it gets caught.
    """

    kind: ClassVar[AskKind] = "scalar"

    role: ScalarRole
    unit: str

    def __post_init__(self) -> None:
        _require_choice(self.role, SCALAR_ROLES, "role")
        _require_text(self.unit, "unit")


@final
@dataclass(frozen=True, slots=True)
class MembershipAsk:
    """Family B: which candidate is named inside a required output block.

    Carries the block and nothing about what belongs in it. Which candidate
    was planted is the answer key, it lives with the scorer, and matching the
    named text against it happens after this module is finished.

    Attributes:
        role: Which arm of the two-arm contrast this item plays.
        block: The output block the candidate has to be named inside. On the
            record so a file says what to read out of itself, which is what
            lets an extractor be rewritten and re-run over the checkpoint after
            the prompt template has moved on.
    """

    kind: ClassVar[AskKind] = "membership"

    role: MembershipRole
    block: str

    def __post_init__(self) -> None:
        _require_choice(self.role, MEMBERSHIP_ROLES, "role")
        _require_text(self.block, "block")


@final
@dataclass(frozen=True, slots=True)
class CallAsk:
    """Family C: which of two courses is recommended.

    Attributes:
        ordering: Which of the two orderings of this scenario the prompt
            printed. Required and never defaulted: it is the manipulation, and
            a record that cannot say which ordering it carried is a record
            neither estimator can be computed from.
        first_course: The identifier of the course printed first.
        second_course: The identifier of the course printed second. With
            ``first_course`` it is what a parsed call gets compared against, so
            a reply naming neither is tellable from one naming the first.
        block: The output block carrying the call. ``CALL`` in the current
            item templates, and read off the record instead of assumed by the
            extractor.
    """

    kind: ClassVar[AskKind] = "call"

    ordering: Ordering
    first_course: str
    second_course: str
    block: str

    def __post_init__(self) -> None:
        """Refuse two courses a call cannot be told apart by.

        ``ordering`` is checked here because a ``Literal`` is a promise to a
        type checker and a resumed run reads its orderings out of JSON, which
        no type checker has read. Before this check, ``null``, ``""``, ``"ab"``
        and ``7`` all loaded and every one of them is a record that cannot say
        which ordering produced it.

        One identifier used twice makes both estimators blind: every call reads
        as naming the second course, and no pair can ever read as a flip. An
        empty identifier does the same to any reply the extractor fails to
        parse. These are construction defects in the item, and this is the same
        class of refusal as ``prompt_too_long``: deterministic, so it is caught
        at the item instead of surviving into an analysis.
        """
        _require_choice(self.ordering, ORDERINGS, "ordering")
        _require_text(self.first_course, "first_course")
        _require_text(self.second_course, "second_course")
        _require_text(self.block, "block")
        if self.first_course == self.second_course:
            raise RunError(
                f"both courses of this call ask are {self.first_course!r}, so every "
                "call would score as a second-position call"
            )


#: What an item asks for. Closed on purpose: adding a family means adding a
#: variant here and a branch in :func:`_load_ask`, and the round-trip test over
#: :data:`ASK_KINDS` fails until both are done.
Ask = ScalarAsk | MembershipAsk | CallAsk

#: The union's members, for the runtime check in :func:`_record`. ``@final``
#: binds a type checker; a subclass of an ask type is still constructible at
#: runtime, and ``asdict`` reads the fields of the instance's own class, so a
#: subclass carrying an extra field writes that field to the checkpoint while
#: ``fields(ScalarAsk)`` still reports two.
ASK_TYPES: Final[tuple[type[Ask], ...]] = get_args(Ask)

#: Every kind there is, read off the union so the two cannot fall out of step.
ASK_KINDS: Final[tuple[AskKind, ...]] = tuple(variant.kind for variant in ASK_TYPES)


@dataclass(frozen=True, slots=True)
class ElicitationItem:
    """One (cluster, arm, repeat) elicitation.

    Carries no expected value, no arithmetic, no ``key`` block and no ``meta``
    block. There is nothing on this type, or on any :class:`Ask` it can hold,
    for an answer key to arrive in.

    Attributes:
        item_id: ``"<construct>|<cluster>|<arm label>|r<repeat>"``, and the
            column the checkpoint resumes on.
        cluster_id: The resampling unit's label. A triplet for Family A and a
            scenario for ``council``, and it travels on the item so the
            bootstrap never has to recover it from the id.
        condition_label: Which side of the instrument's own contrast this item
            sits on, in the words this construct's report uses: ``base`` against
            ``governing``, ``pivotal`` against ``matched``, ``AB`` against
            ``BA``. It is
            deliberately not called an arm. ``arm`` is the other factor
            entirely, and conflating the two is how a scorer ends up grouping
            orderings and calling them treatment conditions.
        ask: What the model is being asked to produce, and the family this
            item belongs to.
    """

    item_id: str
    construct: str
    cluster_id: str
    condition_label: str
    repeat: int
    ask: Ask
    prompt: str
    set_version: int


@dataclass(frozen=True)
class ElicitationRecord:
    """One call, and everything needed to re-derive an answer from it later.

    The response is stored whole. On 2026-08-12 a parser whitelist discarded
    every answer in a 365-call run and the records kept nothing to recover
    from, so the run had to be repeated; keeping the text means a changed
    extractor is re-run over the file instead of over the quota.

    Attributes:
        arm: Which experimental arm produced it, from
            :data:`~decision_evals.solvers.arms.ARM_NAMES`.
        ask_kind: Which instrument family, and the column the loader dispatches
            on to rebuild ``ask`` as its own type. It is a stored column rather
            than a property so that the field set of this class is the whole
            schema of a row, which is what the blindness tests read.
        ask: The item's ask, reaching the file whole so a record can be scored
            without opening the item definition it came from.
        concurrency: How many calls were in flight. Written on every row and
            never left to a default: the register of models measured to return
            different text under concurrency exists because that varied once,
            and a row that does not say cannot be excluded from a comparison.
        isolation_ok: Whether the CLI's own receipt was read and permitted the
            venue. ``False`` on a failed call, where no receipt arrived.
        call_status: ``ok``, ``infrastructure`` or ``prompt_too_long``.
        response: What the model said, verbatim. No answer is read out of it
            here, and no score is written beside it.
        schema_version: Required, with no default.
            :class:`~decision_evals.runner.RunRecord` defaults its copy to 1 so
            that a row written before the column existed loads describing
            itself accurately. No elicitation row predates this column, so the
            same reasoning points the other way here: a row that does not say
            which schema it is has not been written by this module, and a
            default would let it claim a version it never carried.
    """

    item_id: str
    construct: str
    cluster_id: str
    condition_label: str
    repeat: int
    ask_kind: AskKind
    ask: Ask
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
    schema_version: int

    conversation_id: str | None = None

    def __post_init__(self) -> None:
        """Refuse a record whose discriminator disagrees with its ask.

        Two columns that can disagree need something that stops them, and this
        is it. :func:`_record` reads the ask's own class attribute and
        :func:`load_elicitation` dispatches on the stored kind to pick the
        constructor, so neither path can build a mismatch; what this catches is
        a record assembled by hand somewhere downstream, where a council row
        labelled ``scalar`` would invite an extractor to parse a numeral out of
        a recommendation.
        """
        if self.ask_kind != self.ask.kind:
            raise RunError(
                f"ask_kind is {self.ask_kind!r} while the ask is a "
                f"{type(self.ask).__name__}, which is {self.ask.kind!r}"
            )
        if isinstance(self.ask, CallAsk) and self.condition_label != self.ask.ordering:
            raise RunError(
                f"condition_label is {self.condition_label!r} while the ordering is "
                f"{self.ask.ordering!r}. For ``council`` they are the same fact, and two "
                "columns holding one fact are two columns that can disagree."
            )


def run_elicitation(
    items: Sequence[ElicitationItem],
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

    def cost_of(item: ElicitationItem) -> tuple[str, float]:
        """The prompt to send and what to authorise for it.

        The prompt is on the item. It was written by whoever authored the
        cluster, and rendering it again here would make the string that was
        reviewed a different string from the one that is sent. That is also
        what keeps the ask out of the generation path: nothing in this module
        reads a field of :class:`Ask` to build a prompt.
        """
        amount = (
            expected_cost_usd
            if expected_cost_usd is not None
            else estimate_cost_usd(prompt_chars=len(item.prompt) + len(arm.system_prompt))
        )
        return item.prompt, amount

    def dispatch(
        item: ElicitationItem, prompt: str, backpressure: Backpressure
    ) -> ElicitationRecord:
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
            elapsed_of_record=lambda record: record.duration_ms / 1000.0,
            concurrency=concurrency,
            backoff=backoff,
        )


def _elicit_one(
    item: ElicitationItem,
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
    item: ElicitationItem,
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
    """Assemble a row. Every number on it comes from the call or is zero.

    The exact type of the ask is checked, not merely its interface. ``asdict``
    serialises the fields of the instance's own class, so a subclass of an ask
    type carrying an ``expected`` field would write the answer key into the
    checkpoint while ``fields(ScalarAsk)`` still reported two fields and every
    blindness test still passed. That was demonstrated against this module on
    2026-08-25 and this line is what closed it.
    """
    if type(item.ask) not in ASK_TYPES:
        raise RunError(
            f"{item.item_id} carries a {type(item.ask).__name__}, which is not one of "
            f"{[variant.__name__ for variant in ASK_TYPES]}. A subclass can hold a field "
            "the blindness tests do not read and write it to the checkpoint."
        )
    result = elicited.result if elicited else None
    return ElicitationRecord(
        item_id=item.item_id,
        construct=item.construct,
        cluster_id=item.cluster_id,
        condition_label=item.condition_label,
        repeat=item.repeat,
        ask_kind=item.ask.kind,
        ask=item.ask,
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


@dataclass(frozen=True, slots=True)
class ExclusionRow:
    """One cell of the attrition table: how many records, and from where.

    Attributes:
        call_status: Including ``ok``. A count of what dropped with no
            denominator beside it is what made the attrition invisible in the
            three instruments reviewed on 2026-08-25.
    """

    arm: str
    construct: str
    condition_label: str
    call_status: str
    count: int


def exclusion_counts(records: Sequence[ElicitationRecord]) -> list[ExclusionRow]:
    """Count records by arm, condition and status, so attrition cannot hide.

    Every published count of dropped records is meant to be broken out by arm.
    On 2026-08-25 three instruments were each found folding an exclusion
    correlated with competence into a primary, all three reading high on the
    treatment arm, and in all three the exclusion counts were reported with no
    arm breakdown. This function exists so that reporting the breakdown is the
    default and omitting it is a decision somebody has to make.

    It reads ``arm``, ``construct``, ``condition_label`` and ``call_status``,
    and never touches ``response``. Counting what dropped is not scoring what
    survived, and this module still cannot do the second.

    Breaking out by ``condition_label`` also shows an unpaired ``council``
    design, where the flip rate needs both orderings of a scenario and one of
    them dropped: the two ordering counts stop being equal. Nothing here
    refuses that, because one row cannot see the corpus it belongs to.

    Returns:
        One row per observed combination, in a deterministic order. Absent
        combinations are absent: a zero is a claim about a cell that was run,
        and this function cannot tell a cell that produced nothing from a cell
        nobody dispatched.
    """
    counts = Counter(
        (record.arm, record.construct, record.condition_label, record.call_status)
        for record in records
    )
    return [
        ExclusionRow(
            arm=arm, construct=construct, condition_label=label, call_status=status, count=count
        )
        for (arm, construct, label, status), count in sorted(counts.items())
    ]


def format_exclusion_counts(records: Sequence[ElicitationRecord]) -> list[str]:
    """Render :func:`exclusion_counts` as a table an arm cannot hide behind.

    ``exclusion_counts`` itself refuses to invent a row for a cell nobody
    dispatched, because it cannot tell that apart from a cell that ran and
    produced nothing. This function draws the line one step later: for every
    ``(arm, construct, condition_label)`` cell that *did* run -- it has at
    least one row -- every ``call_status`` seen anywhere in ``records`` is
    printed for it, zero included. A status that fires in one arm and is
    silent in another is exactly the shape the three reviews of 2026-08-25
    found, and a report that only prints non-empty rows hides it in precisely
    the arm where its absence is the finding.

    Every rate printed carries its raw count and its denominator beside it,
    never alone: ``n`` is the ``ok`` count plus every exclusion in the cell,
    counted here rather than assumed, so a reader never has to trust a
    percentage against a total they cannot see.

    Returns:
        One header line per cell naming the arm, the construct, the
        condition and ``n``, followed by one line per ``call_status`` in a
        deterministic order. Empty only when ``records`` is empty.
    """
    rows = exclusion_counts(records)
    if not rows:
        return ["exclusion_counts: no records"]

    cells = sorted({(row.arm, row.construct, row.condition_label) for row in rows})
    statuses = sorted({row.call_status for row in rows})
    counted = {
        (row.arm, row.construct, row.condition_label, row.call_status): row.count for row in rows
    }

    lines: list[str] = []
    for arm, construct, label in cells:
        total = sum(counted.get((arm, construct, label, status), 0) for status in statuses)
        lines.append(f"{arm} / {construct} / {label}  (n={total})")
        for status in statuses:
            count = counted.get((arm, construct, label, status), 0)
            rate = count / total if total else 0.0
            lines.append(f"  {status:<16} {count:>6} / {total}  ({rate:.1%})")
    return lines


def print_exclusion_report(records: Sequence[ElicitationRecord]) -> None:
    """Print :func:`format_exclusion_counts`, one line per call to :func:`print`.

    ``exclusion_counts`` computing the right numbers did not stop three
    instruments from publishing an aggregate with no arm broken out; the
    number existed and nothing printed it. This function is the call site:
    it is what turns the computed rows into something a run's summary
    actually shows, so the breakdown a reader sees is not conditioned on
    someone remembering to ask ``exclusion_counts`` for it separately.
    """
    for line in format_exclusion_counts(records):
        print(line)


@dataclass(frozen=True, slots=True)
class CommonItemSet:
    """The items every arm can be scored on, and what restoring that cost.

    ``prompt_too_long`` is deterministic per (item, arm) and the system prompt
    is longer in the arms carrying a document, so a long item can overflow in
    ``on``, ``in_situ`` and ``placebo`` while fitting in ``off``. Scoring each
    arm on whatever survived in it compares arms over different item sets, and
    the items that overflow are the longest, which pushes the document-carrying
    arms up wherever length tracks difficulty.

    The repair is to drop the union of items that overflowed in **any** arm
    from **every** arm. This type is that union, reported whether or not it is
    empty.

    Attributes:
        kept: The item ids every arm can be scored on.
        dropped: The item ids that overflowed somewhere, so they leave
            everywhere.
        clusters_touched: Clusters that lost at least one item. Dropping one
            arm of a triplet breaks the pairing the movement rule needs, so
            whether the rest of the cluster is still usable is the scorer's
            call and this names the clusters it has to make it for.
        arms: The arms these records cover, in sorted order. A union computed
            over one arm is not a union, and this is what says how many were
            in the room.
    """

    kept: frozenset[str]
    dropped: frozenset[str]
    clusters_touched: frozenset[str]
    arms: tuple[str, ...]


def common_item_set(records: Sequence[ElicitationRecord]) -> CommonItemSet:
    """Compute the item set every arm shares, and what it cost to restore.

    Reads ``item_id``, ``cluster_id``, ``arm`` and ``call_status``, and never
    touches ``response``.

    Returns:
        The union of overflowing items and the items that survive it. Both are
        returned even when nothing overflowed, because the number that matters
        is reported rather than inferred from its own absence.
    """
    dropped = {record.item_id for record in records if record.call_status == "prompt_too_long"}
    return CommonItemSet(
        kept=frozenset(record.item_id for record in records if record.item_id not in dropped),
        dropped=frozenset(dropped),
        clusters_touched=frozenset(
            record.cluster_id for record in records if record.item_id in dropped
        ),
        arms=tuple(sorted({record.arm for record in records})),
    )


def _load_ask(kind: object, payload: object) -> Ask:
    """Rebuild one row's ask as its own type.

    A missing required field arrives here as a ``TypeError`` from the dataclass
    constructor, which is the point of the exercise: ``CallAsk.ordering`` has
    no default, so a council row that does not say which ordering produced it
    fails at load instead of being counted as an AB. A row that parses but
    describes an item nothing can be scored from arrives as the
    :class:`~decision_evals.runner.RunError` its own ``__post_init__`` raises.
    :func:`load_elicitation` names the file and the line for both.
    """
    if not isinstance(payload, dict):
        raise TypeError(f"the 'ask' block is {type(payload).__name__}, expected an object")
    if kind == "scalar":
        return ScalarAsk(**payload)
    if kind == "membership":
        return MembershipAsk(**payload)
    if kind == "call":
        return CallAsk(**payload)
    raise TypeError(f"unknown ask_kind {kind!r}; expected one of {list(ASK_KINDS)}")


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
            row = dict(payload)
            ask = _load_ask(row.pop("ask_kind", None), row.pop("ask", None))
            records.append(ElicitationRecord(ask_kind=ask.kind, ask=ask, **row))
        except (TypeError, ValueError, RunError) as exc:
            raise RunError(
                f"{checkpoint}:{number} does not match the current ElicitationRecord "
                f"schema: {exc}\nMove the checkpoint aside and re-run rather than "
                "extracting from a subset."
            ) from exc
    return records
