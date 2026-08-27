"""The reflection prompts SkillOpt ships in its repository and in no release.

``skillopt.prompts.load_prompt`` reads its 43 prompts off disk, from paths it
derives from its own module location. No built distribution contains them. The
0.2.0 wheel and the 0.2.0 sdist on PyPI carry zero non-Python files, and a build
from the ``v0.2.0`` git tag carries none either, because the project declares
``[tool.setuptools.packages.find]`` and no ``package-data``. The Python is fine
-- byte-identical between the wheel and the tag across all 87 modules -- and the
data is simply not there.

The consequence is not subtle and is not specific to this repository's
environment: the inherited reflection step is the first thing every optimisation
step does, so ``pip install skillopt`` produces an engine that raises
``FileNotFoundError`` before finishing one step, for its own benchmarks as much
as for anything else.

So the files are vendored, which here means what
[`AGENTS.md`](../../../../AGENTS.md) says it means: a copy under
``datasets/vendor/``, pinned by digest, restored into the installed package
before a run. Copies rather than replacements. **Writing our own prompts would
have been a patch on the engine**, and not a small one -- the prompts are the
reflection strategy, and the reflection strategy is the thing this study is
measuring. A SkillOpt whose analyst prompt we wrote would not be SkillOpt.

Restoring into ``site-packages`` is not how anyone would like to install data.
It is where the engine looks: ``_PROMPTS_DIR`` is the prompts package's own
directory and there is no override. The alternative is a fork, which is worse
for a study about what an engine does.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: The committed copies, in the layout they have inside the package.
VENDOR_ROOT: Final = "datasets/vendor/skillopt-prompts"

#: Their pinned identity: the upstream commit and a SHA-256 per file.
LOCK_PATH: Final = "datasets/vendor/skillopt_prompts.lock.json"


class PromptError(RuntimeError):
    """The engine's prompts are missing, or are not the ones that were pinned."""


@dataclass(frozen=True, slots=True)
class PromptLock:
    """What was vendored, and from where."""

    repo: str
    tag: str
    commit: str
    license: str
    retrieved: str
    #: Path inside the package -> SHA-256 of its bytes.
    digests: dict[str, str]


def load_lock(repo_root: Path) -> PromptLock:
    """Read the lock, or say which file is missing.

    Raises:
        PromptError: No lock, or a lock missing a field.
    """
    path = repo_root / LOCK_PATH
    if not path.is_file():
        raise PromptError(
            f"{LOCK_PATH} is missing, so there is nothing pinning which prompts a "
            "SkillOpt run used. A run without it would be reproducible only by luck."
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    try:
        return PromptLock(
            repo=raw["repo"],
            tag=raw["tag"],
            commit=raw["commit"],
            license=raw["license"],
            retrieved=raw["retrieved"],
            digests={name: entry["sha256"] for name, entry in raw["files"].items()},
        )
    except KeyError as exc:
        raise PromptError(f"{LOCK_PATH} has no {exc.args[0]!r}") from exc


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_vendored(repo_root: Path, lock: PromptLock) -> None:
    """Check the committed copies against the lock, before anything is installed.

    A digest mismatch here means the vendored copy was edited. That is the one
    edit this module exists to prevent, so it is refused rather than repaired:
    an engine running prompts we changed is not the engine the result is about.

    Raises:
        PromptError: A file is missing, or its bytes are not the pinned bytes.
    """
    root = repo_root / VENDOR_ROOT
    missing = [name for name in lock.digests if not (root / name).is_file()]
    if missing:
        raise PromptError(
            f"{len(missing)} vendored prompt(s) are missing from {VENDOR_ROOT}, starting "
            f"with {missing[0]!r}. They are committed; a checkout should have them."
        )
    changed = [name for name, digest in lock.digests.items() if _sha256(root / name) != digest]
    if changed:
        raise PromptError(
            f"{len(changed)} vendored prompt(s) do not match {LOCK_PATH}, starting with "
            f"{changed[0]!r}. These are copies of {lock.repo}@{lock.tag} and editing one "
            "makes the engine under study a different engine. Restore them, or re-pin "
            "deliberately after finding out what changed upstream."
        )


def install(repo_root: Path, package_root: Path, lock: PromptLock) -> list[str]:
    """Put the pinned prompts where the engine looks for them.

    Idempotent, and it writes only what is absent or wrong: a file already
    matching the lock is left alone, so a second run copies nothing and the
    return value is the honest answer to "what did this run have to repair".

    Args:
        repo_root: This repository.
        package_root: The installed ``skillopt`` package directory.
        lock: What to install and what it must hash to.

    Returns:
        The paths it wrote, relative to the package. Empty when the install was
        already complete.
    """
    source = repo_root / VENDOR_ROOT
    written: list[str] = []
    for name, digest in lock.digests.items():
        target = package_root / name
        if target.is_file() and _sha256(target) == digest:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
        written.append(name)
    return written


def package_root() -> Path:
    """Where ``skillopt`` is installed.

    Raises:
        PromptError: It is not installed. The engine lives in the ``evolve``
            dependency group, which the gate never installs.
    """
    try:
        import skillopt
    except ImportError as exc:
        raise PromptError(
            "skillopt is not installed, so there is nowhere to restore its prompts to. "
            "It is in the `evolve` dependency group: run "
            "`python -m uv sync --group evolve`."
        ) from exc
    spec = skillopt.__file__
    if not spec:
        raise PromptError("skillopt is installed without a file location, which is not usable")
    return Path(spec).parent


def ensure_installed(repo_root: Path) -> list[str]:
    """Verify the vendored prompts and restore any the installed engine lacks.

    Called before a SkillOpt run rather than at import, because it writes into
    ``site-packages`` and that should happen when somebody asked for a search,
    not when something imported a module.

    Returns:
        What it had to write. A non-empty list on a fresh environment and an
        empty one thereafter.

    Raises:
        PromptError: The engine is absent, or the vendored copies are not the
            pinned ones.
    """
    lock = load_lock(repo_root)
    verify_vendored(repo_root, lock)
    return install(repo_root, package_root(), lock)
