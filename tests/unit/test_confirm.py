"""Tests for the confirm pathway: the caller, not the locks.

``decision_evals.prereg`` already has a test per refusal in
``test_locks.py``. What had no test, and no caller, was anything that *reaches*
those refusals. A refusal branch at 100% coverage with nothing calling it is
tested, proven and inert, which is the defect ``de check``'s integrity wiring
step exists to refuse.

So these tests assert three things the locks themselves cannot. That
``de confirm`` gathers real git facts and hands them over. That every way the
command can stop actually stops it. And that the pre-registration this
repository ships validates against the model and hashes what it says it hashes.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml
from typer.testing import CliRunner

from decision_evals import cli
from decision_evals.cli import PREREGISTRATION_MARKER, app, confirmation_runs
from decision_evals.decisions import GOVERNED
from decision_evals.prereg import sha256_text

runner = CliRunner()

SKILL = "# Decision making\nRead one procedure.\n"
ANALYSIS = "def analyse() -> int:\n    return 1\n"
SKILL_NAME = "decision-making"


def _prereg_dict(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "skill": SKILL_NAME,
        "version": 1,
        "hypothesis": "The shipped description fires on holdout decision turns.",
        "primary_metric": "trigger_recall",
        "n_items": 330,
        "minimum_detectable_effect": 0.086,
        "alpha": 0.05,
        "guards": ["no_harm_clean", "format_integrity", "cost"],
        "stopping_rule": "fixed N, no interim analysis",
        "difficulty_band": [0.35, 0.75],
        "budget_usd": 7.43,
        "skill_sha256": sha256_text(SKILL),
        "analysis_script_sha256": sha256_text(ANALYSIS),
    }
    base.update(overrides)
    return base


@pytest.fixture
def repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """A tree shaped like this repository, with a clean committed history.

    ``resolve()`` because the command resolves the pre-registration path before
    taking it relative to the root, and a Windows temporary directory arrives
    through a short-name alias that never matches an unresolved root.
    """
    root = tmp_path.resolve()
    (root / "skills" / SKILL_NAME).mkdir(parents=True)
    (root / "skills" / SKILL_NAME / "SKILL.md").write_text(SKILL, encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts" / "run_triggers.py").write_text(ANALYSIS, encoding="utf-8")
    (root / "preregistration").mkdir()
    (root / "preregistration" / f"{SKILL_NAME}-v1.yaml").write_text(
        yaml.safe_dump(_prereg_dict()), encoding="utf-8"
    )

    monkeypatch.setattr(cli, "REPO_ROOT", root)
    monkeypatch.setattr(cli, "_is_ancestor", lambda ancestor, descendant: True)
    monkeypatch.setattr(cli, "_git_output", _clean_repo)
    return root


def _clean_repo(args: list[str]) -> str | None:
    """A git that reports the pre-registration committed, clean and on history."""
    if args[0] == "status":
        return ""
    return "a1b2c3d4e5f6"


def _confirm(root: Path, *extra: str) -> Any:
    return runner.invoke(
        app,
        [
            "confirm",
            str(root / "preregistration" / f"{SKILL_NAME}-v1.yaml"),
            "--baseline-accuracy",
            "0.55",
            "--projected-cost",
            "7.42",
            *extra,
        ],
    )


# ===========================================================================
# Reaching the locks
# ===========================================================================


class TestTheLocksAreReached:
    def test_a_run_with_no_holdout_stops_after_the_locks_hold(self, repo: Path) -> None:
        """The refusal this pathway exists to produce today.

        Both hash locks match and the commit facts are clean, so every check in
        ``assert_runnable`` ran and passed. What stops the run is the split.
        """
        result = _confirm(repo)
        assert result.exit_code == 1
        assert "both hash locks match" in result.output
        assert "holdout split and there is none on disk" in result.output

    def test_the_holdout_readme_is_not_a_holdout(self, repo: Path) -> None:
        """The real directory holds a README and no records, and must read as empty.

        A looser pattern here would take that README for a split, report the
        holdout present, and stop on the wrong sentence. ``HOLDOUT_GLOB`` is the
        same pattern ``.gitignore`` excludes, which is what keeps a real split
        both visible here and uncommittable.
        """
        (repo / "datasets" / "holdout").mkdir(parents=True)
        (repo / "datasets" / "holdout" / "README.md").write_text("# empty\n", encoding="utf-8")
        result = _confirm(repo)
        assert result.exit_code == 1
        assert "there is none on disk" in result.output

    def test_a_holdout_on_disk_stops_on_the_missing_runner_instead(self, repo: Path) -> None:
        """The other side of the same branch, so neither arm is a claim nobody checked."""
        (repo / "datasets" / "holdout").mkdir(parents=True)
        (repo / "datasets" / "holdout" / "turns.jsonl").write_text("{}\n", encoding="utf-8")
        result = _confirm(repo)
        assert result.exit_code == 1
        assert "no runner reads it yet" in result.output

    def test_one_changed_character_in_the_skill_reaches_the_hash_lock(self, repo: Path) -> None:
        """The lock the whole design turns on, fired through the command."""
        (repo / "skills" / SKILL_NAME / "SKILL.md").write_text(SKILL + " ", encoding="utf-8")
        result = _confirm(repo)
        assert result.exit_code == 1
        assert "skill hash mismatch" in result.output
        assert f"{SKILL_NAME}-v2.yaml" in result.output

    def test_an_edited_analysis_script_reaches_its_lock(self, repo: Path) -> None:
        (repo / "scripts" / "run_triggers.py").write_text(ANALYSIS + "# tweak\n", encoding="utf-8")
        result = _confirm(repo)
        assert result.exit_code == 1
        assert "analysis script hash mismatch" in result.output

    def test_a_baseline_outside_the_band_reaches_the_difficulty_check(self, repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "confirm",
                str(repo / "preregistration" / f"{SKILL_NAME}-v1.yaml"),
                "--baseline-accuracy",
                "0.95",
                "--projected-cost",
                "7.42",
            ],
        )
        assert result.exit_code == 1
        assert "difficulty band" in result.output

    def test_a_run_over_budget_reaches_the_budget_check(self, repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "confirm",
                str(repo / "preregistration" / f"{SKILL_NAME}-v1.yaml"),
                "--baseline-accuracy",
                "0.55",
                "--projected-cost",
                "7.44",
            ],
        )
        assert result.exit_code == 1
        assert "optional-stopping" in result.output

    def test_an_alternative_analysis_script_is_hashed_instead(self, repo: Path) -> None:
        """``--analysis`` names the locked code, so a wrong one has to fail."""
        (repo / "scripts" / "other.py").write_text("print(1)\n", encoding="utf-8")
        result = _confirm(repo, "--analysis", "scripts/other.py")
        assert result.exit_code == 1
        assert "analysis script hash mismatch" in result.output

    def test_an_absolute_analysis_path_is_taken_as_given(self, repo: Path) -> None:
        result = _confirm(repo, "--analysis", str(repo / "scripts" / "run_triggers.py"))
        assert result.exit_code == 1
        assert "both hash locks match" in result.output


class TestTheCommandRefusesBeforeTheLocks:
    def test_an_unreadable_preregistration_is_reported(self, repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "confirm",
                str(repo / "preregistration" / "absent.yaml"),
                "--baseline-accuracy",
                "0.55",
                "--projected-cost",
                "1.0",
            ],
        )
        assert result.exit_code == 1

    def test_a_missing_skill_body_names_the_file(self, repo: Path) -> None:
        (repo / "skills" / SKILL_NAME / "SKILL.md").unlink()
        result = _confirm(repo)
        assert result.exit_code == 1
        assert "is locked by this pre-registration and is not on disk" in result.output

    def test_a_missing_analysis_script_names_the_file(self, repo: Path) -> None:
        (repo / "scripts" / "run_triggers.py").unlink()
        result = _confirm(repo)
        assert result.exit_code == 1
        assert "is locked by this pre-registration and is not on disk" in result.output

    def test_a_preregistration_outside_the_repository_is_refused(
        self, repo: Path, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """No commit of it can be shown to predate anything in this history."""
        outside = tmp_path_factory.mktemp("elsewhere").resolve() / "loose.yaml"
        outside.write_text(yaml.safe_dump(_prereg_dict()), encoding="utf-8")
        result = runner.invoke(
            app,
            [
                "confirm",
                str(outside),
                "--baseline-accuracy",
                "0.55",
                "--projected-cost",
                "7.42",
            ],
        )
        assert result.exit_code == 1
        assert "outside this repository" in result.output


# ===========================================================================
# The commit facts the caller gathers
# ===========================================================================


class TestTheGatheredRepoState:
    def test_outside_a_git_repository_every_fact_is_false(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A pre-registration's value is its timestamp, and a tarball has none."""
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(cli, "_git_output", lambda args: None)
        state = cli._gather_repo_state("preregistration/x-v1.yaml", SKILL_NAME)
        assert not state.committed_and_clean
        assert not state.is_ancestor_of_head
        assert not state.precedes_results

    def test_an_untracked_preregistration_is_not_committed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        def git(args: list[str]) -> str | None:
            return None if args[0] == "ls-files" else ""

        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(cli, "_git_output", git)
        assert not cli._gather_repo_state(
            "preregistration/x-v1.yaml", SKILL_NAME
        ).committed_and_clean

    def test_a_dirty_preregistration_is_not_clean(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        def git(args: list[str]) -> str | None:
            return " M preregistration/x-v1.yaml" if args[0] == "status" else "deadbee"

        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(cli, "_git_output", git)
        assert not cli._gather_repo_state(
            "preregistration/x-v1.yaml", SKILL_NAME
        ).committed_and_clean

    def test_a_failed_git_status_reads_as_dirty(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An answer git could not give is not an answer that the file is clean."""

        def git(args: list[str]) -> str | None:
            return None if args[0] == "status" else "deadbee"

        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(cli, "_git_output", git)
        state = cli._gather_repo_state("preregistration/x-v1.yaml", SKILL_NAME)
        assert not state.committed_and_clean

    def test_a_preregistration_with_no_commit_is_not_on_this_history(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Ancestry is forced true, so only the empty sha can fail this."""

        def git(args: list[str]) -> str | None:
            return "" if args[0] in {"status", "log"} else "deadbee"

        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(cli, "_git_output", git)
        monkeypatch.setattr(cli, "_is_ancestor", lambda ancestor, descendant: True)
        state = cli._gather_repo_state("preregistration/x-v1.yaml", SKILL_NAME)
        assert not state.is_ancestor_of_head

    def test_the_registering_commit_is_the_earliest_that_added_the_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """``git log`` prints newest first, so the *last* line is the registration.

        Reading the first line would date a pre-registration by the last time its
        path was re-added, which is later, and later is weaker in the one
        direction this check exists to be strong in.
        """
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(
            cli,
            "_git_output",
            lambda args: "1111111\n2222222\n3333333" if args[0] == "log" else "",
        )
        assert cli._first_commit_adding("preregistration/x-v1.yaml") == "3333333"

    def test_a_confirmation_run_the_preregistration_postdates_is_refused(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        run = tmp_path / "results" / SKILL_NAME / "2026-08-30-abc1234"
        run.mkdir(parents=True)
        (run / "README.md").write_text(
            f"# A run\n\n{PREREGISTRATION_MARKER} `preregistration/{SKILL_NAME}-v1.yaml`\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(cli, "_git_output", _clean_repo)
        monkeypatch.setattr(cli, "_is_ancestor", lambda ancestor, descendant: False)
        assert not cli._gather_repo_state("preregistration/x-v1.yaml", SKILL_NAME).precedes_results

    def test_a_run_whose_first_commit_is_unknown_does_not_veto(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An unattributable run is a git failure, and a git failure is not evidence."""
        run = tmp_path / "results" / SKILL_NAME / "2026-08-30-abc1234"
        run.mkdir(parents=True)
        (run / "README.md").write_text(f"{PREREGISTRATION_MARKER} `x`\n", encoding="utf-8")

        def git(args: list[str]) -> str | None:
            if args[0] == "log" and args[-1].startswith("results/"):
                return ""
            return "" if args[0] == "status" else "deadbee"

        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(cli, "_git_output", git)
        monkeypatch.setattr(cli, "_is_ancestor", lambda ancestor, descendant: False)
        assert cli._gather_repo_state("preregistration/x-v1.yaml", SKILL_NAME).precedes_results


class TestWhichRunsCount:
    def test_a_skill_with_no_results_has_no_confirmation_runs(self, tmp_path: Path) -> None:
        assert confirmation_runs(tmp_path, SKILL_NAME) == []

    def test_a_screening_run_is_not_a_confirmation_run(self, tmp_path: Path) -> None:
        """The whole reason this is scoped rather than counting every run.

        Screening precedes a pre-registration by design: it runs the public
        split and decides whether to spend on a confirmation. Counting it would
        refuse every skill this repository has ever measured.
        """
        run = tmp_path / "results" / SKILL_NAME / "2026-08-12-40b6ba5"
        run.mkdir(parents=True)
        (run / "README.md").write_text(
            "# A screening run\n\n**Answer key:** v2\n", encoding="utf-8"
        )
        assert confirmation_runs(tmp_path, SKILL_NAME) == []

    def test_a_run_declaring_its_preregistration_counts(self, tmp_path: Path) -> None:
        run = tmp_path / "results" / SKILL_NAME / "2026-09-01-abc1234"
        run.mkdir(parents=True)
        (run / "README.md").write_text(f"{PREREGISTRATION_MARKER} `x`\n", encoding="utf-8")
        assert confirmation_runs(tmp_path, SKILL_NAME) == [
            f"results/{SKILL_NAME}/2026-09-01-abc1234"
        ]

    def test_a_run_directory_with_no_readme_is_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "results" / SKILL_NAME / "2026-09-01-abc1234").mkdir(parents=True)
        assert confirmation_runs(tmp_path, SKILL_NAME) == []

    def test_the_published_screening_runs_are_all_screening_runs(self) -> None:
        """No monkeypatching. Against the real record, so the scoping is checked."""
        assert confirmation_runs(cli.REPO_ROOT, SKILL_NAME) == []


# ===========================================================================
# The screening front
# ===========================================================================


class TestScreen:
    def test_every_argument_reaches_the_runner_untouched(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: dict[str, Any] = {}

        def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
            seen["command"] = command
            seen["kwargs"] = kwargs
            return subprocess.CompletedProcess(command, 0)

        monkeypatch.setattr(cli.subprocess, "run", fake_run)
        result = runner.invoke(app, ["screen", "--model", "haiku", "--band", "s"])
        assert result.exit_code == 0
        assert seen["command"][-4:] == ["--model", "haiku", "--band", "s"]
        assert seen["command"][1].endswith("run_triggers.py")
        # The runner resolves its own paths against the repository root, and a
        # non-zero exit has to come back as a value rather than an exception.
        assert seen["kwargs"] == {"cwd": cli.REPO_ROOT, "check": False}

    def test_the_runners_exit_code_becomes_the_commands_exit_code(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A wrapper that swallowed a failure would report a broken run as a run."""
        monkeypatch.setattr(
            cli.subprocess, "run", lambda command, **kwargs: subprocess.CompletedProcess(command, 3)
        )
        assert runner.invoke(app, ["screen"]).exit_code == 3

    def test_a_missing_runner_is_reported(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = runner.invoke(app, ["screen"])
        assert result.exit_code == 1
        assert "is missing" in result.output


# ===========================================================================
# The pre-registration this repository ships
# ===========================================================================


def _current_preregistration() -> Path:
    """The highest-numbered pre-registration on disk.

    Resolved rather than named, because a superseded version stays where it is.
    `_assert_hash`'s remedy for a lock that no longer matches is a new file, so
    the directory accumulates, and a test naming one version would have to be
    edited by whoever bumps it. A test that has to be edited to stay green is a
    test that gets edited to stay green.
    """
    versions = sorted(
        (int(path.stem.rsplit("-v", 1)[1]), path)
        for path in (cli.REPO_ROOT / "preregistration").glob("decision-making-v*.yaml")
    )
    return versions[-1][1]


class TestTheShippedPreregistration:
    """No monkeypatching anywhere below: the real file against the real model."""

    def test_it_validates_against_the_model(self) -> None:
        prereg = cli.load_preregistration(_current_preregistration())
        assert prereg.skill == "decision-making"

    def test_a_superseded_version_is_left_where_it_is(self) -> None:
        """Version 1 pinned a runner that moved three times on 2026-08-24.

        It stays on disk with the hash it was written with, because a
        pre-registration that can be edited in place is not one. It no longer
        matches, and that is the record rather than a defect.
        """
        superseded = cli.REPO_ROOT / "preregistration" / "decision-making-v1.yaml"
        if not superseded.is_file():
            pytest.skip("nothing has been superseded yet")
        prereg = cli.load_preregistration(superseded)
        source = (cli.REPO_ROOT / cli.TRIGGER_RUNNER).read_text(encoding="utf-8")
        assert prereg.analysis_script_sha256 != sha256_text(source)

    def test_the_skill_lock_hashes_the_skill_it_names(self) -> None:
        prereg = cli.load_preregistration(_current_preregistration())
        body = (cli.REPO_ROOT / "skills" / prereg.skill / "SKILL.md").read_text(encoding="utf-8")
        assert prereg.skill_sha256 == sha256_text(body)

    def test_the_command_reaches_the_locks_against_the_real_repository(self) -> None:
        """The whole claim, end to end, with nothing monkeypatched.

        Every other command test runs against a fixture tree with ancestry
        forced true. This one shells out to the real git, hashes the real skill
        and the real runner, and asserts the refusal this pathway exists to
        produce. If the pre-registration is ever left uncommitted or edited
        after commit, this goes red, which is the point.
        """
        result = runner.invoke(
            app,
            [
                "confirm",
                str(_current_preregistration()),
                "--baseline-accuracy",
                "0.55",
                "--projected-cost",
                "7.42",
            ],
        )
        assert result.exit_code == 1
        assert "both hash locks match" in result.output
        assert "there is none on disk" in result.output

    def test_the_analysis_lock_hashes_the_runner(self) -> None:
        prereg = cli.load_preregistration(_current_preregistration())
        source = (cli.REPO_ROOT / cli.TRIGGER_RUNNER).read_text(encoding="utf-8")
        assert prereg.analysis_script_sha256 == sha256_text(source)


# ===========================================================================
# The register's scope
# ===========================================================================


def test_the_arena_registry_is_a_governed_path() -> None:
    """`MODELS` decides which runs may become evidence, and that is a decision.

    Moving one row from `screen` to `confirm` promotes a whole venue's results.
    Nothing in a checkpoint, a label, or a diff of the answer key shows it.
    """
    assert "evals/src/decision_evals/arenas.py" in GOVERNED


def test_the_arena_registry_is_scoped_to_the_file() -> None:
    """The rest of the harness computes numbers; this file decides which count."""
    assert "evals/src/" not in GOVERNED
    assert "evals/" not in GOVERNED
