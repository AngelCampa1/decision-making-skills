"""The append-only record of what an engine tried and what it kept.

An evolution run's output is one skill body. Its *result* is the search that
produced it, and neither engine keeps that in a form anyone else can read:
GEPA persists frontier state as its own resumption format and SkillOpt writes a
transcript. Both answer "what won". Neither answers "how many candidates were
explored, which parent each came from, what each scored, and on which items" —
which is the whole of what makes a winner interpretable.

The concrete reason this file exists is in
``notebook/2026-08-26-the-two-engines-install-and-one-of-them-needs-an-attribute-the-protocol-calls-optional.md``:
an adapter missing an optional method made every mutation raise, GEPA caught it,
retried, gave up, and **exited zero reporting the seed as the best candidate**.
A run that explored one candidate and a run whose search failed entirely
produced the same output. :func:`assert_searched` is the check that would have
caught it, and it reads this file.

**The body is in the record, not beside it.** A sidecar directory of ``.md``
files keyed by hash is tidier to read and is a second copy of the same thing;
when the two disagree, nothing says which is the run. One line holds one
candidate entire, and :func:`body_sha` recomputes the key from the body, so a
line that has been edited stops verifying.

Append-only, one JSON object per line, in the shape every other checkpoint in
this repository uses. A crashed run leaves a readable file with a truncated
last line; :func:`load_lineage` says so rather than guessing.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

#: Engines whose candidates may appear in a lineage. ``seed`` is the human-
#: written body the search started from, recorded as generation 0 so the
#: comparison a study makes -- machine author against human author -- has both
#: sides in one file.
ENGINES: Final[frozenset[str]] = frozenset({"seed", "gepa", "skillopt"})

#: How many candidates a search must have explored before its winner is read.
#: Two: the seed, and something that is not the seed.
SEARCHED_FLOOR: Final = 2


class LineageError(RuntimeError):
    """The lineage on disk cannot be read, or does not describe a search."""


def body_sha(body: str) -> str:
    """The key a candidate is known by: SHA-256 of its exact bytes.

    Exact, not normalised. Trailing whitespace and heading style are part of
    what an engine mutates, and a key that folded them would merge two
    candidates that scored differently.
    """
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class Candidate:
    """One body an engine produced, and everything needed to place it.

    ``score`` is optional because a candidate can be recorded before it is
    scored and because a proposal can fail to evaluate at all. ``None`` means
    not scored; ``0.0`` means scored zero, and conflating them would turn a
    broken evaluation into a bad candidate.
    """

    candidate_sha: str
    parent_sha: str | None
    generation: int
    engine: str
    #: The model the body was scored against, and the model that wrote it. They
    #: differ on purpose: a 4B target with a stronger reflector is the ordinary
    #: arrangement, and a run that does not record both cannot say which model
    #: the skill is a skill *for*.
    target_model: str
    reflector_model: str | None
    seeds: tuple[int, ...]
    n_items: int
    score: float | None
    #: Whether the *engine* kept this candidate at its own acceptance gate.
    #: SkillOpt reports this per candidate; GEPA does not, and records ``False``
    #: throughout rather than a guess. Never read as "this is the winner": the
    #: winner is whichever body the engine hands back, resolved through
    #: :func:`find`.
    accepted: bool
    #: The commit the harness was at. A candidate is a function of the scorer
    #: as much as of the engine, and the scorer moves.
    git_sha: str
    created_at: str
    body: str

    def __post_init__(self) -> None:
        if self.engine not in ENGINES:
            raise LineageError(f"unknown engine {self.engine!r}; expected one of {sorted(ENGINES)}")
        if self.candidate_sha != body_sha(self.body):
            raise LineageError(
                f"candidate_sha {self.candidate_sha[:12]} is not the hash of this body. "
                "The key is what joins a lineage line to the records scored under it, "
                "so a mismatch makes both unreadable."
            )
        if self.generation == 0 and self.parent_sha is not None:
            raise LineageError("generation 0 is where a search starts, so it has no parent")
        if self.generation > 0 and self.parent_sha is None:
            raise LineageError(
                f"generation {self.generation} candidate {self.candidate_sha[:12]} has no "
                "parent. A search whose children are unparented is a list, not a lineage."
            )


def append_candidate(path: Path, candidate: Candidate) -> None:
    """Append one candidate, creating the file and its directory if needed.

    Flushed per line. A run that dies mid-search has told the truth about
    everything up to the moment it died, which is the only useful thing a
    crashed search can do.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    row = asdict(candidate)
    row["seeds"] = list(candidate.seeds)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()


def load_lineage(path: Path) -> list[Candidate]:
    """Every candidate in file order.

    Raises:
        LineageError: A line that is not JSON, or is JSON that is not a
            candidate. Skipping it would under-count the search, and the count
            is what :func:`assert_searched` reads.
    """
    if not path.is_file():
        return []
    candidates: list[Candidate] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LineageError(
                f"{path}:{number} is not JSON: {exc}. A truncated last line is a run that "
                "died mid-write; drop it deliberately rather than reading past it."
            ) from exc
        try:
            candidates.append(Candidate(**{**row, "seeds": tuple(row.get("seeds", ()))}))
        except TypeError as exc:
            raise LineageError(f"{path}:{number} is not a candidate: {exc}") from exc
    return candidates


def assert_searched(candidates: list[Candidate], *, floor: int = SEARCHED_FLOOR) -> None:
    """Refuse a lineage whose winner never had a competitor.

    The check the GEPA adapter defect made necessary. An engine that proposes
    nothing still returns the seed and still exits zero, so "there is a best
    candidate" is not evidence that anything was searched.

    Raises:
        LineageError: Fewer than ``floor`` distinct bodies.
    """
    distinct = {candidate.candidate_sha for candidate in candidates}
    if len(distinct) < floor:
        raise LineageError(
            f"this lineage holds {len(distinct)} distinct candidate(s), under the floor of "
            f"{floor}. An engine whose every proposal failed still reports a winner and "
            "still exits zero, so a score from this run says nothing about the engine."
        )


def best_scored(candidates: list[Candidate]) -> Candidate:
    """The highest-scoring candidate in the lineage.

    Ties break towards the *later* generation: a tie the search kept exploring
    past is a candidate it preferred and the score could not separate.

    This is what to read when an engine reports no winner of its own. When it
    does report one, :func:`find` is the honest answer — the engine's own
    acceptance rule is part of what the study is comparing, and substituting our
    arithmetic for it would measure something else.

    Raises:
        LineageError: Nothing scored. A search with no scored candidate has no
            winner rather than a winner that is the seed.
    """
    scored = [c for c in candidates if c.score is not None]
    if not scored:
        raise LineageError(
            f"no candidate carries a score across {len(candidates)} line(s), so this "
            "search has no winner to freeze."
        )
    return max(scored, key=lambda c: (c.score or 0.0, c.generation))


def find(candidates: list[Candidate], sha: str) -> Candidate:
    """The candidate with this hash.

    How an engine's declared winner is resolved: the engine hands back a body,
    :func:`body_sha` turns it into a key, and this finds the line that says when
    it was proposed, from what, and what it scored.

    Raises:
        LineageError: No such candidate. An engine returning a body that was
            never evaluated is returning something this record cannot account
            for, and freezing it would publish a winner with no provenance.
    """
    for candidate in candidates:
        if candidate.candidate_sha == sha:
            return candidate
    raise LineageError(
        f"the engine returned a body hashing to {sha[:12]}, which appears nowhere in "
        f"this lineage of {len(candidates)} line(s). A winner that was never scored here "
        "cannot be attributed to this search."
    )
