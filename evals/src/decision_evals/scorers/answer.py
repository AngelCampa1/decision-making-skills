"""Answer parsing and scoring.

Harbor's discipline, adopted wholesale: the verifier is tested against fixtures
of known-correct, known-wrong, paraphrased and boundary responses *before* it is
trusted, and every zero score is classified rather than assumed to be a model
failure. A verifier defect and a model failure look identical in the aggregate,
and only one of them is a finding.

Two parsing decisions are worth defending, because both cost us apparent
accuracy and both are deliberate.

**No fallback search.** When the ``ANSWER:`` line is missing, the response is a
parse failure even if an option is clearly named in the prose. Recovering it
would be easy and would corrupt the experiment: the format contract is in every
arm, so recovery rates would differ by arm in a way that has nothing to do with
decision quality, and the format-integrity guard would stop measuring anything.

**Ambiguity is a distinct outcome, not a coin flip.** A response naming two
options is not half correct. It is reported separately so it cannot be quietly
absorbed into either the numerator or the denominator.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

from decision_evals.generators.generate import Item

ParseStatus = Literal["parsed", "no_answer_line", "unlisted_option", "ambiguous"]

#: Why an item scored zero. The first four are assigned automatically; the rest
#: require a human reading the trace, and exist so that "we did not look" is
#: distinguishable from "we looked and it was the model".
#:
#: ``agent_wrong`` is therefore **provisional until a trace is read**. On the
#: first full control run all fifteen zeros were automatically labelled
#: ``agent_wrong`` and all fifteen turned out to be ``item_defect`` -- the
#: model's answer was defensible and the ground truth was not. Treating the
#: automatic label as a finding would have reported a 5% agent error rate that
#: did not exist.
#:
#: ``item_defect`` is separate from ``verifier_defect`` on purpose. Harbor's
#: ontology assumes fixed tasks and folds both into the verifier, but here the
#: parser and the comparison were correct and the *item* was wrong, and the two
#: have completely different fixes: one is a code change, the other is a
#: template change and a re-blessed golden.
#:
#: ``output_truncated`` is the fourth automatic cause, added 2026-09-03. It
#: splits off the reply that produced **no answer line at all** because the
#: output cap stopped it, which until then arrived as ``format_violation``
#: beside a reply that reached the end of its own argument and got the format
#: wrong. The two have nothing in common: a format violation is about the
#: skill's instructions and a truncation is about the token budget the run was
#: given. It is arm-dependent, which is what makes it worth a code of its own,
#: and the figures behind that are in
#: ``notebook/2026-09-03-a-thinking-model-spent-its-whole-budget-reasoning.md``
#: rather than here.
#:
#: **The boundary is ``no_answer_line`` and nothing wider.** A reply that wrote
#: a complete answer line naming something off the menu stays a
#: ``format_violation`` however it stopped, because it demonstrably reached an
#: answer line and the cap fell after it. The 87 ``ANSWER: monitor /think`` rows
#: below are that shape, on this venue, on a verbose thinking model, and they
#: are already classified ``verifier_defect``. A cap-hit ``unlisted_option``
#: therefore keeps the cause it had, at the cost of reading a reply cut off
#: mid-option as a format violation. That trade is deliberate: it holds every
#: existing cause's meaning fixed, and no field distinguishes the two readings.
#:
#: **This does not relabel a committed record.** A row written before this date
#: carries ``stop_reason`` empty, so its cause cannot be re-derived and it keeps
#: the ``format_violation`` it was scored with, the same rule the control token
#: below follows. One checkpoint spanning the change therefore carries both
#: labels for one failure.
ZeroCause = Literal[
    "agent_wrong",
    "format_violation",
    "output_truncated",
    "infrastructure",
    "item_defect",
    "verifier_defect",
    "environment_leak",
]

#: Stop reasons that mean the output cap ended the generation.
#:
#: ``length`` is the one a provider here produces: Ollama's native
#: ``done_reason`` and an OpenAI-compatible ``finish_reason`` both say it.
#: ``max_tokens`` is the Anthropic Messages API's spelling and **no backend
#: wired into this harness emits it today**, so it is a forward guard rather
#: than a measurement, kept because a second venue arriving is the moment
#: nobody re-reads this set.
#:
#: Matched case-folded on the whole field rather than as a substring, so a
#: backend reporting anything else keeps its own word for it and reads as no
#: claim about the cap. ``agy``'s ``SUCCESS`` and ``ERROR`` are what that
#: protects against as the set widens; today ``agy`` reaches
#: ``scripts/run_triggers.py`` and never a :class:`Score`, so the protection is
#: also untested against a live value.
_CAP_REASONS: Final[frozenset[str]] = frozenset({"length", "max_tokens"})

#: Matches an answer line, tolerating the decorations models add: bold markers,
#: leading bullets, code ticks, trailing punctuation.
_ANSWER_LINE: Final = re.compile(
    r"^[\s>*\-]*(?:\*\*|__|`)?\s*ANSWER\s*(?:\*\*|__|`)?\s*:\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_DECORATION: Final = re.compile(r"^[\s*_`\"'\[]+|[\s*_`\"'\].,;:!]+$")

#: A chat-template control token echoed onto the answer line. Qwen3 reads
#: ``/think`` and ``/no_think`` as a thinking-mode switch, and on the five-arm
#: study of 2026-08-27 it wrote the switch back after its answer 87 times in
#: 3,640 calls: ``ANSWER: monitor /think``. The scorer read that as an option
#: not on the menu and scored it wrong, and the key agreed with the word in
#: front of the token on 84 of the 87. The token is not an option and not a
#: decision, so it is stripped the way a trailing full stop is. This does not
#: rescore a committed record: a record's ``correct`` is what the scorer read
#: at the time, and ``figures.rescored_macros`` reports the difference beside
#: the registered figures rather than in their place.
_CONTROL_TOKEN: Final = re.compile(r"\s*/(?:no_)?think\s*$", re.IGNORECASE)


def last_answer_line(response: str) -> str | None:
    """The text after ``ANSWER:`` on the last answer line, or ``None`` without one."""
    matches = _ANSWER_LINE.findall(response)
    return matches[-1].strip() if matches else None


def strip_control_token(raw: str) -> tuple[str, bool]:
    """The answer text without a trailing control token, and whether one was there."""
    stripped = _CONTROL_TOKEN.sub("", raw)
    return stripped, stripped != raw


def normalise_answer(text: str) -> str:
    """Fold the differences that are presentation rather than content."""
    stripped = _DECORATION.sub("", text)
    return re.sub(r"[\s_\-]+", " ", stripped).strip().casefold()


@dataclass(frozen=True)
class ParsedAnswer:
    """The result of reading a response's final answer."""

    status: ParseStatus
    value: str | None
    raw: str | None

    @property
    def ok(self) -> bool:
        return self.status == "parsed"


