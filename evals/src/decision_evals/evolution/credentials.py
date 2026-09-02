"""Keys a run may not leave behind.

Three sets of files land in a run directory. This package writes the manifest
and the winner; the engine writes its own configuration, its own summary and its
own logs; and the engine's redactor matches three exact key names, none of them
the flattened name this harness passes it. On 2026-09-02 a SkillOpt search put a
live NVIDIA Build key in plaintext into ``<run>/skillopt/config.json`` and
``<run>/skillopt/summary.json`` under ``optimizer_azure_openai_api_key``, inside
the repository tree, while ``run.json`` beside it was clean.

So the redaction happens here, over the files as they sit on disk, once the
search is over and the engine's directory is final. :func:`redacted` is what the
manifest goes through and what the walk reuses, so one function answers what a
secret looks like. :func:`scrub` rewrites the engine's JSON in place,
:func:`credential_files` reads a whole directory back and names whatever still
matches, and :func:`assert_clean` turns that list into a refusal.

The second half is the half that matters. Redaction that quietly missed a file
would read exactly like redaction that worked, and ``.gitignore`` is the only
thing between ``results/evolution/`` and a public repository: the evolution
study's registration asks for search artefacts to be committed, so one
``git add -f`` on a search directory publishes whatever is in it.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

#: What a redacted value reads as. The same marker the manifest has always used,
#: so a reader of either file sees one thing.
REDACTED: Final = "<redacted>"

#: Key-name fragments that make a string value a secret whatever it looks like.
#: Matched as substrings and case-insensitively, because the names arrive from
#: an engine's own flattening: ``optimizer_azure_openai_api_key`` is one key.
SECRET_NAMES: Final[tuple[str, ...]] = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "credential",
)

#: The shortest run of key characters read as opaque. Below this a random-looking
#: string is likelier to be an identifier than a credential.
MIN_OPAQUE: Final = 32

#: Credentials that announce themselves. NVIDIA Build issues ``nvapi-``, which is
#: the key this repository actually uses; the rest are here because a reflector
#: venue can change and a scan that only knew one vendor would go quiet.
_PREFIXED: Final = re.compile(
    r"(?:nvapi-|sk-ant-|sk-|github_pat_|ghp_|gho_|xox[abps]-|AIza)[A-Za-z0-9_\-]{12,}"
)

#: Any long unbroken run of the characters a key is built from.
#: :func:`_opaque` decides which of them look random rather than merely long.
_RUN: Final = re.compile(rf"[A-Za-z0-9_\-]{{{MIN_OPAQUE},}}")

#: What :func:`scrub` rewrites. Everything else in a run directory is read and
#: reported rather than edited: a candidate body or a log line is a record, and
#: silently editing one to make a scan pass would cost more than it saves.
JSON_SUFFIXES: Final[frozenset[str]] = frozenset({".json", ".jsonl"})


class CredentialError(RuntimeError):
    """A credential is on disk somewhere a run wrote."""


def secret_name(key: str) -> bool:
    """Whether a key's name alone makes its string value a secret."""
    lowered = key.lower()
    return any(fragment in lowered for fragment in SECRET_NAMES)


def _opaque(token: str) -> bool:
    """Whether a long run of key characters carries the mix a random key has.

    Upper case, lower case and a digit, all three. A git sha is lower case and
    digits, a template id is lower case and hyphens, and a scan that flagged
    either would fire on every lineage this repository has written.
    """
    return (
        any(character.isupper() for character in token)
        and any(character.islower() for character in token)
        and any(character.isdigit() for character in token)
    )


def credential_shaped(value: str) -> bool:
    """Whether some substring of ``value`` reads as a credential."""
    return bool(_PREFIXED.search(value)) or any(_opaque(run) for run in _RUN.findall(value))


def scrub_text(value: str) -> str:
    """``value`` with every credential-shaped substring replaced.

    A substring rather than the whole string, so a log line keeps its sentence
    and an endpoint keeps its host.
    """
    without_known = _PREFIXED.sub(REDACTED, value)
    return _RUN.sub(
        lambda match: REDACTED if _opaque(match.group()) else match.group(), without_known
    )


def _scrubbed(value: Any, *, key: str = "") -> Any:
    """One JSON value with its secrets removed, containers included.

    A string under a secret-looking key goes whole, because the name is a
    stronger signal than the shape: ``"dummy"`` under ``target_azure_openai_api_key``
    is a placeholder today and a real key after one edit. Every other string is
    read for the shape instead.

    Numbers are left alone even under a name that matches. ``max_tokens`` and
    ``token_summary`` are the engine's own counts, and a summary that reported
    ``<redacted>`` where the token spend goes would have lost the record to
    protect nothing.
    """
    if isinstance(value, Mapping):
        return {name: _scrubbed(item, key=str(name)) for name, item in value.items()}
    if isinstance(value, list):
        return [_scrubbed(item) for item in value]
    if isinstance(value, str):
        return REDACTED if key and secret_name(key) else scrub_text(value)
    return value


