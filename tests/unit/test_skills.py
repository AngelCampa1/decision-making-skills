"""Tests for skill validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from decision_evals.generators.loader import REPO_ROOT
from decision_evals.skills import (
    STANDARD_FIELDS,
    UNSHIPPABLE_VERDICTS,
    VERDICTS,
    SkillIssue,
    check_mirrors,
    delivered_body,
    load_placebos,
    mirror_plan,
    orphaned_promotions,
    parse_skill,
    placebo_marker,
    promotable,
    sync_mirrors,
    validate_all,
    validate_skill,
    verdict_of,
)
from decision_evals.solvers.arms import check_placebo_match

BODY = "\n# Title\n\n## Abort if\nSkip when small.\n\n## Step\n" + ("word " * 60)
PLACEBO = "# Title\n\n## A\nGeneric.\n\n## B\n" + ("word " * 60)


def _frontmatter(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "name": "demo-skill",
        "description": "Use when deciding from a pile of context. Do not use for short prompts.",
        "license": "Apache-2.0",
        "compatibility": ">=1.0",
        "metadata": {
            "version": "0.1.0",
            "status": "experimental",
            "verdict": "UNTESTED",
            "claims": [{"id": "c1", "text": "Something falsifiable."}],
        },
        "allowed-tools": [],
    }
    base.update(overrides)
    return base


#: What the fixtures declare. `_write` puts the placebo at `placebo.md` and the
#: treatment at `SKILL.md`, so the map that covers them is one line each.
DEMO_PLACEBOS: dict[str, str] = {
    "demo-skill/placebo.md": "SKILL.md",
    "good-one/placebo.md": "SKILL.md",
}

#: The frontmatter `_write` puts on a placebo that does not bring its own.
MARKER = "---\nmatched_to: SKILL.md\n---\n"


def _write(
    root: Path,
    *,
    name: str = "demo-skill",
    front: dict[str, Any] | None = None,
    body: str = BODY,
    placebo: str | None = PLACEBO,
    raw: str | None = None,
) -> Path:
    directory = root / name
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "SKILL.md"
    if raw is not None:
        path.write_text(raw, encoding="utf-8")
    else:
        matter = yaml.safe_dump(front if front is not None else _frontmatter(), sort_keys=False)
        path.write_text(f"---\n{matter}---{body}", encoding="utf-8")
    if placebo is not None:
        # Every placebo declares what it controls for. Supplied text that already
        # carries frontmatter is left alone, so a test can write a wrong marker.
        marked = placebo if placebo.startswith("---") else MARKER + placebo
        (directory / "placebo.md").write_text(marked, encoding="utf-8")
    return path


def validate_skill_(path: Path, *, shipped: bool = False) -> list[SkillIssue]:
    """`validate_skill` with the map the fixtures are written to."""
    return validate_skill(path, placebos=DEMO_PLACEBOS, shipped=shipped)


# -- the shipped skill ------------------------------------------------------


def test_the_shipped_skill_validates() -> None:
    """The real artifact, not a fixture. If this fails, the skill is broken."""
    path = REPO_ROOT / "skills" / "decision-making" / "SKILL.md"
    assert validate_skill(path, placebos=load_placebos(REPO_ROOT)) == []


def test_the_shipped_skill_uses_only_portable_fields() -> None:
    """A skill that errors in six tools is Claude-Code-shaped, not portable."""
    document = parse_skill(REPO_ROOT / "skills" / "decision-making" / "SKILL.md")
    assert set(document.frontmatter) <= STANDARD_FIELDS


def test_a_generated_baseline_validates(tmp_path: Path) -> None:
    """Guards the rest: each test below asserts a *deviation* is caught."""
    assert validate_skill_(_write(tmp_path)) == []


# -- parsing ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "match"),
    [
        ("no frontmatter here", "missing YAML frontmatter"),
        ("---\nname: x\nstill going", "unterminated"),
        ("---\nname: [unclosed\n---\nbody", "unparseable"),
        ("---\n- a\n- b\n---\nbody", "not a mapping"),
    ],
)
def test_malformed_documents_report_rather_than_raise(tmp_path: Path, raw: str, match: str) -> None:
    """One broken skill must not hide the others' problems."""
    issues = validate_skill_(_write(tmp_path, raw=raw))
    assert len(issues) == 1
    assert match in issues[0].message