@dataclass(frozen=True)
class Score:
    """One scored item."""

    item_id: str
    template_id: str
    expected: str
    parsed: ParsedAnswer
    correct: bool
    zero_cause: ZeroCause | None

    @property
    def parse_failed(self) -> bool:
        """Feeds the format-integrity guard, which is about parsing, not accuracy."""
        return not self.parsed.ok


def parse_answer(response: str, options: Sequence[str]) -> ParsedAnswer:
    """Extract the chosen option from a response.

    The *last* answer line wins. Models sometimes restate their answer after
    further reasoning, and the last statement is the one they are standing
    behind.
    """
    raw = last_answer_line(response)
    if raw is None:
        return ParsedAnswer(status="no_answer_line", value=None, raw=None)

    text, _ = strip_control_token(raw)
    target = normalise_answer(text)
    hits = [option for option in options if normalise_answer(option) == target]

    if len(hits) == 1:
        return ParsedAnswer(status="parsed", value=hits[0], raw=raw)
    if len(hits) > 1:
        # Only reachable from a template whose options normalise together, which
        # is a template defect. Surfaced rather than silently resolved.
        return ParsedAnswer(status="ambiguous", value=None, raw=raw)
    return ParsedAnswer(status="unlisted_option", value=None, raw=raw)


def hit_output_cap(stop_reason: str) -> bool:
    """Whether a backend's stop reason says the output cap ended the generation.

    An empty string reads as no claim either way, and it has to: it is what a
    record carries when nobody read a stop reason off the backend, which is
    every row written before 2026-09-03 and every row from the Claude Code
    provider. That provider is not silent at the wire, and the gap is worth
    naming rather than explaining away: its result event carries a ``subtype``,
    ``success`` in this repository's own fixture, and
    :func:`decision_evals.providers.claude_code.parse_result` does not read it.
    Until it does, a truncated reply on the CLI venue is still an unexplained
    ``format_violation``.
    """
    return stop_reason.strip().casefold() in _CAP_REASONS