def redacted(config: Mapping[str, Any]) -> dict[str, Any]:
    """The mapping with every secret removed, for a file that gets written.

    Keys live in the environment and never in the tree, and a manifest is a
    file. Nested mappings and lists are walked, because an engine's summary
    carries the whole config one level down.
    """
    return {key: _scrubbed(value, key=str(key)) for key, value in config.items()}


def _scrubbed_json(text: str) -> str | None:
    """One JSON document redacted, or ``None`` when nothing in it was a secret.

    Reformatting is what ``None`` avoids. Re-dumping a file whose data did not
    change would rewrite an engine's own indentation and separators, and a diff
    that large hides the one line that mattered.
    """
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        cleaned = scrub_text(text)
        # A half-written file, which is what a killed search leaves. It cannot be
        # parsed and it can still hold a key, so it is scrubbed as text.
        return None if cleaned == text else cleaned
    cleaned_value = _scrubbed(loaded)
    if cleaned_value == loaded:
        return None
    body = json.dumps(cleaned_value, indent=2, ensure_ascii=False)
    return f"{body}\n" if text.endswith("\n") else body


def _scrubbed_lines(text: str) -> str | None:
    """A JSON-lines file redacted line by line, or ``None`` when it was clean.

    Untouched lines are kept verbatim rather than re-dumped, so a checkpoint
    that carried nothing keeps the bytes a resume reads.
    """
    rewritten: list[str] = []
    changed = False
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        ending = line[len(line.rstrip("\r\n")) :]
        if not stripped:
            rewritten.append(line)
            continue
        try:
            loaded = json.loads(stripped)
        except json.JSONDecodeError:
            cleaned_line = scrub_text(line)
            changed = changed or cleaned_line != line
            rewritten.append(cleaned_line)
            continue
        cleaned_value = _scrubbed(loaded)
        if cleaned_value == loaded:
            rewritten.append(line)
            continue
        changed = True
        rewritten.append(json.dumps(cleaned_value, ensure_ascii=False) + ending)
    return "".join(rewritten) if changed else None


def scrub(directory: Path) -> list[Path]:
    """Redact the JSON under ``directory`` in place, and say which files moved.

    Returns an empty list for a directory that does not exist, which is the
    ordinary case for an engine that never got as far as writing one.
    """
    if not directory.is_dir():
        return []
    moved: list[Path] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix not in JSON_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Not text, whatever the suffix says. :func:`credential_files` reads
            # it as bytes afterwards, so it is checked rather than skipped.
            continue
        cleaned = _scrubbed_lines(text) if path.suffix == ".jsonl" else _scrubbed_json(text)
        if cleaned is not None:
            path.write_text(cleaned, encoding="utf-8")
            moved.append(path)
    return moved


def _carries(path: Path) -> bool:
    """Whether one file reads as though it holds a credential.

    A file that is not UTF-8 is read with the undecodable bytes replaced and
    checked against the vendor prefixes alone. GEPA pickles its state, and a
    pickle of English prose is mostly ASCII, so the prefix rule reaches it; the
    opaque rule would read binary padding as a key and refuse every run.
    """
    try:
        return credential_shaped(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return bool(_PREFIXED.search(path.read_text(encoding="utf-8", errors="replace")))


def credential_files(directory: Path) -> list[Path]:
    """Every file under ``directory`` carrying a credential-shaped string.

    The other direction from :func:`scrub`, and public for that reason: a gate
    step or a check run before anything is committed can ask this about a
    directory without knowing which engine wrote it.
    """
    if not directory.is_dir():
        return []
    return [path for path in sorted(directory.rglob("*")) if path.is_file() and _carries(path)]


def assert_clean(directory: Path) -> None:
    """Refuse a directory that still holds something shaped like a credential.

    Raises:
        CredentialError: Naming every file, relative to ``directory``. A run
            that cannot be made safe stops here rather than returning a result
            somebody will commit.
    """
    carriers = credential_files(directory)
    if not carriers:
        return
    named = ", ".join(str(path.relative_to(directory)) for path in carriers)
    raise CredentialError(
        f"{len(carriers)} file(s) under {directory} still read as though they carry a "
        f"credential: {named}. Redaction ran over the engine's JSON and did not reach "
        "these, so the key is on disk in a directory a study is registered to commit. "
        "Rotate the key, then delete or redact the files by hand."
    )
