"""Tests for the paper's number generator.

Two jobs here. The first is the ordinary one: every refusal branch has a test
that makes it refuse. The second matters more — a class of test that asserts the
generated macros equal the published record, because the whole point of `de
figures` is that the PDF cannot disagree with `results/`, and a renderer nobody
compares against its source is exactly the drift the arrangement exists to
prevent.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from decision_evals.figures import (
    LOW_SIGNAL_J,
    FigureError,
    Reading,
    arm_order,
    collect,
    informedness_deltas,
    latest_run,
    load_readings,
    low_signal_templates,
    read_study,
    render_accuracy_plot,
    render_macros,
    render_signal_plot,
    render_tables,
    signal_by_arm,
    write_figures,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISHED = "2026-08-27-53b4965-five-arm"

ARMS = ("off", "on", "candidate")

# Three templates and what each one is for. `t-quiet` is answered by a coin, so
# every arm reads near zero on it and it is the low-signal case. `t-onesided`
# has a key holding a single answer class, which is the case informedness
# refuses and skew does not.
TEMPLATES = ("t-good", "t-quiet", "t-onesided")


def _row(
    arm: str, template: str, index: int, expected: str, parsed: str | None
) -> dict[str, object]:
    return {
        "arm": arm,
        "item_id": f"{template}#v{index}",
        "template_id": template,
        "seed": 1000,
        "expected": expected,
        "parsed": parsed,
        "parse_status": "parsed" if parsed is not None else "unparsed",
    }


def _write_run(root: Path, *, arms: tuple[str, ...] = ARMS, aa: bool = True) -> Path:
    """A study directory small enough to reason about and shaped like the real one."""
    run_dir = root / "results" / "evolution-study" / "2026-01-01-abcdef0-fixture"
    run_dir.mkdir(parents=True)

    keys = {
        # Balanced, and read correctly by every arm.
        "t-good": ["a", "a", "b", "b"],
        # Balanced, and answered "a" throughout: accuracy 0.5, informedness 0.
        "t-quiet": ["a", "a", "b", "b"],
        # One answer class, so J is undefined here and skew is not.
        "t-onesided": ["a", "a", "a", "a"],
    }
    answers = {
        "t-good": ["a", "a", "b", "b"],
        "t-quiet": ["a", "a", "a", "a"],
        "t-onesided": ["a", "b", "a", "a"],
    }

    for arm in arms:
        rows = [
            _row(arm, template, index, keys[template][index], answers[template][index])
            for template in TEMPLATES
            for index in range(4)
        ]
        # One unanswered reading per arm, so the parse rate is not trivially 1.
        rows.append(_row(arm, "t-good", 9, "a", None))
        text = "\n".join(json.dumps(row) for row in rows)
        # A trailing blank line, which the real checkpoints also carry.
        (run_dir / f"records-{arm}.jsonl").write_text(text + "\n\n", encoding="utf-8")

    if aa:
        # Never counted. Present so the test proves it is skipped rather than
        # proving nothing about a file that was not there.
        (run_dir / "records-aa.jsonl").write_text(
            json.dumps(_row("placebo", "t-good", 0, "a", "a")) + "\n", encoding="utf-8"
        )

    analysis: dict[str, object] = {
        "control": "on",
        "sets": [
            {
                "label": "unseen",
                "n_items": 12,
                "accuracy": dict.fromkeys(arms, 0.5),
                "comparisons": [
                    {
                        "arm": "candidate",
                        "accuracy": 0.5,
                        "control_accuracy": 0.4,
                        "arm_only": 3,
                        "control_only": 1,
                        "p_value": 0.25,
                        "adjusted": 0.5,
                    }
                ],
            }
        ],
    }
    if aa:
        analysis["aa"] = {
            "n_pairs": 12,
            "arm_only": 0,
            "control_only": 0,
            "p_value": 1.0,
            "accuracy": 0.5,
        }
    (run_dir / "analysis.json").write_text(json.dumps(analysis), encoding="utf-8")
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "request": {"target_model": "fixture/model"},
                "arms": [{"label": arm} for arm in arms],
            }
        ),
        encoding="utf-8",
    )
    return run_dir


class TestFindingARun:
    def test_no_results_directory_is_not_an_error(self, tmp_path: Path) -> None:
        """A bare checkout still builds the paper, which the Makefile promises."""
        assert latest_run(tmp_path) is None

    def test_a_results_directory_holding_no_run_is_not_an_error(self, tmp_path: Path) -> None:
        (tmp_path / "results" / "evolution-study").mkdir(parents=True)
        assert latest_run(tmp_path) is None

    def test_the_latest_run_wins(self, tmp_path: Path) -> None:
        root = tmp_path / "results" / "evolution-study"
        for name in ("2026-01-01-aaaaaaa-first", "2026-06-01-bbbbbbb-second"):
            (root / name).mkdir(parents=True)
            (root / name / "analysis.json").write_text("{}", encoding="utf-8")
        found = latest_run(tmp_path)
        assert found is not None
        assert found.name == "2026-06-01-bbbbbbb-second"

    def test_a_directory_without_an_analysis_is_not_a_run(self, tmp_path: Path) -> None:
        (tmp_path / "results" / "evolution-study" / "half-written").mkdir(parents=True)
        assert latest_run(tmp_path) is None


class TestReadingRecords:
    def test_the_arm_comes_from_the_file_name(self, tmp_path: Path) -> None:
        """The record's own `arm` field holds the kind, and two arms share one.

        Both evolved winners are of kind `candidate`. Reading that field merges
        them into a single arm whose every number is a blend of two.
        """
        run_dir = _write_run(tmp_path)
        arms = {reading.arm for reading in load_readings(run_dir)}
        assert arms == set(ARMS)

    def test_the_aa_pass_is_left_out(self, tmp_path: Path) -> None:
        run_dir = _write_run(tmp_path)
        assert not any(reading.arm == "aa" for reading in load_readings(run_dir))
        assert len(load_readings(run_dir)) == len(ARMS) * 13

    def test_an_unparsed_reading_carries_no_answer(self, tmp_path: Path) -> None:
        run_dir = _write_run(tmp_path)
        unparsed = [r for r in load_readings(run_dir) if r.parsed is None]
        assert len(unparsed) == len(ARMS)

    def test_a_run_with_no_arm_records_refuses(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "empty"
        run_dir.mkdir()
        with pytest.raises(FigureError, match="no arm records"):
            load_readings(run_dir)

    def test_an_item_is_a_seed_and_an_id_together(self) -> None:
        """`item_id` does not encode the seed, so alone it collapses the seeds."""
        first = Reading("off", "x#v0", "x", 1000, "a", "a")
        second = Reading("off", "x#v0", "x", 1001, "a", "a")
        assert first.item != second.item
        assert first.item == (1000, "x#v0")


class TestSignal:
    def test_a_one_class_template_is_dropped_rather_than_scored_zero(self, tmp_path: Path) -> None:
        run_dir = _write_run(tmp_path)
        signals = signal_by_arm(load_readings(run_dir), ARMS)
        assert set(signals["off"].per_template) == {"t-good", "t-quiet"}

    def test_the_measures_split_a_template_accuracy_cannot(self, tmp_path: Path) -> None:
        run_dir = _write_run(tmp_path)
        signals = signal_by_arm(load_readings(run_dir), ARMS)
        assert signals["off"].per_template["t-good"] == pytest.approx(1.0)
        assert signals["off"].per_template["t-quiet"] == pytest.approx(0.0)

    def test_the_parse_rate_counts_every_reading_asked_for(self, tmp_path: Path) -> None:
        run_dir = _write_run(tmp_path)
        signals = signal_by_arm(load_readings(run_dir), ARMS)
        assert signals["off"].parse_rate == pytest.approx(12 / 13)

    def test_the_arms_come_back_in_the_order_the_study_registered_them(
        self, tmp_path: Path
    ) -> None:
        run_dir = _write_run(tmp_path)
        manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        assert arm_order(manifest) == list(ARMS)
        assert list(signal_by_arm(load_readings(run_dir), ARMS)) == list(ARMS)

    def test_an_arm_the_manifest_names_and_no_file_carries_refuses(self, tmp_path: Path) -> None:
        run_dir = _write_run(tmp_path)
        with pytest.raises(FigureError, match="ghost"):
            signal_by_arm(load_readings(run_dir), [*ARMS, "ghost"])

    def test_an_arm_with_no_measurable_template_refuses(self, tmp_path: Path) -> None:
        """Reporting a mean over nothing is worse than declining to report one."""
        run_dir = tmp_path / "onesided"
        run_dir.mkdir()
        rows = [_row("off", "t-onesided", i, "a", "a") for i in range(4)]
        (run_dir / "records-off.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows), encoding="utf-8"
        )
        with pytest.raises(FigureError, match="both answer classes"):
            signal_by_arm(load_readings(run_dir), ["off"])

    def test_the_baseline_is_not_differenced_against_itself(self, tmp_path: Path) -> None:
        run_dir = _write_run(tmp_path)
        deltas = informedness_deltas(signal_by_arm(load_readings(run_dir), ARMS))
        assert [delta.arm for delta in deltas] == ["on", "candidate"]

    def test_identical_arms_have_no_difference_to_report(self, tmp_path: Path) -> None:
        """Every arm here answers identically, so every delta is exactly zero."""
        run_dir = _write_run(tmp_path)
        deltas = informedness_deltas(signal_by_arm(load_readings(run_dir), ARMS))
        assert all(delta.estimate == pytest.approx(0.0) for delta in deltas)

    def test_a_template_no_arm_discriminates_on_is_named(self, tmp_path: Path) -> None:
        run_dir = _write_run(tmp_path)
        signals = signal_by_arm(load_readings(run_dir), ARMS)
        assert low_signal_templates(signals) == ["t-quiet"]
        assert signals["off"].per_template["t-quiet"] < LOW_SIGNAL_J


class TestMacros:
    def test_a_name_latex_cannot_define_refuses(self, tmp_path: Path) -> None:
        """`newcommand` takes letters. A digit in an arm label breaks the build."""
        run_dir = _write_run(tmp_path, arms=("off", "arm2"))
        with pytest.raises(FigureError, match="letters only"):
            collect(read_study(run_dir))

    def test_every_reported_number_matches_the_published_record(self) -> None:
        """The generator is a renderer, and this is the assertion that says so.

        `analysis.json` is the record. Anything the paper prints that this file
        does not hold is a number nothing checked.
        """
        run_dir = REPO_ROOT / "results" / "evolution-study" / PUBLISHED
        values = collect(read_study(run_dir))
        analysis = json.loads((run_dir / "analysis.json").read_text(encoding="utf-8"))

        for item_set in analysis["sets"]:
            label = item_set["label"].capitalize()
            for arm, accuracy in item_set["accuracy"].items():
                assert values[f"acc{label}{arm.capitalize()}"] == f"{accuracy:.4f}"
            for comparison in item_set["comparisons"]:
                arm = comparison["arm"].capitalize()
                assert values[f"p{label}{arm}"] == f"{comparison['p_value']:.4f}"
                assert values[f"q{label}{arm}"] == f"{comparison['adjusted']:.4f}"

    def test_the_item_counts_are_items_and_not_calls(self) -> None:
        """728 items over five arms is 3,640 readings, and the two are not one."""
        values = collect(read_study(REPO_ROOT / "results" / "evolution-study" / PUBLISHED))
        assert values["totalItems"] == "728"
        assert values["studyReadings"] == "3640"
        assert values["unseenItems"] == "336"
        assert values["seenItems"] == "392"

    def test_the_low_signal_split_adds_back_up(self) -> None:
        values = collect(read_study(REPO_ROOT / "results" / "evolution-study" / PUBLISHED))
        assert int(values["lowSignalItems"]) + int(values["signalItems"]) == int(
            values["totalItems"]
        )
        assert values["lowSignalTemplates"] == "3"

    def test_a_run_without_an_aa_pass_defines_no_aa_macros(self, tmp_path: Path) -> None:
        run_dir = _write_run(tmp_path, aa=False)
        values = collect(read_study(run_dir))
        assert not any(name.startswith("aa") for name in values)

    def test_an_aa_pass_is_reported_as_disagreements(self, tmp_path: Path) -> None:
        values = collect(read_study(_write_run(tmp_path)))
        assert values["aaDisagreements"] == "0"
        assert values["aaPairs"] == "12"

    def test_an_empty_macro_file_is_still_a_macro_file(self) -> None:
        text = render_macros({})
        assert "Do not edit" in text
        assert "newcommand" not in text


class TestRendering:
    def test_the_control_arm_gets_no_comparison_against_itself(self, tmp_path: Path) -> None:
        tables = render_tables(read_study(_write_run(tmp_path)))
        assert "\\texttt{on} & \\accUnseenOn & --- & --- & --- & --- \\\\" in tables

    def test_the_baseline_gets_no_delta_against_itself(self, tmp_path: Path) -> None:
        tables = render_tables(read_study(_write_run(tmp_path)))
        assert "\\texttt{off} & \\parseRateOff & \\meanJOff & --- & ---" in tables

    def test_a_low_signal_template_is_marked_in_the_table(self, tmp_path: Path) -> None:
        tables = render_tables(read_study(_write_run(tmp_path)))
        assert "\\texttt{t-quiet}$^{\\dagger}$" in tables
        assert "\\texttt{t-good} &" in tables

    def test_a_template_an_arm_could_not_measure_reads_as_absent(self, tmp_path: Path) -> None:
        """An unmeasurable cell is a dash. Writing 0.000 there would be a claim."""
        run_dir = _write_run(tmp_path)
        study = read_study(run_dir)
        crippled = dict(study.signals)
        thin = crippled["on"]
        crippled["on"] = type(thin)(
            arm=thin.arm,
            parse_rate=thin.parse_rate,
            mean_informedness=thin.mean_informedness,
            mean_skew=thin.mean_skew,
            per_template={"t-good": thin.per_template["t-good"]},
        )
        tables = render_tables(
            type(study)(
                run=study.run,
                analysis=study.analysis,
                manifest=study.manifest,
                readings=study.readings,
                signals=crippled,
                deltas=study.deltas,
            )
        )
        assert "\\texttt{t-quiet}" in tables
        assert "---" in tables

    def test_the_plots_are_text_and_name_every_arm(self, tmp_path: Path) -> None:
        study = read_study(_write_run(tmp_path))
        accuracy = render_accuracy_plot(study)
        signal = render_signal_plot(study)
        assert "\\begin{tikzpicture}" in accuracy
        assert all(arm in accuracy for arm in ARMS)
        assert "error bars" in signal
        assert "candidate" in signal


class TestWriting:
    def test_nothing_published_still_writes_a_buildable_macro_file(self, tmp_path: Path) -> None:
        result = write_figures(tmp_path, tmp_path / "paper")
        assert result.run is None
        assert result.macros == 0
        assert (tmp_path / "paper" / "generated" / "macros.tex").is_file()

    def test_a_published_run_writes_four_artefacts(self, tmp_path: Path) -> None:
        _write_run(tmp_path)
        result = write_figures(tmp_path, tmp_path / "paper")
        assert result.run == "2026-01-01-abcdef0-fixture"
        assert result.macros > 0
        assert {path.name for path in result.paths} == {
            "macros.tex",
            "tables.tex",
            "accuracy.tex",
            "signal.tex",
        }

    def test_a_second_build_writes_the_same_bytes(self, tmp_path: Path) -> None:
        """A published interval that moves between builds is not a published one."""
        _write_run(tmp_path)
        write_figures(tmp_path, tmp_path / "paper")
        first = (tmp_path / "paper" / "generated" / "macros.tex").read_bytes()
        write_figures(tmp_path, tmp_path / "paper")
        assert (tmp_path / "paper" / "generated" / "macros.tex").read_bytes() == first