def score_item(
    item: Item,
    response: str,
    *,
    infrastructure_error: bool = False,
    stop_reason: str = "",
) -> Score:
    """Score one response against its item.

    Args:
        infrastructure_error: Set by the runner when the call itself failed --
            a timeout, a revoked credential, a transport error. Passed in rather
            than inferred, because a model that returns nothing and a call that
            never happened are indistinguishable from the response text alone,
            and conflating them would let a rate-limited run masquerade as a
            model that stopped answering.
        stop_reason: What the backend said ended the generation, verbatim, or
            empty where it said nothing. It changes ``zero_cause`` and it never
            touches the parse: a reply is read exactly as it was before this
            argument existed, so a parsed answer scores identically whatever
            the backend reports. Defaulted for the same reason
            ``infrastructure_error`` is, and every caller that omits it gets
            the labels it got before.
    """
    parsed = parse_answer(response, item.options)
    correct = parsed.ok and parsed.value == item.answer
    return Score(
        item_id=item.item_id,
        template_id=item.template_id,
        expected=item.answer,
        parsed=parsed,
        correct=correct,
        zero_cause=_zero_cause(correct, parsed, infrastructure_error, stop_reason),
    )


def _zero_cause(
    correct: bool, parsed: ParsedAnswer, infrastructure_error: bool, stop_reason: str
) -> ZeroCause | None:
    """Why this item scored zero, or ``None`` where it did not.

    The order is the reading of the row, narrowest claim last. A call that
    never completed says nothing about the model. Then a reply with no answer
    line anywhere in it, which splits on whether the cap is what stopped it.
    Then everything else, unchanged: a reply that named an option off the menu
    or named two is a ``format_violation`` however it stopped, and a reply that
    answered and was wrong is ``agent_wrong`` however it stopped. Both of those
    reached an answer line, so the cap fell after the model had committed to
    something, and neither cause moves.
    """
    if infrastructure_error:
        return "infrastructure"
    if correct:
        return None
    if parsed.status == "no_answer_line" and hit_output_cap(stop_reason):
        return "output_truncated"
    if not parsed.ok:
        return "format_violation"
    return "agent_wrong"


@dataclass(frozen=True)
class ScoreSummary:
    """Aggregates over a set of scores.

    Accuracy counts parse failures as incorrect, which is the honest
    denominator: a response that did not answer did not get it right. The
    parse-failure rate is reported alongside so the two can be told apart, and
    that separation is what the format-integrity guard needs -- a skill that
    improves accuracy while breaking the output contract has not improved
    anything usable.
    """

    total: int
    correct: int
    parse_failures: int

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def parse_failure_rate(self) -> float:
        return self.parse_failures / self.total if self.total else 0.0


def summarise(scores: Sequence[Score]) -> ScoreSummary:
    return ScoreSummary(
        total=len(scores),
        correct=sum(1 for score in scores if score.correct),
        parse_failures=sum(1 for score in scores if score.parse_failed),
    )