# -- frontmatter ------------------------------------------------------------


def test_a_vendor_extension_is_rejected(tmp_path: Path) -> None:
    """`context: fork` is a hard error in Codex, Cursor and the rest."""
    front = _frontmatter()
    front["context"] = "fork"
    issues = validate_skill_(_write(tmp_path, front=front))
    assert any("non-standard frontmatter" in str(i) for i in issues)


def test_a_missing_required_field_is_reported(tmp_path: Path) -> None:
    front = _frontmatter()
    del front["description"]
    issues = validate_skill_(_write(tmp_path, front=front))
    assert any("missing required frontmatter" in str(i) for i in issues)


def test_the_name_must_match_the_directory(tmp_path: Path) -> None:
    """Discovery uses the directory, so a mismatch means the name is decoration."""
    issues = validate_skill_(_write(tmp_path, front=_frontmatter(name="something-else")))
    assert any("does not match directory" in str(i) for i in issues)


# -- description ------------------------------------------------------------


@pytest.mark.parametrize("description", ["", "   ", None])
def test_an_empty_description_is_rejected(tmp_path: Path, description: Any) -> None:
    """It is the only text always resident in context."""
    issues = validate_skill_(_write(tmp_path, front=_frontmatter(description=description)))
    assert any("description is empty" in str(i) for i in issues)


def test_a_description_without_a_negative_clause_is_rejected(tmp_path: Path) -> None:
    """Availability dominates; a description saying only when to fire fires on everything."""
    front = _frontmatter(description="Use whenever you are making any kind of decision.")
    issues = validate_skill_(_write(tmp_path, front=front))
    assert any("no negative clause" in str(i) for i in issues)


@pytest.mark.parametrize(
    "description",
    [
        "Use for X. Do not use for Y.",
        "Use for X. Don't use for Y.",
        "Use for X. Not for Y.",
        "Use for X. Skip when Y.",
        "Use for X. Avoid when Y.",
    ],
)
def test_recognised_negative_phrasings(tmp_path: Path, description: str) -> None:
    assert validate_skill_(_write(tmp_path, front=_frontmatter(description=description))) == []


# -- metadata and evidence --------------------------------------------------


def test_metadata_must_be_a_mapping(tmp_path: Path) -> None:
    issues = validate_skill_(_write(tmp_path, front=_frontmatter(metadata="none")))
    assert any("must be a mapping" in str(i) for i in issues)


def test_an_unrecognised_verdict_is_rejected(tmp_path: Path) -> None:
    """A typo in a verdict is a false claim."""
    front = _frontmatter(
        metadata={"verdict": "PROBABLY_FINE", "claims": [{"id": "c", "text": "t"}]}
    )
    issues = validate_skill_(_write(tmp_path, front=front))
    assert any("is not one of" in str(i) for i in issues)


def test_an_untested_skill_may_be_developed_but_not_shipped(tmp_path: Path) -> None:
    """The distinction the rule turns on."""
    path = _write(tmp_path)
    assert validate_skill_(path, shipped=False) == []
    issues = validate_skill_(path, shipped=True)
    assert any("may not ship" in str(i) for i in issues)


@pytest.mark.parametrize("verdict", sorted(VERDICTS - UNSHIPPABLE_VERDICTS))
def test_a_skill_with_a_verdict_may_ship(tmp_path: Path, verdict: str) -> None:
    front = _frontmatter(metadata={"verdict": verdict, "claims": [{"id": "c1", "text": "t"}]})
    assert validate_skill_(_write(tmp_path, front=front), shipped=True) == []


