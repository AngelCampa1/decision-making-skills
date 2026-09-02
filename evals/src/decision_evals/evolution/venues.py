"""Where an evolution run's calls go, and what each venue can prove about itself.

Two venues carry this study and they are unalike in the one way that matters to
a budget. A local Ollama server and NVIDIA Build's free tier both report
``total_cost_usd`` as zero, so the dollar cap that guarded every previous run
here cannot fire on either; :class:`~decision_evals.budget.BudgetLedger` refuses
a ledger built for them without a call cap or a clock cap, and :attr:`Venue.bills`
is the flag that tells it which kind of venue it is looking at.

They are also unalike in what they can be asked about themselves.
:func:`~decision_evals.providers.openai_compatible.show` reads an Ollama model
card and :func:`~decision_evals.providers.openai_compatible.assert_isolated`
refuses a card carrying a baked-in ``SYSTEM`` line — a contamination channel
that would put text in front of every arm without appearing in any prompt. A
hosted endpoint has no such card. **The honest record for NVIDIA Build is "no
receipt obtainable", which is not the same sentence as "isolation verified"**,
and :func:`isolation_receipt` returns the first rather than quietly returning
the second.

The reflector and the target are separate venues on purpose. A 4B model is a
reasonable thing to write a skill *for* and a poor thing to write one *with*,
so the ordinary arrangement is a local target and a hosted reflector, and a run
that recorded one model would not say which job it did.
"""

from __future__ import annotations

import hashlib
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from decision_evals.providers.claude_code import CliResult, IsolationError, RateLimitedError
from decision_evals.providers.openai_compatible import (
    Endpoint,
    assert_isolated,
    loaded,
    nvidia_build,
    ollama,
    show,
    warm,
)
from decision_evals.providers.openai_compatible import run as openai_run
from decision_evals.runner import (
    Backoff,
    Backpressure,
    CallFn,
    RunError,
    call_with_backoff,
    local_call,
)


class VenueError(RuntimeError):
    """A venue was named that cannot be reached, or cannot be reached honestly."""


@dataclass(frozen=True, slots=True)
class Venue:
    """One endpoint, one model, and what is true about paying for it."""

    model: str
    endpoint: Endpoint
    #: Whether ``total_cost_usd`` from this venue means anything. False for both
    #: venues this study uses, which is why they need a call or clock cap.
    bills: bool

    @property
    def label(self) -> str:
        return self.endpoint.label

    @property
    def receipts(self) -> bool:
        """Whether isolation can be checked rather than assumed.

        Read off the endpoint rather than stored, because
        :class:`~decision_evals.providers.openai_compatible.Endpoint` already
        answers it and two fields that must agree eventually will not.
        """
        return self.endpoint.has_receipt


def venue_for(model: str, *, api_key: str | None = None) -> Venue:
    """Build the venue a model string names.

    The prefix is the venue, matching :data:`~decision_evals.arenas.MODELS`, so
    a model that resolves here is a model the arena gate has a row for.

    Args:
        api_key: Passed through to :func:`nvidia_build`, which falls back to
            ``NVIDIA_API_KEY`` in the environment. Keys live in the environment
            and never in the tree.

    Raises:
        VenueError: An unknown prefix, or a hosted venue with no key. A missing
            key surfaces here rather than as an authentication failure on the
            first call, because by then the run has a checkpoint and a
            half-written lineage.
    """
    if model == MOCK_MODEL:
        return Venue(model=model, endpoint=Endpoint(base_url="", label="mockllm"), bills=False)
    if model.startswith("ollama/"):
        return Venue(model=model, endpoint=ollama(), bills=False)
    if model.startswith("nvbuild/"):
        endpoint = nvidia_build(api_key)
        if not endpoint.api_key:
            raise VenueError(
                "NVIDIA Build needs a key in NVIDIA_API_KEY. It is a free tier and the "
                "key is free; it lives in the environment and never in the tree."
            )
        return Venue(model=model, endpoint=endpoint, bills=False)
    raise VenueError(
        f"no venue for {model!r}. Prefix it with the venue that answers it "
        f"(`ollama/` or `nvbuild/`, or {MOCK_MODEL!r} for a smoke run), which is also "
        "what the arena registry keys on."
    )


