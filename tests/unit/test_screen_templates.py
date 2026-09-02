"""Tests for `scripts/screen_templates.py`.

No model is called. The mock venue answers by hashing the prompt, which is a
coin, and a coin is the case the screen exists to detect: every template
should come out near chance with a J near zero. What is checked is the wiring
around that: items per template are spread over strata, the checkpoint resumes,
J is blank where it is undefined, and the numbers print per template.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from datetime import date
from pathlib import Path
from types import ModuleType

import pytest

from decision_evals.generators.generate import Item
from decision_evals.runner import RunRecord

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = REPO_ROOT / "datasets" / "templates"
MOCK = "mockllm/deterministic"


def _load() -> ModuleType:
    """Import ``scripts/screen_templates.py``, which is not part of the package."""
    path = REPO_ROOT / "scripts" / "screen_templates.py"
    spec = importlib.util.spec_from_file_location("screen_templates", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["screen_templates"] = module
    spec.loader.exec_module(module)
    return module


screen = _load()


@pytest.fixture
def two_templates(tmp_path: Path) -> Path:
    """A corpus of two shipped templates, copied so the test owns its root."""
    root = tmp_path / "templates"
    root.mkdir()
    for name in ("rel-001-vendor-outage.yaml", "rel-002-deploy-window.yaml"):
        shutil.copy(TEMPLATES / name, root / name)
    return root


def _record(template_id: str, expected: str, parsed: str | None) -> RunRecord:
    return RunRecord(
        item_id=f"{template_id}#v0-d0-none",
        template_id=template_id,
        arm="off",
        model="mockllm/deterministic",
        n_distractors=0,
        position="none",
        expected=expected,
        parsed=parsed,
        parse_status="parsed" if parsed is not None else "unparsed",
        correct=parsed == expected,
        zero_cause=None if parsed == expected else "agent_wrong",
        cost_usd=0.0,
        input_tokens=1,
        output_tokens=1,
        duration_ms=1,
        response="",
        seed=10_000,
    )


def _item(template_id: str, options: list[str]) -> Item:
    return Item(
        item_id=f"{template_id}#v0-d0-none",
        template_id=template_id,
        seed=10_000,
        variant=0,
        n_distractors=0,
        position="none",
        variables={},
        question="q",
        options=options,
        facts=[],
        answer=options[0],
        load_bearing=[],
        distractor_ids=[],
    )


class TestItemsPerTemplate:
    def test_every_template_gets_the_count_asked_for(self, two_templates: Path) -> None:
        items = screen.items_per_template((two_templates,), 10_000, 6)
        assert sorted(items) == ["rel-001-vendor-outage", "rel-002-deploy-window"]
        assert all(len(rows) == 6 for rows in items.values())

    def test_a_short_draw_spans_strata_rather_than_variants(self, two_templates: Path) -> None:
        """The first six items in generation order are one variant across six
        strata; the rotated draw is what a screen of six should see."""
        items = screen.items_per_template((two_templates,), 10_000, 6)
        rows = items["rel-001-vendor-outage"]
        assert len({(row.n_distractors, row.position) for row in rows}) > 1

    def test_the_whole_template_is_the_ceiling(self, two_templates: Path) -> None:
        items = screen.items_per_template((two_templates,), 10_000, 500)
        assert len(items["rel-001-vendor-outage"]) == 28


class TestReadingACheckpoint:
    def test_accuracy_counts_an_unparsed_answer_as_wrong(self) -> None:
        items = {"t": [_item("t", ["a", "b"])]}
        records = [_record("t", "a", "a"), _record("t", "b", None)]
        (reading,) = screen.read(records, items, MOCK)
        assert (reading.asked, reading.parsed, reading.correct) == (2, 1, 1)
        assert reading.accuracy == 0.5
        assert reading.parse_rate == 0.5

    def test_j_is_zero_for_a_constant_answer(self) -> None:
        """The number the screen exists for: a template a model answers the
        same way every time has no signal however its accuracy reads."""
        items = {"t": [_item("t", ["a", "b"])]}
        records = [_record("t", key, "a") for key in ("a", "a", "b", "b")]
        (reading,) = screen.read(records, items, MOCK)
        assert reading.accuracy == 0.5
        assert reading.informedness == 0.0

    def test_j_is_one_for_a_perfect_reader(self) -> None:
        items = {"t": [_item("t", ["a", "b"])]}
        records = [_record("t", key, key) for key in ("a", "a", "b", "b")]
        (reading,) = screen.read(records, items, MOCK)
        assert reading.informedness == 1.0

    def test_j_is_blank_with_more_than_two_options(self) -> None:
        items = {"t": [_item("t", ["a", "b", "c"])]}
        records = [_record("t", key, key) for key in ("a", "b", "c")]
        (reading,) = screen.read(records, items, MOCK)
        assert reading.informedness is None
        assert reading.accuracy == 1.0

    def test_j_is_blank_when_the_key_holds_one_class(self) -> None:
        items = {"t": [_item("t", ["a", "b"])]}
        records = [_record("t", "a", "a"), _record("t", "a", "b")]
        (reading,) = screen.read(records, items, MOCK)
        assert reading.informedness is None

    def test_j_is_blank_when_nothing_parsed(self) -> None:
        items = {"t": [_item("t", ["a", "b"])]}
        records = [_record("t", "a", None), _record("t", "b", None)]
        (reading,) = screen.read(records, items, MOCK)
        assert reading.informedness is None
        assert reading.parse_rate == 0.0

    def test_a_template_with_no_records_still_prints(self) -> None:
        items = {"t": [_item("t", ["a", "b"])], "u": [_item("u", ["a", "b"])]}
        readings = screen.read([_record("t", "a", "a")], items, MOCK)
        assert [(r.template_id, r.asked) for r in readings] == [("t", 1), ("u", 0)]
        assert readings[1].accuracy == 0.0

    def test_a_record_from_an_unknown_template_is_ignored(self) -> None:
        items = {"t": [_item("t", ["a", "b"])]}
        (reading,) = screen.read([_record("other", "a", "a")], items, MOCK)
        assert reading.asked == 0


class TestRendering:
    def test_the_table_names_every_template_and_blanks_an_undefined_j(self) -> None:
        readings = [
            screen.TemplateReading("t-one", asked=4, parsed=4, correct=2, informedness=0.0),
            screen.TemplateReading("t-two", asked=4, parsed=3, correct=3, informedness=None),
        ]
        text = screen.render(readings)
        lines = text.splitlines()
        assert lines[0].split() == ["template", "asked", "acc", "parse", "J"]
        assert "t-one" in lines[1]
        assert "+0.000" in lines[1]
        assert "t-two" in lines[2]
        assert lines[2].rstrip().endswith("0.750")


class TestTheScreenDirectory:
    def test_it_has_the_shape_every_run_directory_has(self, tmp_path: Path) -> None:
        path = screen.screen_dir(tmp_path, "abcdef0123456", 10_000, on=date(2026, 9, 2))
        assert path == tmp_path / "results" / "screens" / "2026-09-02-abcdef0-s10000-templates"


class TestRunningTheScreen:
    def test_it_answers_every_item_and_prints_per_template(
        self, two_templates: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = tmp_path / "screen"
        code = screen.main(
            [
                "--templates-root",
                str(two_templates),
                "--items-per-template",
                "28",
                "--out",
                str(out),
            ]
        )
        assert code == 0
        printed = capsys.readouterr().out
        assert "rel-001-vendor-outage" in printed
        assert "rel-002-deploy-window" in printed
        records = [
            json.loads(line)
            for line in (out / "records.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(records) == 56
        assert {r["arm"] for r in records} == {"off"}
        manifest = json.loads((out / "run.json").read_text(encoding="utf-8"))
        assert manifest["items_per_template"] == 28
        assert manifest["templates"] == ["rel-001-vendor-outage", "rel-002-deploy-window"]
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        assert [row["template_id"] for row in summary] == manifest["templates"]
        assert all(row["asked"] == 28 for row in summary)
        assert all(row["informedness"] is not None for row in summary)

    def test_a_second_run_resumes_rather_than_re_asking(
        self, two_templates: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "screen"
        args = [
            "--templates-root",
            str(two_templates),
            "--items-per-template",
            "3",
            "--out",
            str(out),
        ]
        screen.main(args)
        before = (out / "records.jsonl").read_bytes()
        screen.main(args)
        assert (out / "records.jsonl").read_bytes() == before

    def test_zero_items_per_template_is_refused(self, two_templates: Path, tmp_path: Path) -> None:
        with pytest.raises(SystemExit, match="at least 1"):
            screen.main(
                [
                    "--templates-root",
                    str(two_templates),
                    "--items-per-template",
                    "0",
                    "--out",
                    str(tmp_path / "screen"),
                ]
            )

    def test_the_default_directory_is_under_results_screens(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Without `--out`, the checkpoint lands where `.gitignore` and
        `provenance.WORKING_DIRS` both expect it."""
        seen: dict[str, Path] = {}

        def fake_run(**kwargs: object) -> list[object]:
            seen["out"] = kwargs["out"]  # type: ignore[assignment]
            return []

        monkeypatch.setattr(screen, "run", fake_run)
        monkeypatch.setattr(screen, "_head", lambda root: "0123456789abcdef")
        assert screen.main(["--items-per-template", "1"]) == 0
        assert seen["out"].parent == REPO_ROOT / "results" / "screens"
        assert seen["out"].name.endswith("-0123456-s10000-templates")

    def test_outside_a_repository_there_is_no_directory_to_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import subprocess

        def failing(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(args=[], returncode=128, stdout="", stderr="")

        monkeypatch.setattr(screen.subprocess, "run", failing)
        with pytest.raises(SystemExit, match="not a git repository"):
            screen.main([])


class TestTwoScreensDoNotPool:
    """The checkpoint resumes on the study's key and the manifest overwrites,
    so a second screen into the first's directory would print numbers over
    both. Each of these is a way that happened or could."""

    def test_the_default_directory_carries_the_seed(self, tmp_path: Path) -> None:
        path = screen.screen_dir(tmp_path, "abcdef0123456", 10_007, on=date(2026, 9, 2))
        assert path.name == "2026-09-02-abcdef0-s10007-templates"

    def test_reading_ignores_another_seed_and_another_model(self) -> None:
        items = {"t": [_item("t", ["a", "b"])]}
        mine = _record("t", "a", "a")
        other_seed = RunRecord(**{**mine.__dict__, "seed": 10_001, "correct": False, "parsed": "b"})
        other_model = RunRecord(**{**mine.__dict__, "model": "ollama/x", "parsed": "b"})
        (reading,) = screen.read([mine, other_seed, other_model], items, mine.model)
        assert (reading.asked, reading.correct) == (1, 1)

    def _args(self, root: Path, out: Path, *extra: str) -> list[str]:
        return [
            "--templates-root",
            str(root),
            "--items-per-template",
            "2",
            "--out",
            str(out),
            *extra,
        ]

    def test_another_seed_into_the_same_directory_is_refused(
        self, two_templates: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "screen"
        screen.main(self._args(two_templates, out, "--seed", "10000"))
        before = (out / "run.json").read_bytes()
        with pytest.raises(SystemExit, match="different seed"):
            screen.main(self._args(two_templates, out, "--seed", "10001"))
        assert (out / "run.json").read_bytes() == before

    def test_another_target_or_count_is_refused(self, two_templates: Path, tmp_path: Path) -> None:
        out = tmp_path / "screen"
        screen.main(self._args(two_templates, out))
        with pytest.raises(SystemExit, match="different items_per_template"):
            screen.main(
                [
                    "--templates-root",
                    str(two_templates),
                    "--items-per-template",
                    "3",
                    "--out",
                    str(out),
                ]
            )
        (out / "run.json").write_text(
            json.dumps(
                {
                    **json.loads((out / "run.json").read_text(encoding="utf-8")),
                    "target_model": "ollama/other",
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(SystemExit, match="different target_model"):
            screen.main(self._args(two_templates, out))

    def test_the_same_screen_resumes(self, two_templates: Path, tmp_path: Path) -> None:
        out = tmp_path / "screen"
        screen.main(self._args(two_templates, out))
        before = (out / "records.jsonl").read_bytes()
        assert screen.main(self._args(two_templates, out)) == 0
        assert (out / "records.jsonl").read_bytes() == before