def test_a_withdrawn_skill_may_be_developed_but_not_shipped(tmp_path: Path) -> None:
    """The retirement rule, enforced rather than merely written in SCORECARD.md.

    WITHDRAWN is the negative outcome of the maintainer's daily use. If it did
    not block the plugin it would be a label, and an evidence channel that only
    ever comes out positive is not an evidence channel.
    """
    front = _frontmatter(metadata={"verdict": "WITHDRAWN", "claims": [{"id": "c1", "text": "t"}]})
    path = _write(tmp_path, front=front)
    assert validate_skill_(path, shipped=False) == []
    assert any(
        "WITHDRAWN skill may not ship" in str(i) for i in validate_skill_(path, shipped=True)
    )


@pytest.mark.parametrize("claims", [None, [], "not a list"])
def test_claims_must_be_declared(tmp_path: Path, claims: Any) -> None:
    front = _frontmatter(metadata={"verdict": "UNTESTED", "claims": claims})
    issues = validate_skill_(_write(tmp_path, front=front))
    assert any("metadata.claims" in str(i) for i in issues)


@pytest.mark.parametrize("claim", [{"id": "c1"}, {"text": "t"}, "a string"])
def test_a_malformed_claim_is_reported(tmp_path: Path, claim: Any) -> None:
    front = _frontmatter(metadata={"verdict": "UNTESTED", "claims": [claim]})
    issues = validate_skill_(_write(tmp_path, front=front))
    assert any("malformed claim" in str(i) for i in issues)


def test_duplicate_claim_ids_are_reported(tmp_path: Path) -> None:
    front = _frontmatter(
        metadata={
            "verdict": "UNTESTED",
            "claims": [{"id": "c1", "text": "a"}, {"id": "c1", "text": "b"}],
        }
    )
    issues = validate_skill_(_write(tmp_path, front=front))
    assert any("duplicate claim ids" in str(i) for i in issues)


# -- placebo ----------------------------------------------------------------


def test_a_missing_placebo_is_rejected(tmp_path: Path) -> None:
    """Writing it after seeing results is the degree of freedom the arm removes."""
    issues = validate_skill(_write(tmp_path, placebo=None), placebos={})
    assert any("no placebo" in str(i) for i in issues)


def test_an_unmatched_placebo_is_rejected(tmp_path: Path) -> None:
    issues = validate_skill_(_write(tmp_path, placebo="# Tiny\n\n## A\nShort."))
    assert any("not matched to SKILL.md" in str(i) for i in issues)


def test_a_placebo_is_measured_against_the_body_its_arm_delivers(tmp_path: Path) -> None:
    """The hole this check was opened to close.

    A placebo may stand in for a procedure rather than for `SKILL.md`, and
    pointing it at the wrong body was invisible while the pairing came from the
    filename, because the filename only ever named one pair.
    """
    path = _write(tmp_path, placebo=PLACEBO)
    (path.parent / "procedure.md").write_text("# P\n\n## A\ntwo words\n", encoding="utf-8")

    assert validate_skill(path, placebos={"demo-skill/placebo.md": "SKILL.md"}) == []

    issues = validate_skill(path, placebos={"demo-skill/placebo.md": "procedure.md"})
    assert any("not matched to procedure.md" in str(i) for i in issues)


def test_an_undeclared_placebo_file_is_refused(tmp_path: Path) -> None:
    """A placebo nothing declares is a placebo nothing measures."""
    path = _write(tmp_path, placebo=PLACEBO)
    (path.parent / "placebo-procedure.md").write_text(PLACEBO, encoding="utf-8")
    assert any("placebo-procedure.md is on disk" in str(i) for i in validate_skill_(path))


def test_a_declared_placebo_with_no_file_is_refused(tmp_path: Path) -> None:
    issues = validate_skill(
        _write(tmp_path, placebo=PLACEBO),
        placebos=DEMO_PLACEBOS | {"demo-skill/placebo-gone.md": "SKILL.md"},
    )
    assert any("placebo-gone.md is declared" in str(i) for i in issues)