def call_fn(venue: Venue, *, max_tokens: int | None = None, num_ctx: int | None = None) -> CallFn:
    """The callable a run makes its calls through.

    ``max_tokens`` caps generation. It is passed rather than defaulted because
    the number belongs in the run's manifest: a small reasoning model that fails
    to stop scores the same as one that is capped -- no answer line either way --
    but costs two orders of magnitude more wall clock, and on a matched-budget
    comparison that decides the result.

    ``num_ctx`` fixes the context window, and passing it moves the call to
    Ollama's native surface, the only one that accepts a window. That surface
    also pins residency, which matters more than the window did: two of this
    corpus's 21 validation items answer to whether the model was freshly loaded,
    deterministically, and a search that waits on a hosted reflector between
    passes crosses the default five-minute residency every time.

    Raises:
        VenueError: The model does not name its venue.
            :func:`~decision_evals.runner.local_call` refuses a bare model name
            because a record stamped with the label but requested without it
            un-registers the venue by typo; that refusal is re-raised here in
            this module's own type so a caller catches one thing.
    """
    if venue.model == MOCK_MODEL:
        return mock_call()
    try:
        return local_call(venue.model, venue.endpoint, max_tokens=max_tokens, num_ctx=num_ctx)
    except RunError as exc:
        raise VenueError(str(exc)) from exc


def isolation_receipt(venue: Venue, *, timeout: float = 30.0) -> str:
    """One line saying what was checked, for a run's README.

    Returns a sentence rather than a boolean, because the three outcomes are not
    two: the card was read and is clean, the card was read and is not, or there
    is no card to read. Only the first is a verified venue.

    Raises:
        VenueError: A card was obtainable and carried a baked-in system prompt.
            That is contamination reaching every arm at once, and it is the one
            outcome a run may not proceed past.
    """
    if not venue.receipts:
        return (
            f"{venue.model}: no receipt obtainable. This endpoint exposes no model card, "
            "so nothing here has checked for a baked-in system prompt. Not the same "
            "statement as isolation verified."
        )
    card = show(venue.model, endpoint=venue.endpoint, timeout=timeout)
    try:
        assert_isolated(card)
    except IsolationError as exc:
        raise VenueError(f"{venue.model} is not isolated: {exc}") from exc
    return (
        f"{venue.model}: card read, no baked-in system prompt "
        f"(system={len(card.system)} chars, template={len(card.template)} chars)."
    )


#: What the longest prompt this corpus has produced actually cost, rounded up.
#: Every skill body plus its item across the two 2026-08-27 runs fitted in 1,873
#: input tokens, and a search grows bodies, so the allowance is generous rather
#: than tight.
PROMPT_ALLOWANCE: Final = 2_048


def context_window(venue: Venue, *, timeout: float = 30.0) -> int | None:
    """The context window the target is *loaded* with, or ``None`` if unknowable.

    ``None`` is a real answer and appears in two cases: a hosted endpoint that
    exposes no residency surface, and a local model nobody has loaded yet. The
    caller warms the model and asks again rather than treating either as
    permission to proceed.
    """
    if not venue.receipts:
        return None
    bare = venue.model[len(venue.label) + 1 :]
    window = loaded(endpoint=venue.endpoint, timeout=timeout).get(bare)
    if window is not None:
        return window
    # Nobody has loaded it, which is the state every first run of the day is
    # in. A guard that only ever fires on a warm server is a guard that misses
    # the run it was written for, so make the server resident and ask again.
    # The load generates nothing and is not a model call.
    warm(venue.model, endpoint=venue.endpoint)
    return loaded(endpoint=venue.endpoint, timeout=timeout).get(bare)


