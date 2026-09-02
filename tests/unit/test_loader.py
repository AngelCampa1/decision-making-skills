"""Tests for template loading."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from decision_evals.generators.loader import (
    TEMPLATE_ROOT,
    TemplateLoadError,
    load_all,
    load_template,
    parse_roots,
)

Build = Callable[..., dict[str, Any]]


def _write(directory: Path, name: str, payload: object) -> Path:
    path = directory / f"{name}.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return path


def test_a_valid_template_round_trips(tmp_path: Path, template_dict: Build) -> None:
    path = _write(tmp_path, "tst-001-example", template_dict())
    assert load_template(path).template_id == "tst-001-example"


def test_a_missing_file_is_a_load_error(tmp_path: Path) -> None:
    with pytest.raises(TemplateLoadError):
        load_template(tmp_path / "absent.yaml")


def test_malformed_yaml_is_a_load_error(tmp_path: Path) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("key: [unclosed\n", encoding="utf-8")
    with pytest.raises(TemplateLoadError):
        load_template(path)


def test_a_non_mapping_document_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, "listy", ["not", "a", "mapping"])
    with pytest.raises(TemplateLoadError, match="expected a mapping"):
        load_template(path)


def test_validation_errors_name_the_file(tmp_path: Path, template_dict: Build) -> None:
    """Pydantic names the field; when fifty templates load, you need the file."""
    path = _write(tmp_path, "tst-001-example", template_dict(options=["only"]))
    with pytest.raises(TemplateLoadError, match="tst-001-example"):
        load_template(path)


def test_the_id_must_match_the_filename(tmp_path: Path, template_dict: Build) -> None:
    """So a failing item id locates its template without a search."""
    path = _write(tmp_path, "tst-002-different", template_dict())
    with pytest.raises(TemplateLoadError, match="does not match the filename"):
        load_template(path)


def test_load_all_sorts_by_id(tmp_path: Path, template_dict: Build) -> None:
    _write(tmp_path, "tst-002-beta", template_dict(template_id="tst-002-beta"))
    _write(tmp_path, "tst-001-alpha", template_dict(template_id="tst-001-alpha"))
    assert [t.template_id for t in load_all(tmp_path)] == ["tst-001-alpha", "tst-002-beta"]


def test_load_all_rejects_a_non_directory(tmp_path: Path) -> None:
    with pytest.raises(TemplateLoadError, match="is not a directory"):
        load_all(tmp_path / "nope")


def test_load_all_rejects_an_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(TemplateLoadError, match="no templates found"):
        load_all(tmp_path)


def test_the_shipped_corpus_loads(tmp_path: Path) -> None:
    """Defaulting to the real template root is the common path; exercise it."""
    templates = load_all()
    assert len(templates) >= 10
    assert TEMPLATE_ROOT.is_dir()
    assert all(t.template_id.startswith("rel-") for t in templates)


HARD_ROOT = TEMPLATE_ROOT.parent / "templates-hard"


def test_two_roots_pool_and_stay_sorted(tmp_path: Path, template_dict: Build) -> None:
    """A study told two directories sees one corpus, in id order across both."""
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    _write(first, "tst-003-gamma", template_dict(template_id="tst-003-gamma"))
    _write(second, "tst-001-alpha", template_dict(template_id="tst-001-alpha"))
    _write(second, "tst-002-beta", template_dict(template_id="tst-002-beta"))
    ids = [t.template_id for t in load_all((first, second))]
    assert ids == ["tst-001-alpha", "tst-002-beta", "tst-003-gamma"]


def test_an_id_in_two_roots_is_refused(tmp_path: Path, template_dict: Build) -> None:
    """An item id names its template and nothing else does, so two files under
    one id would score under one name and neither could be told from the other."""
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    _write(first, "tst-001-alpha", template_dict(template_id="tst-001-alpha"))
    _write(second, "tst-001-alpha", template_dict(template_id="tst-001-alpha"))
    with pytest.raises(TemplateLoadError, match="is in both"):
        load_all((first, second))


def test_an_empty_root_list_is_refused() -> None:
    with pytest.raises(TemplateLoadError, match="no template root"):
        load_all(())


def test_a_missing_root_among_several_is_refused(tmp_path: Path, template_dict: Build) -> None:
    first = tmp_path / "first"
    first.mkdir()
    _write(first, "tst-001-alpha", template_dict(template_id="tst-001-alpha"))
    with pytest.raises(TemplateLoadError, match="is not a directory"):
        load_all((first, tmp_path / "absent"))


def test_the_shipped_corpora_pool_without_a_collision() -> None:
    """The two directories a re-run would pool. Their ids are disjoint by
    prefix, and this is where that stops being an assumption."""
    ids = [t.template_id for t in load_all((TEMPLATE_ROOT, HARD_ROOT))]
    assert len(ids) == len(set(ids))
    assert any(t.startswith("hrd-") for t in ids)
    assert any(t.startswith("rel-") for t in ids)


class TestParsingRoots:
    def test_a_comma_list_is_several_roots_under_the_base(self, tmp_path: Path) -> None:
        assert parse_roots("a,b", base=tmp_path) == (tmp_path / "a", tmp_path / "b")

    def test_blank_entries_are_dropped(self, tmp_path: Path) -> None:
        assert parse_roots(" a , ,b ,", base=tmp_path) == (tmp_path / "a", tmp_path / "b")

    def test_an_absolute_entry_is_left_alone(self, tmp_path: Path) -> None:
        elsewhere = tmp_path / "elsewhere"
        assert parse_roots(str(elsewhere), base=tmp_path / "base") == (elsewhere,)

    def test_nothing_named_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(TemplateLoadError, match="no template root"):
            parse_roots(" , ", base=tmp_path)

    def test_the_default_string_names_the_shipped_corpus(self) -> None:
        (root,) = parse_roots("datasets/templates")
        assert root == TEMPLATE_ROOT
