"""The bridge between GEPA's search and this repository's scored environment.

GEPA optimises text against a scored batch. This package already has the batch
and the scorer: :func:`~decision_evals.generators.generate.generate` mints items
with computed ground truth, :func:`~decision_evals.solvers.arms.build_arm`
renders one into a prompt, and
:func:`~decision_evals.scorers.answer.score_item` says whether the reply was
right and, when it was not, why. What was missing is the adapter that joins
them, and four things it has to do that the protocol does not ask for.

**The body goes through the ``candidate`` arm, which is the ``on`` arm's code
path.** A generated body reaching the model any other way would confound
authorship with delivery, and authorship is the one comparison the study exists
to make. :data:`~decision_evals.solvers.arms.FORMAT_CONTRACT` is therefore in
the prompt for every candidate, which matters more here than anywhere: the
Phase 0 smoke run watched GEPA win its entire gain by restating a format
contract, and an engine that can only do that would show a number saying
nothing about decision quality.

**Every batch is checked against the seed firewall before a call goes out.** An
engine that scores on a holdout item has fitted the test set, and nothing
undoes it afterwards.

**Every candidate is recorded before it is scored.** A search whose record is
written by the winner is a search that cannot be audited.

**``propose_new_texts`` is set to ``None`` explicitly.** The protocol documents
it as optional with an engine-supplied default; ``reflective_mutation.py`` reads
the attribute with no ``getattr`` default, so an adapter that simply omits it
raises on every proposal, and GEPA catches the error, retries, gives up, and
exits zero reporting the seed as the winner. That is a search that never
searched wearing the output of one that did. The one-line fix is here and
:func:`~decision_evals.evolution.lineage.assert_searched` is the check that
catches it when some other engine does the same thing differently.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from decision_evals.budget import NestedBudget
from decision_evals.evolution.holdout import assert_evolvable
from decision_evals.evolution.lineage import Candidate, append_candidate, body_sha
from decision_evals.evolution.venues import Venue, call_fn
from decision_evals.generators.generate import Item
from decision_evals.runner import CallFn, RunRecord, completed_keys, load_records, run_arm
from decision_evals.scorers.answer import score_item
from decision_evals.solvers.arms import build_arm, render_item

if TYPE_CHECKING:  # pragma: no cover - types only, and gepa is not a gate dependency
    from gepa.core.adapter import EvaluationBatch

#: The component GEPA mutates. One component, because the artefact under study
#: is one skill file; a multi-component candidate would be a different
#: experiment and its winner would not be installable as a skill.
COMPONENT: Final = "skill_md"

#: The columns that identify a call once one checkpoint holds many candidates.
#: ``(item_id, arm)`` is what every published run resumed on and is wrong here
#: twice over: every candidate scores in the ``candidate`` arm, and ``item_id``
#: carries no seed.
RESUME_FIELDS: Final[tuple[str, ...]] = ("item_id", "arm", "candidate_sha", "seed")


class AdapterError(RuntimeError):
    """The adapter cannot evaluate what it was handed."""


@dataclass(frozen=True, slots=True)
class Trace:
    """One item's outcome, in the shape reflection needs to say something useful.

    Carries the failure *cause* rather than only the score.
    :func:`~decision_evals.scorers.answer.score_item` already distinguishes a
    wrong answer from an unparseable one from an infrastructure zero, and a
    reflector told only "0.0" will happily rewrite the reasoning guidance of a
    skill whose real problem was that the reply had no final line.
    """

    item_id: str
    seed: int
    question: str
    rendered: str
    response: str
    expected: str
    parsed: str | None
    parse_status: str
    zero_cause: str | None
    correct: bool

    @property
    def score(self) -> float:
        return 1.0 if self.correct else 0.0


def _evaluation_batch() -> Any:
    """Import GEPA's return type at call time.

    ``gepa`` lives in the ``evolve`` dependency group, which ``de check`` never
    installs: the engines are the *subject* of the study and must not become a
    dependency of the instrument. So this module imports without them and says
    something useful when a run is attempted without them.

    Raises:
        AdapterError: GEPA is not installed.
    """
    try:
        from gepa.core.adapter import EvaluationBatch as Batch
    except ImportError as exc:  # pragma: no cover - exercised by the import guard test
        raise AdapterError(
            "gepa is not installed. It is in the `evolve` dependency group, which the "
            "gate deliberately does not install: run `python -m uv sync --group evolve`."
        ) from exc
    return Batch


class DecisionAdapter:
    """A :class:`gepa.core.adapter.GEPAAdapter` over this repository's corpus.

    Structural rather than declared: GEPA's adapter is a ``Protocol``, and
    inheriting from it would make ``gepa`` an import-time dependency of a module
    the gate loads.

    Args:
        venue: Where the *candidate* is scored. The model the skill is a skill
            for, which is not the model that writes it.
        checkpoint: One JSONL for the whole search. Resume is keyed on
            :data:`RESUME_FIELDS`, so a re-run re-scores nothing it already
            scored and two candidates in one file stay two candidates.
        lineage: Where every candidate is appended, scored or not.
        budget: Charged per call across all three of its scopes. On these
            venues it is the call cap and the clock that stop a search.
        git_sha: The commit the harness is at. Recorded on every candidate,
            because a candidate is a function of the scorer as much as of the
            engine.
        call: How a call is made. ``None`` derives it from ``venue``, which is
            what a real run wants. It is injectable so a test can score a
            candidate without a server, and so the mock venue can be handed the
            answer key it needs to be an oracle.
    """

    #: Explicitly ``None``. See the module docstring: the attribute is read
    #: without a default, so omitting it silently disables mutation.
    propose_new_texts = None

    def __init__(
        self,
        *,
        venue: Venue,
        checkpoint: Path,
        lineage: Path,
        budget: NestedBudget,
        git_sha: str,
        engine: str = "gepa",
        reflector_model: str | None = None,
        call: CallFn | None = None,
        now: Any = None,
    ) -> None:
        self.venue = venue
        self.call = call or call_fn(venue)
        self.checkpoint = checkpoint
        self.lineage = lineage
        self.budget = budget
        self.git_sha = git_sha
        self.engine = engine
        self.reflector_model = reflector_model
        self._now = now or (lambda: dt.datetime.now(dt.UTC).isoformat(timespec="seconds"))
        self.generation = 0
        self._seen: dict[str, str] = {}
        self._recorded: set[str] = set()

    # -- the protocol -------------------------------------------------------

    def evaluate(
        self,
        batch: list[Item],
        candidate: dict[str, str],
        capture_traces: bool = False,
    ) -> EvaluationBatch[Trace, str]:
        """Score one candidate body on one batch of items.

        Raises:
            AdapterError: The candidate has no ``skill_md``, or the batch is
                empty. Both would otherwise produce a clean zero, and a zero
                that means "nothing ran" is indistinguishable from a zero that
                means "everything was wrong".
            HoldoutBreachError: The batch carries a seed no engine may see.
            BudgetError: The run is out of calls, seconds or dollars.
        """
        traces = self.score(candidate.get(COMPONENT) or "", batch)
        batch_type = _evaluation_batch()
        return batch_type(
            outputs=[trace.response for trace in traces],
            scores=[trace.score for trace in traces],
            trajectories=traces if capture_traces else None,
            # What the *engine* spent, which is one metric evaluation per item.
            # The calls this harness actually made is a smaller number whenever a
            # candidate is re-evaluated on items it already covers, and reporting
            # that as the engine's spend means `max_metric_calls` never falls and
            # the search does not terminate. The two counters answer different
            # questions and both are kept: the ledger is charged the calls, GEPA
            # is told the evaluations.
            num_metric_calls=len(batch),
        )

    # -- the scored environment, which is not GEPA's ------------------------

    def score(self, body: str, batch: Sequence[Item]) -> list[Trace]:
        """Score one body on one batch, and record that it happened.

        Everything an engine needs and nothing shaped like any particular
        engine's protocol. :meth:`evaluate` is a wrapper for GEPA and
        :mod:`decision_evals.evolution.skillopt_env` is a wrapper for SkillOpt;
        both go through here, so the firewall, the budget, the resume key and
        the lineage cannot be right for one engine and absent for the other.

        Raises:
            AdapterError: An empty body, or an empty batch. Both would otherwise
                produce a clean zero, and a zero that means "nothing ran" is
                indistinguishable from a zero that means "everything was wrong".
            HoldoutBreachError: The batch carries a seed no engine may see.
            BudgetError: The run is out of calls, seconds or dollars.
        """
        if not body or not body.strip():
            raise AdapterError(
                f"this candidate has no {COMPONENT!r} text. An empty body scores like a "
                "missing skill and would be recorded as a candidate that lost."
            )
        if not batch:
            raise AdapterError("an empty batch scores zero for reasons that are not the skill")

        assert_evolvable(item.seed for item in batch)

        sha = body_sha(body)
        # Authorise the calls this evaluation will actually make, not the size
        # of the batch. An engine re-evaluates a candidate on batches it has
        # already covered, those items resume off the checkpoint for nothing,
        # and charging the budget for them stopped a search at its per-child cap
        # after two candidates -- a refusal for spending that never happened.
        self.budget.assert_can_afford(calls=_pending(batch, self.checkpoint, sha))

        records = run_arm(
            list(batch),
            build_arm("candidate", skill_body=body),
            model=self.venue.model,
            checkpoint=self.checkpoint,
            call=self.call,
            ledger=self.budget.run,
            candidate_sha=sha,
            resume_fields=RESUME_FIELDS,
        )
        self.budget = self.budget.record(
            sum(record.cost_usd for record in records),
            calls=len(records),
            seconds=sum(record.duration_ms for record in records) / 1000.0,
        )

        # `run_arm` returns what it *made*, and an engine re-evaluates the same
        # candidate on overlapping batches all the time: the base program on the
        # valset, then minibatches drawn from it. Those calls resume rather than
        # re-run, so the returned list is short by exactly the items that were
        # already scored. The traces have to come off the checkpoint.
        traces = _traces(batch, load_records(self.checkpoint), sha)
        self._record_candidate(body, sha, batch, [trace.score for trace in traces])
        return traces

    def make_reflective_dataset(
        self,
        candidate: dict[str, str],
        eval_batch: EvaluationBatch[Trace, str],
        components_to_update: list[str],
    ) -> Mapping[str, Sequence[Mapping[str, Any]]]:
        """Turn scored traces into the examples the reflector reads.

        Only the losses, and at most :data:`REFLECTION_EXAMPLES` of them. A
        reflector shown a batch that is mostly right rewrites what is already
        working, and the reflector here is a hosted model on a free tier whose
        context is the binding constraint before its judgement is.

        Feedback names the *cause*. "wrong answer" and "no final ANSWER line"
        call for different edits, and the scorer already knows which happened.

        Raises:
            AdapterError: Traces were not captured, or a component was requested
                that this adapter does not own. Returning an empty dataset for
                either would read as "nothing to learn from" and let the search
                run on proposing nothing.
        """
        unknown = [name for name in components_to_update if name != COMPONENT]
        if unknown:
            raise AdapterError(
                f"this adapter owns {COMPONENT!r} and was asked to update {unknown}. "
                "A skill is one file; a candidate with more components would not install."
            )
        if eval_batch.trajectories is None:
            raise AdapterError(
                "reflection was asked for without captured traces, so there is nothing "
                "to reflect on. Pass capture_traces=True."
            )

        losses = [trace for trace in eval_batch.trajectories if not trace.correct]
        examples = [
            {
                "Inputs": trace.rendered,
                "Generated Outputs": trace.response,
                "Feedback": _feedback(trace),
            }
            for trace in losses[:REFLECTION_EXAMPLES]
        ]
        if not examples:
            examples = [
                {
                    "Inputs": "(no failures in this batch)",
                    "Generated Outputs": "",
                    "Feedback": (
                        "Every item in this batch was answered correctly. Any change risks "
                        "losing that; prefer a smaller edit, or none."
                    ),
                }
            ]
        return {COMPONENT: examples}

    # -- bookkeeping --------------------------------------------------------

    def _record_candidate(
        self, body: str, sha: str, batch: Sequence[Item], scores: Sequence[float]
    ) -> None:
        """Append this candidate to the lineage, once.

        Re-entered on every evaluation, and an engine evaluates the same
        candidate many times -- the base program on the valset, then minibatches
        drawn from it. Appending each time produced a lineage of 4,665 lines for
        a search of two candidates, so a body already recorded is skipped and the
        first score it got is the one on file.

        ``accepted`` is False here without exception. Acceptance is the engine's
        decision and it is taken *after* the score comes back, so recording it
        at evaluation time would be recording a guess. The run's driver resolves
        the winner from the body the engine hands back.

        **``parent_sha`` is proposal order, not observed descent.** GEPA does not
        report which candidate a proposal was mutated from, so what this records
        is the previously recorded distinct candidate. It is right whenever the
        search moves forward and wrong whenever it branches back to an earlier
        point on the frontier. SkillOpt reports parentage and will not need the
        approximation; until an engine says otherwise, read the field as order.
        """
        if sha in self._recorded:
            return
        parent = self._seen.get(COMPONENT)
        append_candidate(
            self.lineage,
            Candidate(
                candidate_sha=sha,
                parent_sha=None if self.generation == 0 else parent,
                generation=self.generation,
                engine=self.engine,
                target_model=self.venue.model,
                reflector_model=self.reflector_model,
                seeds=tuple(sorted({item.seed for item in batch})),
                n_items=len(batch),
                score=sum(scores) / len(scores) if scores else None,
                accepted=False,
                git_sha=self.git_sha,
                created_at=self._now(),
                body=body,
            ),
        )
        self._recorded.add(sha)
        self._seen[COMPONENT] = sha
        self.generation += 1
        self.budget = self.budget.start_child()


#: How many losing items the reflector is shown per proposal.
REFLECTION_EXAMPLES: Final = 5


def _feedback(trace: Trace) -> str:
    """One sentence a reflector can act on, naming the cause rather than the score.

    The truncation branch is the reason this reads the cause and not the parse.
    A reply the output cap stopped has no answer line, so it used to arrive here
    as "the reply did not end with a parseable line" and the reflector was
    pointed at the format instructions. Truncation is arm-dependent and
    concentrates on the arm whose document makes the model reason longest, so
    that feedback pushes hardest on the arm that reasoned most, for a fault the
    skill cannot fix.
    """
    if trace.zero_cause == "infrastructure":
        return (
            "This item never got an answer back from the venue. Nothing about the skill "
            "caused it; ignore this example."
        )
    if trace.zero_cause == "output_truncated":
        return (
            "The reply ran out of output budget while still reasoning and never got as far "
            "as an answer line, so it scored zero without stating a choice. The format "
            "instructions are not what failed. What would have helped is reaching a "
            f"decision in fewer tokens. The correct option was {trace.expected!r}."
        )
    if trace.parsed is None:
        return (
            "The reply did not end with a parseable 'ANSWER: <option>' line, so it scored "
            f"zero whatever it argued. The correct option was {trace.expected!r}."
        )
    return (
        f"The reply chose {trace.parsed!r}. The facts support {trace.expected!r}. "
        "The option list was fixed and both were on it."
    )


def _pending(batch: Sequence[Item], checkpoint: Path, sha: str) -> int:
    """How many of these items this candidate has not been scored on yet.

    The same key :func:`~decision_evals.runner.run_arm` resumes on, read here so
    the budget is asked to authorise the same work the runner is about to do.
    """
    done = completed_keys(checkpoint, RESUME_FIELDS)
    return sum(1 for item in batch if (item.item_id, "candidate", sha, str(item.seed)) not in done)


def _traces(batch: Sequence[Item], records: Sequence[RunRecord], sha: str) -> list[Trace]:
    """Line up one candidate's records against the items that produced them.

    Records are written in completion order and a checkpoint holds every
    candidate, while GEPA requires ``len(trajectories) == len(batch)`` in
    ``batch`` order. So this is a join on the three columns that identify a
    call, not a zip: ``item_id`` alone names a different scenario under a
    different seed, and names one row per candidate on top of that.

    Raises:
        AdapterError: An item with no record. A short trajectory list is a
            protocol violation GEPA reports as an unrelated index error several
            frames away.
    """
    by_key = {
        (record.candidate_sha, record.seed, record.item_id): record
        for record in records
        if record.candidate_sha == sha
    }
    traces: list[Trace] = []
    for item in batch:
        record = by_key.get((sha, item.seed, item.item_id))
        if record is None:
            raise AdapterError(
                f"no record for {item.item_id} at seed {item.seed} under candidate "
                f"{sha[:12]}. The batch and the trajectories have to line up one to one, "
                "and a missing row is a wrong score rather than a missing one."
            )
        # `stop_reason` travels with the response for the same reason
        # `infrastructure_error` does: this re-derives the score from a
        # committed row, and a re-derivation that drops an input lands on a
        # different cause than the row carries.
        score = score_item(
            item,
            record.response,
            infrastructure_error=record.zero_cause == "infrastructure",
            stop_reason=record.stop_reason,
        )
        traces.append(
            Trace(
                item_id=item.item_id,
                seed=item.seed,
                question=item.question,
                rendered=render_item(item),
                response=record.response,
                expected=item.answer,
                parsed=score.parsed.value,
                parse_status=score.parsed.status,
                zero_cause=score.zero_cause,
                correct=score.correct,
            )
        )
    return traces