def assert_cap_fits(window: int | None, max_tokens: int) -> None:
    """Refuse an output cap the model's own context cannot hold.

    A cap larger than the window asks for an answer the request cannot hold. The
    server shifts the context as the window fills, the system prompt and the
    question go out of the front of it, and whatever the model does after that
    it is no longer answering the question it was asked. Refusing that is not a
    theory about any particular run: it is the observation that no possible
    response fills the gap between the two numbers.

    On 2026-08-27 two searches ran at ``max_tokens: 8192`` against a 4,096-token
    window. Whether that produced their unreadable answers is **not** settled --
    a probe at 16,384 did not reproduce them and neither did one at 4,096 --
    and this refusal does not need it to be.

    ``window`` of ``None`` passes, because a check that cannot be made is not a
    failure. Whether it *could* be made is the caller's problem.

    Raises:
        EvolveError: The cap plus a prompt allowance exceeds the window.
    """
    if window is None:
        return
    if max_tokens + PROMPT_ALLOWANCE > window:
        raise VenueError(
            f"an output cap of {max_tokens:,} tokens does not fit a context window of "
            f"{window:,}, once {PROMPT_ALLOWANCE:,} tokens are left for the prompt. A "
            "generation that runs to the end of the window loses the question out of the "
            "front of it and can never answer, which scores as a formatting failure. "
            f"Cap the output at {window - PROMPT_ALLOWANCE:,} or load the model with a "
            "larger window (`OLLAMA_CONTEXT_LENGTH`), and record which."
        )


def key_is_present(variable: str = "NVIDIA_API_KEY") -> bool:
    """Whether a hosted venue could be reached, without reading the key.

    For a preflight message and for tests. The value never leaves the
    environment, and nothing in this package logs it.
    """
    return bool(os.environ.get(variable, "").strip())


#: The in-process venue. Registered in :data:`~decision_evals.arenas.MODELS`
#: under the ``dev`` arena, which emits no verdict, so nothing measured here can
#: reach a published number.
MOCK_MODEL: Final = "mockllm/deterministic"

#: The phrase a candidate body has to contain for :func:`mock_call` to answer
#: correctly. Arbitrary, and that is the point: it gives a search real signal
#: that is not a real capability, so a smoke run exercises the whole loop --
#: proposal, scoring, acceptance, lineage -- without a model and without a
#: number anyone could mistake for a result.
MOCK_MARKER: Final = "read the facts in order"


def mock_call(answers: Mapping[str, str] | None = None, marker: str = MOCK_MARKER) -> CallFn:
    """A CallFn that answers from the prompt, with no server and no model.

    It reads the option menu out of the rendered item and picks one. Which one
    depends on whether ``marker`` appears in the system prompt: with it, the
    correct option, looked up in ``answers``; without it, an option chosen by
    hashing the prompt, which is right about half the time on a corpus whose
    answer sits at each position equally often.

    So a body containing the marker is worth roughly half an item per item, and
    nothing else in a body is worth anything. That is an oracle rather than a
    capability, deliberately: a smoke run's job is to show that a search
    proposes, scores, accepts and records, and a mock that rewarded something
    resembling decision quality would invite reading its number as one.

    ``answers`` maps a rendered item to its correct option. ``None`` makes every
    reply the hashed guess, which is the honest behaviour when the caller did
    not supply an answer key -- a marker that cannot be rewarded should not be.

    Deterministic, instant and free.
    """
    key = dict(answers or {})

    def call(prompt: str, system_prompt: str, append: bool) -> CliResult:
        options = _options_in(prompt)
        chosen = ""
        if options:
            if marker in system_prompt.lower() and prompt in key:
                chosen = key[prompt]
            else:
                digest = hashlib.sha256(prompt.encode("utf-8")).digest()
                chosen = options[digest[0] % len(options)]
        return CliResult(
            text=f"ANSWER: {chosen}",
            model=MOCK_MODEL,
            cost_usd=0.0,
            input_tokens=len(prompt) // 4,
            output_tokens=len(chosen) // 4 + 3,
            duration_ms=0,
            session_id="mock",
        )

    return call


def _options_in(prompt: str) -> list[str]:
    """The option menu, which is the block after the ``Options:`` line.

    Facts render as bullets too, so a bare "every line starting with a dash" is
    the whole item rather than its menu -- and a mock that picked its answer
    from the facts would score zero everywhere and look like a broken skill.
    """
    _, _, menu = prompt.partition("Options:")
    return [line[2:].strip() for line in menu.splitlines() if line.startswith("- ")]


def _stderr(message: str) -> None:
    """Where a retry is reported when the caller names nowhere else.

    The search log GEPA writes belongs to the engine, and the reflector is built
    before the engine is, so the console is the surface both jobs share.
    """
    print(message, file=sys.stderr, flush=True)


