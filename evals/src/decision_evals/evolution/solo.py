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


#: ``OpenProcess`` access right that only asks to wait on a handle.
_SYNCHRONIZE: Final = 0x0010_0000
#: ``WaitForSingleObject`` saying the process has not exited.
_WAIT_TIMEOUT: Final = 0x0000_0102
#: ``OpenProcess`` refused because the process belongs to somebody else. It
#: exists, which is the whole question.
_ERROR_ACCESS_DENIED: Final = 5


def _alive_windows(pid: int) -> bool:
    """Whether a process id is running, asked of the Win32 API.

    ``os.kill(pid, 0)`` does not work here and does not fail safely either. The
    POSIX idiom of "signal zero probes without delivering" has no Windows
    equivalent: ``os.kill`` maps to ``TerminateProcess`` for any signal it does
    not special-case, and signal zero is rejected outright with
    ``WinError 87``. The first version of this module caught that as
    ``OSError``, returned ``False``, and so reported **every** live process as
    dead -- a lock that took itself out and let a second search start into a
    running one, which is exactly what it was written to prevent.

    ``SYNCHRONIZE`` is the narrowest right that answers the question, and
    access-denied is an answer: a process somebody else owns is still a process.
    """
    import ctypes

    # `ctypes.windll` exists only on Windows, and typeshed says so, so a direct
    # attribute access is an error wherever the checker is configured for
    # another platform. CI runs on Linux and caught it there after every local
    # run had passed. The two obvious repairs both fail under this config:
    # `strict` turns on `warn_unused_ignores`, so a `type: ignore` here is an
    # error on Windows, and `warn_unreachable` rejects a `sys.platform` branch
    # on whichever platform it narrows away. `getattr` is the one spelling that
    # is clean on both.
    kernel32 = getattr(ctypes, "windll").kernel32  # noqa: B009
    handle = kernel32.OpenProcess(_SYNCHRONIZE, False, pid)
    if not handle:
        return bool(kernel32.GetLastError() == _ERROR_ACCESS_DENIED)
    try:
        return bool(kernel32.WaitForSingleObject(handle, 0) == _WAIT_TIMEOUT)
    finally:
        kernel32.CloseHandle(handle)


def _alive(pid: int) -> bool:
    """Whether a process id is still running.

    Two implementations because the platforms disagree about what "ask without
    disturbing" means. See :func:`_alive_windows` for why the portable-looking
    one is not portable.

    The branch is on ``os.name`` rather than ``sys.platform`` because the type
    checker narrows the latter to the platform it was configured for and then
    reports the other half of a deliberately cross-platform function as dead
    code.
    """
    if pid <= 0:
        return False
    if os.name == "nt":
        return _alive_windows(pid)
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
