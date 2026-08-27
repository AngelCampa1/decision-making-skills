"""One search at a time, on venues where two would corrupt both.

This repository has *measured* the failure this prevents. On 2026-08-19 a
batching local server, asked the same questions twice under concurrency,
returned a different answer to every one of forty items -- 0 of 40 agreement,
McNemar p < 0.0001 -- which is why
:data:`~decision_evals.runner.CONCURRENCY_UNSAFE` registers the ``ollama``
prefix.

It then happened twice on 2026-08-27, in the same session, to somebody who knew
the rule. The first time a run outlived the tool timeout that appeared to end
it and a second was launched on top. The second time a shell loop meant to wait
for one process to exit misread the process list and started the next engine
into a live run. Both times the evidence was the same and unmistakable: the seed
skill scored 15 of 21 in each of two serial runs and **17 of 21** in the run
that overlapped, on the same body, the same items and the same model at
temperature zero.

A rule written in a document did not stop it and a shell loop did not stop it.
This does, because it is checked by the thing that makes the calls.

**A stale lock is not a running process.** A killed run leaves its file behind,
and refusing every later run because of it would make the guard the problem. So
the file carries a pid and the check is whether that pid is alive.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from decision_evals.runner import CONCURRENCY_UNSAFE

#: Beside the runs it guards, so one lock covers every checkpoint under it.
LOCK_NAME: Final = ".running.json"


class ConcurrencyError(RuntimeError):
    """Another search holds the venue this one needs."""


@dataclass(frozen=True, slots=True)
class Holder:
    """Who holds the lock, and what they are doing."""

    pid: int
    model: str
    run: str


def unsafe(model: str) -> bool:
    """Whether concurrent calls to this model are known to change its answers."""
    return any(model.startswith(prefix) for prefix in CONCURRENCY_UNSAFE)


def _alive(pid: int) -> bool:
    """Whether a process id is still running.

    ``os.kill(pid, 0)`` is the portable check and raises ``PermissionError``
    when the process exists but belongs to somebody else, which still counts as
    alive.
    """
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def read_holder(root: Path) -> Holder | None:
    """Who currently holds the lock, or ``None`` if nobody does.

    A lock file whose process has exited is not a holder, and neither is one
    that cannot be parsed: a corrupt file should not be able to block every
    future run.
    """
    path = root / LOCK_NAME
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        holder = Holder(pid=int(raw["pid"]), model=str(raw["model"]), run=str(raw["run"]))
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return holder if _alive(holder.pid) else None


class Solo:
    """Hold the venue for one search, or refuse to start.

    Only engaged for a venue on the unsafe list. A hosted endpoint fans out by
    design and two runs against it are two runs, so locking there would serialise
    work for no reason.

    Args:
        root: Where the lock lives, normally ``results/evolution/``.
        model: The *target* model. The reflector is not locked: it is somebody
            else's server and this rule is about a local one answering two
            callers at once.
        run: The run name, so a refusal can say what is already going.

    Raises:
        ConcurrencyError: A live process holds it.
    """

    def __init__(self, root: Path, model: str, run: str) -> None:
        self.root = root
        self.model = model
        self.run = run
        self._held = False

    def __enter__(self) -> Solo:
        if not unsafe(self.model):
            return self
        held = read_holder(self.root)
        if held is not None:
            raise ConcurrencyError(
                f"{held.run!r} is already running against {held.model} as pid {held.pid}, "
                f"and {self.model} changes its answers when two callers share it: this "
                "repository measured 0 of 40 agreement under concurrency on 2026-08-19, "
                "and measured it again on 2026-08-27 when two runs overlapped and the "
                "same skill scored 17 of 21 against 15 of 21 in each serial run. Wait for "
                "it, or stop it deliberately."
            )
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / LOCK_NAME).write_text(
            json.dumps({"pid": os.getpid(), "model": self.model, "run": self.run}, indent=2),
            encoding="utf-8",
            newline="",
        )
        self._held = True
        return self

    def __exit__(self, *_: object) -> None:
        if self._held:
            (self.root / LOCK_NAME).unlink(missing_ok=True)
            self._held = False