def reflection_lm(
    model: str,
    *,
    temperature: float = 1.0,
    backoff: Backoff | None = None,
    log: Callable[[str], None] = _stderr,
) -> Callable[[str], str]:
    """A prompt-in, text-out callable for an engine's proposal step.

    This is the one place in the package where temperature is not zero. Every
    scored call runs at zero, because a measurement that resamples is a
    measurement with an extra variance term nobody registered. A *proposal* is
    the opposite job: an engine asking for the same rewrite five times and
    getting the same rewrite five times is an engine with a search space of one.

    Returns the reply text and nothing else, which is the shape GEPA's
    ``reflection_lm`` expects. The reasoning field is dropped: a reflector that
    thinks out loud is fine and the engine has no use for the transcript.

    A rate limit waits here, on the schedule :func:`~decision_evals.runner.run_arm`
    uses for a scored call, and every wait is written to ``log``. The hosted
    free tier that reflects for a local target answers 429 when its window
    closes, and on 2026-08-27 that refusal reached the engine as a plain error.
    GEPA catches everything and sleeps, the deadline in
    :mod:`decision_evals.evolution.run` is what finally stopped it, and the
    hours between were spent on a call that would have cleared in seconds. One
    :class:`~decision_evals.runner.Backpressure` serves the whole search, so the
    breaker counts consecutive refusals across proposals and a window that has
    closed stops the search instead of being waited on again.

    Args:
        backoff: The schedule. ``None`` is the runner's default, the same five
            attempts and sixty-second ceiling a scored call gets.
        log: Where each retry is reported. Standard error unless the caller
            has a better place.
    """
    venue = venue_for(model)
    backpressure = Backpressure(backoff)

    def report(attempt: int, exc: RateLimitedError) -> None:
        asked = f"server asked for {exc.retry_after:g}s" if exc.retry_after else "backing off"
        log(
            f"reflector {venue.model} rate-limited on attempt {attempt + 1} of "
            f"{backpressure.policy.attempts}, {asked} before the next: {exc}"
        )

    def reflect(prompt: str) -> str:
        result = call_with_backoff(
            lambda: openai_run(
                prompt,
                system_prompt="",
                model=venue.model,
                endpoint=venue.endpoint,
                temperature=temperature,
            ),
            backpressure=backpressure,
            on_retry=report,
        )
        return result.text

    return reflect


#: What :func:`mock_reflector` appends, one rung per proposal. The last rung is
#: the phrase :func:`mock_call` rewards, so a smoke search improves on its third
#: proposal and not before -- which is what makes the run a test of the loop
#: rather than of the first thing it tried.
MOCK_LADDER: Final[tuple[str, ...]] = (
    "Weigh each option against the facts.",
    "Say which fact decided it.",
    f"When the facts conflict, {MOCK_MARKER}.",
)


def mock_reflector(ladder: Sequence[str] = MOCK_LADDER) -> Callable[[str], str]:
    """A proposer that improves on a schedule instead of thinking.

    GEPA's default proposal step asks a model to rewrite the current instruction
    and reads the answer out of a fenced block, so this returns one. It appends
    the next rung of ``ladder`` to whatever instruction it was shown, and it
    counts *calls* rather than reading what is already in the text.

    **Counting calls is the part that took two tries.** A version that appended
    the first rung not already present could never get past rung one: GEPA
    accepts on strict improvement, rung one is worth nothing, the rejected
    candidate is discarded, and the next proposal starts from the same base and
    produces the same rung again. The search converged after two candidates
    having never reached the rung that was worth something.

    Once the ladder is exhausted it keeps appending the last rung, so a proposal
    from an accepted parent eventually repeats a body GEPA has already seen and
    the search converges. A proposer that always returns something new never
    repeats a candidate, and a search that never repeats a candidate never
    stops: the first smoke run wrote 4,665 lineage lines before it was stopped
    by hand.

    It exists so a smoke run needs no model at all. GEPA refuses to start
    without a ``reflection_lm`` when the adapter supplies no
    ``propose_new_texts`` -- which this one deliberately does not, for reasons in
    :mod:`decision_evals.evolution.adapter` -- so "no reflector" is not an option
    and a stub is the honest way to have none.
    """
    rungs = list(ladder)
    proposals = 0

    def reflect(prompt: str) -> str:
        nonlocal proposals
        blocks = prompt.split("```")
        current = blocks[1].strip() if len(blocks) > 2 else ""
        addition = rungs[min(proposals, len(rungs) - 1)]
        proposals += 1
        return f"```\n{current}\n\n{addition}\n```"

    return reflect