def test_a_placebo_declared_against_an_absent_body_is_refused(tmp_path: Path) -> None:
    issues = validate_skill(
        _write(tmp_path, placebo=PLACEBO), placebos={"demo-skill/placebo.md": "gone.md"}
    )
    assert any("which is not on disk" in str(i) for i in issues)


def test_the_shipped_council_placebo_matches_council() -> None:
    """The real pair, not a fixture."""
    directory = REPO_ROOT / "skills" / "decision-making"
    match = check_placebo_match(
        delivered_body(directory / "council.md"),
        delivered_body(directory / "placebo-council.md"),
    )
    assert match.ok, match


def test_delivered_body_strips_frontmatter() -> None:
    """Counting YAML as skill prose has produced one wrong ratio on record."""
    directory = REPO_ROOT / "skills" / "decision-making"
    assert "matched_to" not in delivered_body(directory / "placebo-council.md")
    assert delivered_body(directory / "council.md").startswith("# Council")


#: Layout deixis: language that points at where something sits in the prompt
#: rather than at what it says. No scanner for this shipped in the harness, so
#: the pattern list is here, beside the one assertion that needs it.
#:
#: `council.md` keeps its `A.` / `B.` labels. A placebo that shared them would
#: stop being a size control and become a weaker copy of the treatment, and the
#: arm would then answer "does the procedure beat itself" instead of "does the
#: procedure beat instruction bulk".
POSITIONAL_PATTERNS: dict[str, str] = {
    "option letter label": r"(?m)^\s*[A-Z][.)]\s",
    "inline letter label": r"\b(?:option|position|case|choice)\s+[A-Z]\b",
    "ordinal": r"\b(?:first|second|third|fourth|last|former|latter)\b",
    "layout direction": r"\b(?:above|below|top|bottom|earlier|later)\b",
    "list deixis": r"\b(?:the list|listed|in order|the order)\b",
    "counted positions": r"\b(?:both|either|neither|each of them|two of them)\b",
    "sequence marker": r"\b(?:step \d|then|next|finally|begin by)\b",
}


def scan_positional_language(body: str) -> list[tuple[str, str]]:
    """Every layout-deixis hit in a body, as (what it is, what matched)."""
    return [
        (label, match.group(0))
        for label, pattern in POSITIONAL_PATTERNS.items()
        for match in re.finditer(pattern, body, flags=re.IGNORECASE)
    ]


def test_the_council_placebo_carries_no_positional_language() -> None:
    """A placebo that names positions is a partial treatment wearing a control's clothes."""
    body = delivered_body(REPO_ROOT / "skills" / "decision-making" / "placebo-council.md")
    assert scan_positional_language(body) == []


def test_the_scan_finds_positional_language_where_there_is_some() -> None:
    """A scan that cannot hit is a scan that has not run."""
    assert scan_positional_language("A. sell it\nB. keep it\nThe first is above.")


def test_a_placebo_marker_that_disagrees_with_the_register_is_refused(
    tmp_path: Path,
) -> None:
    """The site reads the marker and the guard reads the register."""
    path = _write(tmp_path, placebo="---\nmatched_to: other.md\n---\n" + PLACEBO)
    issues = validate_skill_(path)
    assert any("declares `matched_to: other.md`" in str(i) for i in issues)


def test_every_shipped_placebo_declares_what_it_controls_for() -> None:
    directory = REPO_ROOT / "skills" / "decision-making"
    declared = load_placebos(REPO_ROOT)
    assert declared, "the register is empty, so the guard has nothing to check"
    for key, treatment in declared.items():
        assert placebo_marker(REPO_ROOT / "skills" / key) == treatment
    assert {path.name for path in directory.glob("placebo*.md")} == {
        key.split("/", 1)[1] for key in declared
    }


# -- batch ------------------------------------------------------------------


