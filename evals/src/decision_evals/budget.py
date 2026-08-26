"""Run cost projection and the spend ledger.

Cost is a guard, not a metric. It exists so a run is stopped by arithmetic
rather than by noticing, and so a projection that was wrong is visible as a
refusal instead of as a quota exhausted three days into a confirmation run.

Dollars were the only unit for as long as every call went through
``--output-format json``, which reports ``total_cost_usd`` per call even on a
subscription where no dollars change hands. It is a usable proxy for quota
consumption there, and ``docs/LIMITATIONS.md`` has always said plainly that rate
limits rather than dollars are the real budget.

**On a local model and on a free tier that figure is zero, and a dollar cap that
cannot fire is not a guard.** So a ledger carries three limits — dollars, calls
and wall-clock seconds — and one of them has to be able to bind:
:class:`BudgetLedger` refuses at construction when ``bills`` is false and
neither the call cap nor the clock cap is set. That refusal is the whole point
of the class on a free venue, because every other failure mode here announces
itself and this one reads as a run that simply never stopped.

Wall-clock is a limit rather than a statistic for the same reason. A free tier
answers a rate limit with a pause, the pause is served by
:class:`~decision_evals.runner.Backpressure`, and a run held at the wall burns
no dollars and no calls while burning the afternoon. :meth:`BudgetLedger.record`
takes those seconds separately so a stopped run can say which of the two it ran
out of.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final


class BudgetError(RuntimeError):
    """The run would exceed its budget."""


def project_cost(*, n_items: int, n_arms: int, repeats: int = 2, usd_per_item: float) -> float:
    """Project the cost of a run.

    Every factor is multiplied in explicitly, because each is a place a
    projection quietly goes wrong by an integer factor. ``repeats`` defaults to
    2 rather than 1: the harness-variance literature makes single-run point
    estimates uninterpretable, so a one-repeat run is not the cheap version of
    this experiment, it is a different and weaker one.

    Raises:
        BudgetError: A non-positive factor. A projection of zero would pass any
            budget check, which is the one wrong answer that fails silently.
    """
    if n_items < 1 or n_arms < 1 or repeats < 1:
        raise BudgetError(
            f"a run needs at least one item, arm and repeat; got items={n_items}, "
            f"arms={n_arms}, repeats={repeats}"
        )
    if usd_per_item <= 0:
        raise BudgetError(f"usd_per_item must be positive, got {usd_per_item}")
    return n_items * n_arms * repeats * usd_per_item


#: Notional dollars per prompt token, taken from the most expensive call the
#: long canary made ($0.2296 for 101,142 tokens = $2.27e-6) and rounded up. It
#: is an upper bound on purpose: this figure authorises a call *before* it is
#: made, and an authorisation that under-counts is not a budget.
_USD_PER_TOKEN: Final = 2.5e-6

#: Conservative chars-per-token. Canary filler measured 6.01; real casefile
#: prose tokenises worse and lands nearer 4. Assuming 4 over-estimates the token
#: count for anything more repetitive than prose, which is the direction an
#: authorisation should err in.
_CHARS_PER_TOKEN: Final = 4.0

#: Below this, per-call overhead dominates and the linear model under-reads.
_FLOOR_USD: Final = 0.005


def estimate_cost_usd(*, prompt_chars: int) -> float:
    """Project one call's notional cost from the length of its prompt.

    The ledger authorises before the call, so this must never read low. Every
    constant here is set to over-estimate, and the test suite pins that against
    the four real calls the long canary made.

    The figure it returns is notional -- an API-equivalent price on a
    subscription where nothing is billed per call -- so it is a burn meter for
    quota consumption rather than a spend cap. It has to scale with length all
    the same: the flat $0.05 it replaces under-counted a 100k-token prompt
    roughly fivefold, and the ledger would have authorised a run it could not
    finish.

    Raises:
        BudgetError: A negative length. Silently clamping would authorise a call
            at the floor when the caller's length arithmetic is broken.
    """
    if prompt_chars < 0:
        raise BudgetError(f"prompt_chars cannot be negative, got {prompt_chars}")
    tokens = prompt_chars / _CHARS_PER_TOKEN
    return max(tokens * _USD_PER_TOKEN, _FLOOR_USD)


@dataclass(frozen=True)
class BudgetLedger:
    """What a run is allowed to spend, and what it has spent.

    Three limits, any of which stops the run. ``limit_usd`` is the original and
    still the one that matters on a metered venue. ``limit_calls`` and
    ``limit_seconds`` are optional and are what actually guards a venue whose
    per-call cost reads zero.

    Frozen: :meth:`record` returns a new ledger rather than mutating this one,
    so a checkpointed run resumes from a value it can serialise instead of from
    whatever an object happened to accumulate.

    Args:
        bills: Whether this venue's ``total_cost_usd`` means anything. False for
            a local model and for a free tier. A ledger that does not bill and
            carries neither a call cap nor a clock cap is refused, because it
            would authorise every call ever put to it.

    Raises:
        BudgetError: A limit that cannot bind, or one set below its own floor.
    """

    limit_usd: float
    spent_usd: float = 0.0
    limit_calls: int | None = None
    spent_calls: int = 0
    limit_seconds: float | None = None
    elapsed_seconds: float = 0.0
    #: How much of ``elapsed_seconds`` went on waiting out a rate limit rather
    #: than on waiting for an answer. Reported, never subtracted: an hour held
    #: at the wall is an hour of the run.
    backoff_seconds: float = 0.0
    bills: bool = True

    def __post_init__(self) -> None:
        if not self.bills and self.limit_calls is None and self.limit_seconds is None:
            raise BudgetError(
                "this venue reports no cost, so a dollar limit cannot fire. Set "
                "limit_calls or limit_seconds, or the ledger authorises every call it "
                "is ever shown."
            )
        if self.limit_calls is not None and self.limit_calls < 1:
            raise BudgetError(f"limit_calls must be at least 1, got {self.limit_calls}")
        if self.limit_seconds is not None and self.limit_seconds <= 0:
            raise BudgetError(f"limit_seconds must be positive, got {self.limit_seconds}")

    @property
    def remaining_usd(self) -> float:
        return max(self.limit_usd - self.spent_usd, 0.0)

    @property
    def remaining_calls(self) -> int | None:
        """Calls left, or None when no call cap is set."""
        if self.limit_calls is None:
            return None
        return max(self.limit_calls - self.spent_calls, 0)

    @property
    def remaining_seconds(self) -> float | None:
        """Seconds left, or None when no clock cap is set."""
        if self.limit_seconds is None:
            return None
        return max(self.limit_seconds - self.elapsed_seconds, 0.0)

    @property
    def exhausted(self) -> bool:
        """Whether any one of the three limits has been reached."""
        if self.bills and self.spent_usd >= self.limit_usd:
            return True
        if self.limit_calls is not None and self.spent_calls >= self.limit_calls:
            return True
        return self.limit_seconds is not None and self.elapsed_seconds >= self.limit_seconds

    def record(
        self,
        cost_usd: float = 0.0,
        *,
        calls: int = 1,
        seconds: float = 0.0,
        backoff_seconds: float = 0.0,
    ) -> BudgetLedger:
        """Return a ledger with one call's consumption added.

        ``calls`` defaults to 1 because the ordinary caller is recording a call.
        Pass 0 to book pure waiting against the clock: a backpressure pause that
        no call was charged for is still time the run spent.

        Raises:
            BudgetError: Any negative figure, or backoff longer than the elapsed
                time it is part of. Refunds are not a thing that happens here, so
                a negative is a bug in the caller and would extend the budget
                without saying so.
        """
        if cost_usd < 0:
            raise BudgetError(f"cost cannot be negative, got {cost_usd}")
        if calls < 0:
            raise BudgetError(f"calls cannot be negative, got {calls}")
        if seconds < 0 or backoff_seconds < 0:
            raise BudgetError(
                f"elapsed time cannot be negative, got seconds={seconds}, "
                f"backoff_seconds={backoff_seconds}"
            )
        if backoff_seconds > seconds:
            raise BudgetError(
                f"backoff_seconds={backoff_seconds} exceeds seconds={seconds}. Backoff is "
                "part of the elapsed time, not on top of it."
            )
        return replace(
            self,
            spent_usd=self.spent_usd + cost_usd,
            spent_calls=self.spent_calls + calls,
            elapsed_seconds=self.elapsed_seconds + seconds,
            backoff_seconds=self.backoff_seconds + backoff_seconds,
        )

    def assert_can_afford(
        self, cost_usd: float = 0.0, *, calls: int = 1, seconds: float = 0.0
    ) -> None:
        """Refuse a call that would take the run past any of its limits.

        Checked *before* the call rather than after, so the limit is a limit
        rather than a report. ``seconds`` is what the next call is expected to
        take; passing zero checks only that the clock has not already run out,
        which is the honest thing to do when there is no estimate.
        """
        if self.bills and self.spent_usd + cost_usd > self.limit_usd:
            raise BudgetError(
                f"this call would bring spend to ${self.spent_usd + cost_usd:.2f}, past the "
                f"${self.limit_usd:.2f} limit. The run is checkpointed: raise the limit "
                "deliberately and resume, rather than letting it drift."
            )
        if self.limit_calls is not None and self.spent_calls + calls > self.limit_calls:
            raise BudgetError(
                f"this call would be number {self.spent_calls + calls}, past the "
                f"{self.limit_calls}-call limit. The run is checkpointed: raise the limit "
                "deliberately and resume, rather than letting it drift."
            )
        if self.limit_seconds is not None and self.elapsed_seconds + seconds > self.limit_seconds:
            raise BudgetError(
                f"this call would bring the run to {self.elapsed_seconds + seconds:.0f}s, past "
                f"the {self.limit_seconds:.0f}s limit, {self.backoff_seconds:.0f}s of which "
                "went on waiting out rate limits. The run is checkpointed: raise the limit "
                "deliberately and resume."
            )

    def reset(self) -> BudgetLedger:
        """The same limits with nothing spent against them.

        What a nested cap does at a boundary. Limits are carried and totals are
        dropped, so a per-generation cap means per generation rather than
        whichever generation happened to go first.
        """
        return replace(self, spent_usd=0.0, spent_calls=0, elapsed_seconds=0.0, backoff_seconds=0.0)


#: The three scopes a nested budget guards, outermost first.
LEDGER_SCOPES: Final = ("run", "generation", "child")


@dataclass(frozen=True)
class NestedBudget:
    """Three ledgers at once: the whole run, one generation, one child.

    An evolution loop runs out of budget in two shapes and a single ledger only
    sees the first. One is the run as a whole going long. The other is one
    pathological child eating everything before the search has been anywhere: a
    candidate that provokes twenty thousand tokens of reasoning per item, or a
    generation that keeps proposing and keeps failing the acceptance gate. A cap
    per child bounds the second without lowering the first.

    Every method fans out across all three, so a call cannot be charged to the
    run and forgotten against the child.
    """

    run: BudgetLedger
    generation: BudgetLedger
    child: BudgetLedger

    def assert_can_afford(
        self, cost_usd: float = 0.0, *, calls: int = 1, seconds: float = 0.0
    ) -> None:
        """Refuse a call that any of the three scopes cannot afford.

        Raises:
            BudgetError: Naming the scope that refused, because "over budget" is
                not actionable when three budgets are in play.
        """
        for scope in LEDGER_SCOPES:
            ledger: BudgetLedger = getattr(self, scope)
            try:
                ledger.assert_can_afford(cost_usd, calls=calls, seconds=seconds)
            except BudgetError as exc:
                raise BudgetError(f"the {scope} budget refused this call: {exc}") from exc

    def record(
        self,
        cost_usd: float = 0.0,
        *,
        calls: int = 1,
        seconds: float = 0.0,
        backoff_seconds: float = 0.0,
    ) -> NestedBudget:
        """Charge one call to all three scopes."""
        charged = {
            scope: getattr(self, scope).record(
                cost_usd, calls=calls, seconds=seconds, backoff_seconds=backoff_seconds
            )
            for scope in LEDGER_SCOPES
        }
        return replace(self, **charged)

    def start_generation(self) -> NestedBudget:
        """Roll both inner ledgers over. The run ledger keeps accumulating."""
        return replace(self, generation=self.generation.reset(), child=self.child.reset())

    def start_child(self) -> NestedBudget:
        """Roll the child ledger over. The run and the generation keep accumulating."""
        return replace(self, child=self.child.reset())
