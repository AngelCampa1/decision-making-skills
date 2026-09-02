"""Loading templates from disk."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from pathlib import Path

import yaml
from pydantic import ValidationError

from decision_evals.generators.schema import Template

#: Repository root, four levels up from this file
#: (``evals/src/decision_evals/generators/loader.py``).
REPO_ROOT = Path(__file__).resolve().parents[4]

TEMPLATE_ROOT = REPO_ROOT / "datasets" / "templates"


class TemplateLoadError(ValueError):
    """A template file was missing, malformed, or failed validation."""


def load_template(path: Path) -> Template:
    """Load and validate one template file.

    Validation errors are re-raised with the file path attached. Pydantic's
    message alone names the field but not the file, and when a load of fifty
    templates fails, the file is the part you need.
    """
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise TemplateLoadError(f"{path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise TemplateLoadError(f"{path}: expected a mapping, got {type(raw).__name__}")
    try:
        template = Template.model_validate(raw)
    except ValidationError as exc:
        raise TemplateLoadError(f"{path}: {exc}") from exc

    if template.template_id != path.stem:
        raise TemplateLoadError(
            f"{path}: template_id {template.template_id!r} does not match the filename. "
            "They are kept identical so a template can be located from a failing item id."
        )
    return template


def parse_roots(spec: str, *, base: Path = REPO_ROOT) -> tuple[Path, ...]:
    """The template directories a comma-separated option names.

    ``datasets/templates,datasets/templates-hard`` loads both corpora. A
    relative entry is taken from ``base``, which the CLI sets to the repository
    root, so the string a run records in ``run.json`` reads the same on every
    machine. Blank entries are dropped.

    Raises:
        TemplateLoadError: No directory was named.
    """
    roots = tuple(
        (base / part.strip() if not Path(part.strip()).is_absolute() else Path(part.strip()))
        for part in spec.split(",")
        if part.strip()
    )
    if not roots:
        raise TemplateLoadError("no template root was named")
    return roots


def load_all(root: Path | Sequence[Path] | None = None) -> list[Template]:
    """Load every template under ``root``, sorted by id.

    Sorted rather than filesystem-ordered so that generation, golden files, and
    any pooled analysis see templates in the same sequence on every platform.

    A sequence of directories loads each in turn and pools them. Template ids
    stay unique across the pool: ``item_id`` carries the id and nothing else
    locates a template, so two files answering to one id would score under one
    name and neither could be told from the other.

    Raises:
        TemplateLoadError: A root is missing or empty, no root was given, or one
            id appears in two roots.
    """
    if root is None:
        directories: tuple[Path, ...] = (TEMPLATE_ROOT,)
    elif isinstance(root, Path):
        directories = (root,)
    else:
        directories = tuple(root)
    if not directories:
        raise TemplateLoadError("no template root was named")
    seen: dict[str, Path] = {}
    templates: list[Template] = []
    for directory in directories:
        if not directory.is_dir():
            raise TemplateLoadError(f"{directory} is not a directory")
        loaded = [load_template(path) for path in sorted(directory.glob("*.yaml"))]
        if not loaded:
            raise TemplateLoadError(f"no templates found in {directory}")
        for template in loaded:
            if template.template_id in seen:
                raise TemplateLoadError(
                    f"{template.template_id!r} is in both {seen[template.template_id]} and "
                    f"{directory}. Ids stay unique across roots because an item id names "
                    "its template and nothing else does."
                )
            seen[template.template_id] = directory
        templates.extend(loaded)
    return sorted(templates, key=lambda template: template.template_id)


def restrict(templates: Sequence[Template], ids: Collection[str]) -> list[Template]:
    """The templates ``ids`` names, in the order they were loaded.

    An empty ``ids`` is the whole corpus, which is what every run before
    2026-09-02 drew. A named subset is how a study leaves out the scenarios a
    screen found at chance for its target: an item no arm can answer is a pair
    that never discords, and it dilutes the denominator without moving the test.

    Raises:
        TemplateLoadError: An id no loaded template answers to. Dropping it
            would run a study over one scenario fewer than the registration
            names, under a manifest recording the registration's list.
    """
    if not ids:
        return list(templates)
    known = {template.template_id for template in templates}
    unknown = sorted(set(ids) - known)
    if unknown:
        raise TemplateLoadError(
            f"no template answers to {', '.join(unknown)}. The corpus holds "
            f"{', '.join(sorted(known))}."
        )
    wanted = set(ids)
    return [template for template in templates if template.template_id in wanted]