def test_validate_all_covers_every_skill(tmp_path: Path) -> None:
    _write(tmp_path, name="good-one", front=_frontmatter(name="good-one"))
    _write(tmp_path, name="bad-one", front=_frontmatter(name="mismatch"), placebo=None)
    issues = validate_all(tmp_path, placebos=DEMO_PLACEBOS)
    assert {i.skill for i in issues} == {"mismatch"}
    assert len(issues) == 2


def test_validate_all_on_an_empty_root(tmp_path: Path) -> None:
    assert validate_all(tmp_path, placebos=DEMO_PLACEBOS) == []


# -- mirrors ----------------------------------------------------------------


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "AGENTS.md").write_text("# Agents\nwiring block\n", encoding="utf-8")
    _write(tmp_path / "skills", name="demo-skill")
    return tmp_path


def test_the_real_repository_mirrors_are_current() -> None:
    """A stale `.agents/skills/` silently serves an old skill to every non-Claude tool."""
    assert check_mirrors(REPO_ROOT) == []


def test_mirror_plan_pairs_agents_with_claude(tmp_path: Path) -> None:
    pairs = mirror_plan(_repo(tmp_path))
    assert (tmp_path / "AGENTS.md", tmp_path / "CLAUDE.md") in pairs


def test_mirror_plan_skips_an_absent_agents_file(tmp_path: Path) -> None:
    _write(tmp_path / "skills", name="demo-skill")
    assert all(source.name != "AGENTS.md" for source, _ in mirror_plan(tmp_path))


def test_mirror_plan_covers_every_skill_file(tmp_path: Path) -> None:
    """Not just SKILL.md: the placebo has to reach the mirror too."""
    mirrors = {mirror.name for _, mirror in mirror_plan(_repo(tmp_path))}
    assert {"SKILL.md", "placebo.md", "CLAUDE.md"} <= mirrors


def test_mirror_plan_on_a_bare_directory(tmp_path: Path) -> None:
    assert mirror_plan(tmp_path) == []


def test_sync_writes_then_becomes_a_no_op(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    first = sync_mirrors(repo)
    assert first
    assert sync_mirrors(repo) == []
    assert (repo / "CLAUDE.md").read_text(encoding="utf-8") == (repo / "AGENTS.md").read_text(
        encoding="utf-8"
    )


def test_a_missing_mirror_is_reported(tmp_path: Path) -> None:
    issues = check_mirrors(_repo(tmp_path))
    assert issues
    assert all("is missing" in str(i) for i in issues)


def test_a_stale_mirror_is_reported(tmp_path: Path) -> None:
    """Worse than a missing one: it serves old content without erroring."""
    repo = _repo(tmp_path)
    sync_mirrors(repo)
    (repo / "AGENTS.md").write_text("# Agents\nrevised wiring\n", encoding="utf-8")
    issues = check_mirrors(repo)
    assert any("CLAUDE.md is stale" in str(i) for i in issues)


def test_sync_repairs_a_stale_mirror(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    sync_mirrors(repo)
    (repo / "CLAUDE.md").write_text("tampered", encoding="utf-8")
    assert sync_mirrors(repo) == [repo / "CLAUDE.md"]
    assert check_mirrors(repo) == []


# -- promotion --------------------------------------------------------------


def _promote(repo: Path, verdict: str, *, name: str = "demo-skill") -> Path:
    """Rewrite a source skill's verdict, as a confirmation run would."""
    front = _frontmatter(
        name=name,
        metadata={"verdict": verdict, "claims": [{"id": "c1", "text": "t"}]},
    )
    _write(repo / "skills", name=name, front=front)
    return repo


def test_an_untested_skill_is_not_promotable(tmp_path: Path) -> None:
    """The gate. Nothing reaches the plugin on good intentions."""
    assert promotable(_repo(tmp_path) / "skills") == []


@pytest.mark.parametrize("verdict", sorted(VERDICTS - UNSHIPPABLE_VERDICTS))
def test_any_recorded_verdict_makes_a_skill_promotable(tmp_path: Path, verdict: str) -> None:
    """Including HARMFUL: shipping it off-by-default with its evidence is the point."""
    repo = _promote(_repo(tmp_path), verdict)
    assert [path.name for path in promotable(repo / "skills")] == ["demo-skill"]


def test_a_skill_with_unreadable_metadata_is_not_promotable(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write(repo / "skills", name="demo-skill", front=_frontmatter(metadata="none"))
    assert promotable(repo / "skills") == []


def test_verdict_of_a_directory_without_a_skill_file(tmp_path: Path) -> None:
    assert verdict_of(tmp_path / "absent") is None


def test_promotable_on_a_missing_skills_root(tmp_path: Path) -> None:
    assert promotable(tmp_path / "nothing") == []


def test_an_untested_skill_never_reaches_the_plugin(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    sync_mirrors(repo)
    assert not (repo / "plugin" / "skills" / "demo-skill").exists()
    assert check_mirrors(repo) == []


def test_promotion_copies_the_whole_skill_directory(tmp_path: Path) -> None:
    """Everything travels, not just SKILL.md.

    The placebo, because evidence includes what the skill was tested against;
    and nested `references/` or `scripts/`, because a skill that loses them on
    promotion ships broken to every installer while validating locally.
    """
    repo = _promote(_repo(tmp_path), "SHIP")
    nested = repo / "skills" / "demo-skill" / "references"
    nested.mkdir()
    (nested / "worked-example.md").write_text("example", encoding="utf-8")

    sync_mirrors(repo)
    promoted = repo / "plugin" / "skills" / "demo-skill"
    assert (promoted / "SKILL.md").exists()
    assert (promoted / "placebo.md").exists()
    assert (promoted / "references" / "worked-example.md").read_text(encoding="utf-8") == "example"
    assert check_mirrors(repo) == []


def test_a_promoted_skill_that_is_demoted_is_reported(tmp_path: Path) -> None:
    """The failure the evidence rule exists to prevent, and the one mirror_plan misses.

    A demoted skill contributes no source/mirror pairs at all, so a staleness
    check sees nothing wrong while the plugin keeps shipping a withdrawn badge.
    """
    repo = _promote(_repo(tmp_path), "SHIP")
    sync_mirrors(repo)
    _promote(repo, "UNTESTED")
    issues = check_mirrors(repo)
    assert any("promoted but its source now records UNTESTED" in str(i) for i in issues)


def test_sync_withdraws_a_demoted_skill(tmp_path: Path) -> None:
    repo = _promote(_repo(tmp_path), "SHIP")
    sync_mirrors(repo)
    _promote(repo, "UNTESTED")
    assert repo / "plugin" / "skills" / "demo-skill" in sync_mirrors(repo)
    assert not (repo / "plugin" / "skills" / "demo-skill").exists()
    assert check_mirrors(repo) == []


def test_a_plugin_skill_with_no_source_at_all_is_reported(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "plugin" / "skills" / "ghost").mkdir(parents=True)
    assert any("no source skill" in str(i) for i in check_mirrors(repo))


def test_a_file_beside_the_promotions_is_not_an_orphan(tmp_path: Path) -> None:
    """`plugin/skills/README.md` explains the empty directory; it is not a skill."""
    repo = _repo(tmp_path)
    plugin_skills = repo / "plugin" / "skills"
    plugin_skills.mkdir(parents=True)
    (plugin_skills / "README.md").write_text("why this is empty", encoding="utf-8")
    assert orphaned_promotions(repo) == []


def test_orphan_detection_without_a_plugin_directory(tmp_path: Path) -> None:
    assert orphaned_promotions(tmp_path) == []


# -- the real repository ----------------------------------------------------


def test_the_shipped_plugin_promotes_nothing_yet() -> None:
    """Guards the README badge. `proven: 0` has to mean the directory is empty."""
    assert promotable(REPO_ROOT / "skills") == []
    assert orphaned_promotions(REPO_ROOT) == []
