"""Every number the paper reports, written from the records rather than typed.

``paper/main.tex`` states the rule it is built on: if a number appears in the
prose and not in ``generated/macros.tex``, it is a bug. This module is what
makes that rule satisfiable. It reads a published run directory and emits three
artefacts under ``paper/``:

``generated/macros.tex``
    One ``\\newcommand`` per reported figure, so the prose cites a macro and a
    stale number becomes an undefined control sequence rather than a sentence
    that quietly disagrees with the data.
``generated/tables.tex``
    The booktabs tables, built from the same values as the macros.
``figures/*.tex``
    pgfplots pictures. Text, so a diff can review them, and no plotting
    dependency: the alternative was matplotlib, which this project does not
    install and would not gain anything else from.

**This is a renderer and never a second analysis.** Accuracies, p-values and
adjusted q-values are read out of ``analysis.json``, which is the record. The
one thing computed here is the signal decomposition, because it postdates the
run and no file on disk carries it; it goes through
:mod:`decision_evals.stats.signal` and :mod:`decision_evals.stats.cluster`, the
same functions the notebook entry used, so the paper and the notebook cannot
drift.

Both output directories are gitignored. Committing them would let the PDF drift
from the data, which is the failure the arrangement exists to prevent.
"""

from __future__ import annotations

import json
import re
import string
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from decision_evals.scorers.answer import (
    last_answer_line,
    normalise_answer,
    strip_control_token,
)
from decision_evals.skills import delivered_body
from decision_evals.solvers.arms import check_placebo_match
from decision_evals.stats.cluster import (
    SignFlipResult,
    cluster_bootstrap_diff,
    cluster_sign_flip,
)
from decision_evals.stats.multiplicity import holm
from decision_evals.stats.paired import mcnemar_exact
from decision_evals.stats.power import minimum_detectable_effect
from decision_evals.stats.signal import DegenerateSignalError, informedness, skew

#: Where published runs of the five-arm study live.
STUDY_ROOT: Final = "results/evolution-study"

#: The two bodies whose match the paper reports. Both are read through
#: ``delivered_body``, which strips the frontmatter an arm does not deliver, so
#: the count here is the count the gate in ``skills.py`` enforces.
SEED_SKILL: Final = "skills/decision-making/SKILL.md"
PLACEBO_SKILL: Final = "skills/decision-making/placebo.md"

#: The arm the decomposition is differenced against. Not the arm the study's own
#: comparisons use, and deliberately so: ``placebo`` answers "does this beat a
#: document-shaped control", ``off`` answers "does any document help at all",
#: and which arm a published comparison used is read out of ``analysis.json``
#: rather than assumed here.
BASELINE_ARM: Final = "off"

#: Resampling draws for the cluster bootstrap, matching the notebook entry of
#: 2026-08-28. It does not reproduce that entry's intervals exactly: the paper
#: publishes skillopt at [-0.068, +0.259] against the notebook's
#: [-0.069, +0.260], and gepa and on differ in the third decimal too. Same
#: estimator, same draws, a different resampling order, and an interval quoted
#: to three decimals is not stable at that resolution. The paper's figures are
#: the generated ones; the notebook is the dated record of what was seen first.
BOOTSTRAP_DRAWS: Final = 20_000

#: Seed for those draws. A published interval that moves between builds is not
#: a published interval.
BOOTSTRAP_SEED: Final = 20260828

#: Templates below this informedness in every arm are reported as carrying no
#: discriminative signal. Chosen on 2026-08-28 by reading the ten measured
#: values, which fall into a group of seven above 0.4 and a group of three below
#: 0.3 with nothing between; it is a description of that gap and not a
#: threshold anything was tested against.
LOW_SIGNAL_J: Final = 0.3

_LETTERS: Final = frozenset(string.ascii_letters)


class FigureError(RuntimeError):
    """A figure could not be built from the records.

    Raised rather than warned. A renderer that skips what it cannot read emits
    a macro file missing exactly the numbers nobody checked, and the LaTeX build
    then fails somewhere unrelated with no indication of why.
    """


@dataclass(frozen=True, slots=True)
class Reading:
    """One model answer, reduced to the fields a figure reads."""

    arm: str
    item_id: str
    template_id: str
    seed: int
    expected: str
    parsed: str | None
    input_tokens: int
    output_tokens: int
    #: What the scorer would have read with a trailing control token stripped
    #: (:func:`decision_evals.scorers.answer.strip_control_token`). Equal to
    #: ``parsed`` when the answer parsed; the text in front of the token when
    #: the answer was refused for carrying one; ``None`` otherwise. Feeds
    #: :func:`rescored_macros` and nothing registered.
    rescored: str | None = None

    @property
    def item(self) -> tuple[int, str]:
        """What makes an item one item.

        ``item_id`` does not encode the seed, so three seeds of one template
        share an id and collapse under it. A per-item count keyed on the id
        alone reported a twentieth of this study on 2026-08-28 before the
        mistake was caught by the number being implausible rather than by
        anything checking.
        """
        return (self.seed, self.item_id)


@dataclass(frozen=True, slots=True)
class ArmSignal:
    """One arm's discrimination and bias, averaged over templates.

    Attributes:
        arm: The arm's label.
        parse_rate: Share of readings that produced a parsable answer. Reported
            because everything else here is computed over the parsed subset, so
            an arm that parses less is measured on the part it managed.
        mean_informedness: Per-template Youden's J, averaged over templates.
        mean_skew: Per-template absolute skew, averaged over templates.
        per_template: Each template's J, keyed by template id.
    """

    arm: str
    parse_rate: float
    mean_informedness: float
    mean_skew: float
    per_template: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class Delta:
    """A difference in informedness against the baseline arm, with its interval."""

    arm: str
    estimate: float
    ci_low: float
    ci_high: float


@dataclass(frozen=True, slots=True)
class Study:
    """One published run, read once.

    Everything downstream is a rendering of this. Building it in each renderer
    instead would run the cluster bootstrap several times per build, and two
    computations of one published interval are two chances to publish different
    numbers for it.

    Attributes:
        run: The run directory's name.
        analysis: ``analysis.json`` verbatim. The record for every accuracy,
            p-value and adjusted q-value the paper reports.
        manifest: ``run.json`` verbatim.
        readings: Every arm's records, the A/A pass excluded.
        signals: Per-arm discrimination and bias.
        deltas: Each arm's informedness against ``off``, with its interval.
    """

    run: str
    analysis: Mapping[str, Any]
    manifest: Mapping[str, Any]
    readings: Sequence[Reading]
    signals: Mapping[str, ArmSignal]
    deltas: Sequence[Delta]


@dataclass(frozen=True, slots=True)
class FiguresResult:
    """What a build wrote, for the caller to report."""

    run: str | None
    macros: int
    paths: tuple[Path, ...]


def latest_run(repo_root: Path) -> Path | None:
    """The most recent published study directory, or ``None`` if there is none.

    Directory names begin with an ISO date, so the plain sort is chronological.
    A bare checkout with no results is not an error, so the caller decides what
    to do about it rather than being handed an exception.
    """
    root = repo_root / STUDY_ROOT
    if not root.is_dir():
        return None
    runs = sorted(path for path in root.iterdir() if (path / "analysis.json").is_file())
    return runs[-1] if runs else None


def load_readings(run_dir: Path) -> list[Reading]:
    """Every arm's records, flattened into the fields the decomposition needs.

    **The arm is the file name, not the record's ``arm`` field.** That field
    holds the arm's *kind*, and both evolved winners are of kind ``candidate``,
    so reading it merges GEPA and SkillOpt into one arm whose numbers are a
    blend of two. The blend is plausible-looking, which is what makes it worth
    a comment: it reported a mean J of 0.582 for an arm that does not exist.

    The A/A pass is excluded. It is the placebo scored a second time, so folding
    it in would weight one arm double for no gain.
    """
    readings: list[Reading] = []
    for path in sorted(run_dir.glob("records-*.jsonl")):
        if path.name == "records-aa.jsonl":
            continue
        arm = path.stem.removeprefix("records-")
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            parsed = row["parsed"] if row["parse_status"] == "parsed" else None
            readings.append(
                Reading(
                    arm=arm,
                    item_id=row["item_id"],
                    template_id=row["template_id"],
                    seed=int(row["seed"]),
                    expected=row["expected"],
                    parsed=parsed,
                    input_tokens=int(row["input_tokens"]),
                    output_tokens=int(row["output_tokens"]),
                    rescored=_rescore(parsed, row.get("response", "")),
                )
            )
    if not readings:
        raise FigureError(f"no arm records under {run_dir}")
    return readings


def _rescore(parsed: str | None, response: str) -> str | None:
    """The answer with a trailing control token stripped, or what the scorer read.

    Only an answer the scorer refused is re-read, and only when the refusal was a
    control token on the answer line. Everything else keeps the verdict on file.
    """
    if parsed is not None:
        return parsed
    line = last_answer_line(response)
    if line is None:
        return None
    text, carried = strip_control_token(line)
    return text if carried else None


def body_tokens(readings: Sequence[Reading], arms: Sequence[str]) -> dict[str, int]:
    """How many prompt tokens each arm's document actually cost, by arm.

    ``off`` carries the task framing and the format contract and no document, so
    its input length is the shared prefix and every other arm's document is the
    difference. The subtraction is exact rather than approximate: the same items
    run in every arm, so per item the delta against ``off`` has zero variance,
    and this refuses if that is ever untrue.

    The word-count match in ``placebo_macros`` is a property of two files on
    disk. This is a property of what the model was sent, and the two disagree:
    the placebo is matched to the seed skill and to nothing else, while the
    evolved winners are whatever length the engines chose.

    Raises:
        FigureError: No ``off`` arm, or an arm whose per-item delta is not
            constant, which would mean the prefix is not shared.
    """
    if BASELINE_ARM not in arms:
        raise FigureError(f"no {BASELINE_ARM!r} arm to difference against")
    by_arm: dict[str, dict[tuple[int, str], int]] = defaultdict(dict)
    for reading in readings:
        by_arm[reading.arm][reading.item] = reading.input_tokens
    baseline = by_arm[BASELINE_ARM]
    sizes: dict[str, int] = {}
    for arm in arms:
        shared = baseline.keys() & by_arm[arm].keys()
        if not shared:
            raise FigureError(f"{arm!r} and {BASELINE_ARM!r} share no item")
        deltas = {by_arm[arm][item] - baseline[item] for item in shared}
        if len(deltas) != 1:
            raise FigureError(
                f"{arm!r} differs from {BASELINE_ARM!r} by {len(deltas)} distinct "
                "amounts, so the prompt prefix is not shared across items"
            )
        sizes[arm] = deltas.pop()
    return sizes


def clustered_tests(
    readings: Sequence[Reading], manifest: Mapping[str, Any], control: str
) -> dict[tuple[str, str], SignFlipResult]:
    """The registered comparisons re-run with the template as the unit.

    The registration named an item-matched test and this study reports it. Items
    minted from one template share a scenario, a rule and a distractor pool, so
    that test is answering at a unit the design does not have. This sums to one
    net difference per template and exchanges those signs instead.

    Keyed by ``(set label, arm)``, control arm excluded because it is the thing
    every arm is differenced against.

    Raises:
        FigureError: The manifest declares no item sets, or an arm is missing an
            item another arm has.
    """
    sets = manifest.get("request", {}).get("sets")
    if not sets:
        raise FigureError("manifest declares no item sets to cluster within")
    by_arm: dict[str, dict[tuple[int, str], Reading]] = defaultdict(dict)
    for reading in readings:
        by_arm[reading.arm][reading.item] = reading
    results: dict[tuple[str, str], SignFlipResult] = {}
    for item_set in sets:
        seeds = set(item_set["seeds"])
        items = sorted(item for item in by_arm[control] if item[0] in seeds)
        for arm in by_arm:
            if arm == control:
                continue
            missing = [item for item in items if item not in by_arm[arm]]
            if missing:
                raise FigureError(f"{arm!r} is missing {len(missing)} item(s) {control!r} has")
            differences = [
                _is_correct(by_arm[arm][item]) - _is_correct(by_arm[control][item])
                for item in items
            ]
            clusters = [by_arm[control][item].template_id for item in items]
            results[(item_set["label"], arm)] = cluster_sign_flip(
                differences, clusters, alternative="greater"
            )
    return results


#: Discordance the pre-registration measured before the run, on 84 held-out
#: items at validation seed 1000. The MDE is a function of it, so it is the
#: study's own input and not a value chosen here.
REGISTERED_DISCORDANCE: Final = 0.250

#: The design effect PROTOCOL.md assumes for a template-built corpus. The
#: pre-registration computed its MDE at 1.0, which is the no-clustering case and
#: not the one the protocol specifies; both are reported.
PROTOCOL_DESIGN_EFFECT: Final = 2.0


def power_macros(analysis: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, str]:
    """The smallest effect this design could have seen, at each item count.

    A null is only worth reading beside the effect the study was powered for.
    This one registered an MDE before the first call and the paper did not carry
    it, which leaves a reader unable to tell a small effect from no effect.

    Reported at the pre-registration's own design effect of 1.0 and again at
    PROTOCOL.md's 2.0, because the registration used the first where the
    standing protocol specifies the second.
    """
    family = max(len(item_set["comparisons"]) for item_set in analysis["sets"])
    alpha = float(manifest["request"]["alpha"]) / family
    values: dict[str, str] = {
        _macro_name("study", "alpha"): _fixed(float(manifest["request"]["alpha"]), 2),
        _macro_name("family", "size"): str(family),
        _macro_name("mde", "alpha"): _fixed(alpha, 4),
        _macro_name("mde", "discordance"): _fixed(REGISTERED_DISCORDANCE, 3),
        _macro_name("protocol", "designEffect"): f"{PROTOCOL_DESIGN_EFFECT:.1f}",
    }
    clustered: list[float] = []
    for item_set in analysis["sets"]:
        label = item_set["label"]
        for name, effect in (("mde", 1.0), ("mdeClustered", PROTOCOL_DESIGN_EFFECT)):
            try:
                result = minimum_detectable_effect(
                    int(item_set["n_items"]),
                    REGISTERED_DISCORDANCE,
                    alpha=alpha,
                    design_effect=effect,
                )
            except ValueError:
                # A set too small to detect any effect at this alpha has no MDE
                # to report. Omitting the macro leaves any prose citing it as an
                # undefined control sequence, which is the failure this module
                # is built to produce rather than a wrong number.
                continue
            values[_macro_name(name, label)] = _fixed(result.effect, 4)
            if effect != 1.0:
                clustered.append(result.effect)

    # How far the clustered bar sits above the biggest gain the study saw. The
    # largest *gain* rather than the largest absolute movement, because the
    # question a power calculation answers is whether an improvement of that
    # size was detectable, and a decrement of the same size is a different
    # claim. Both are in the tables; only this one is the bar's counterpart.
    gains = [
        comparison["accuracy"] - comparison["control_accuracy"]
        for item_set in analysis["sets"]
        for comparison in item_set["comparisons"]
    ]
    best = max(gains)
    if best > 0 and clustered:
        values[_macro_name("mde", "ratio")] = f"{min(clustered) / best:.1f}"
    return values


def per_template_macros(
    readings: Sequence[Reading], manifest: Mapping[str, Any], baseline: str, control: str
) -> dict[str, str]:
    """Accuracy and parse rate per template, and each arm with one dropped.

    An aggregate over three templates can be carried entirely by one of them,
    which is what happened to this study's most quoted sentence. These are the
    numbers that show it: per template, and per arm with each template removed
    in turn.

    ``\\accWithout<Set><Template><Arm>`` is an arm's accuracy over the set with
    that template dropped. ``\\constantShare<Set><Template><Arm>`` is how often
    the arm gave its most frequent answer, which reads 1.000 for a constant
    responder.
    """
    sets = manifest.get("request", {}).get("sets") or []
    by_arm: dict[str, list[Reading]] = defaultdict(list)
    for reading in readings:
        by_arm[reading.arm].append(reading)
    values: dict[str, str] = {}
    for item_set in sets:
        label, seeds = item_set["label"], set(item_set["seeds"])
        templates = sorted({r.template_id for r in readings if r.seed in seeds})
        for arm, rows in by_arm.items():
            scoped = [r for r in rows if r.seed in seeds]
            for template in templates:
                key = _template_key(template)
                here = [r for r in scoped if r.template_id == template]
                rest = [r for r in scoped if r.template_id != template]
                values[_macro_name("acc", label, key, arm)] = _fixed(_accuracy(here), 4)
                values[_macro_name("accWithout", label, key, arm)] = _fixed(_accuracy(rest), 4)
                values[_macro_name("parseRate", label, key, arm)] = _fixed(_parse_rate(here), 3)
                # Accuracy over the parsed subset, and its distance from the
                # reported figure. On a balanced key the two coincide unless the
                # unreadable answers land unevenly across it, so this difference
                # is a direct measure of how selective an arm's parse failure is.
                read = [r for r in here if r.parsed is not None]
                if read:
                    parsed_acc = _accuracy(read)
                    values[_macro_name("accParsed", label, key, arm)] = _fixed(parsed_acc, 4)
                    values[_macro_name("gapParsed", label, key, arm)] = _signed(
                        parsed_acc - _accuracy(here), 4
                    )
                answers = [r.parsed for r in here if r.parsed is not None]
                if answers:
                    top = max(set(answers), key=answers.count)
                    share = answers.count(top) / len(answers)
                    values[_macro_name("constantShare", label, key, arm)] = _fixed(share, 3)
                    values[_macro_name("parsedCount", label, key, arm)] = str(len(answers))
                for answer, (failed, total) in key_selectivity(
                    readings, seeds, template, arm
                ).items():
                    slug = _template_key(answer.replace("_", "-"))
                    values[_macro_name("failOn", label, key, arm, slug)] = str(failed)
                    values[_macro_name("countOn", label, key, arm, slug)] = str(total)
        for template in templates:
            key = _template_key(template)
            # Net items against the *control*, which is what every reported
            # effect is measured against. An aggregate effect is a signed sum
            # over templates and not a partition of them, so this is what shows
            # which template carried one and which pulled the other way.
            for arm in by_arm:
                if arm == control:
                    continue
                here = [r for r in by_arm[arm] if r.seed in seeds]
                there = [r for r in by_arm[control] if r.seed in seeds]
                paired = {r.item: r for r in there}
                net = sum(
                    _is_correct(r) - _is_correct(paired[r.item])
                    for r in here
                    if r.item in paired and r.template_id == template
                )
                values[_macro_name("net", label, key, arm)] = _signed(net, 0)
            # Named for its numerator, not its trailing token. The sibling
            # family above puts the arm last, so a shared `gap` prefix with the
            # *baseline* last read as the same shape meaning the opposite
            # thing. An arm the study did not run leaves the pair out rather
            # than dividing by zero.
            gepa = [r for r in by_arm["gepa"] if r.seed in seeds and r.template_id == template]
            floor = [r for r in by_arm[baseline] if r.seed in seeds and r.template_id == template]
            if gepa and floor:
                values[_macro_name("gepaLess", label, key, baseline)] = _signed(
                    _accuracy(gepa) - _accuracy(floor), 4
                )
    return values


def restricted_macros(
    readings: Sequence[Reading], manifest: Mapping[str, Any], control: str
) -> dict[str, str]:
    """The registered comparisons re-run on items both arms could read.

    Accuracy scores an unreadable answer wrong, so it sums decision quality and
    format compliance, and the arms differ on the second by more than any effect
    here. This holds format constant by keeping only the pairs where the arm and
    the control both parsed.

    It is not the corrected analysis and must not be reported as one: parse
    failure is selective on the answer key (:func:`key_selectivity`), so the
    restriction conditions on a post-treatment variable that correlates with the
    outcome. Both readings are biased and this design cannot say which is nearer.
    """
    by_arm: dict[str, dict[tuple[int, str], Reading]] = defaultdict(dict)
    for reading in readings:
        by_arm[reading.arm][reading.item] = reading
    values: dict[str, str] = {}
    for item_set in manifest.get("request", {}).get("sets") or []:
        label, seeds = item_set["label"], set(item_set["seeds"])
        for arm in by_arm:
            if arm == control:
                continue
            pairs = [
                (by_arm[control][item], by_arm[arm][item])
                for item in sorted(by_arm[control])
                if item[0] in seeds
                and item in by_arm[arm]
                and by_arm[control][item].parsed is not None
                and by_arm[arm][item].parsed is not None
            ]
            if not pairs:
                continue
            result = mcnemar_exact(
                [_is_correct(c) for c, _ in pairs], [_is_correct(t) for _, t in pairs]
            )
            values[_macro_name("restricted", label, arm)] = _signed(result.proportion_difference, 4)
            values[_macro_name("restrictedP", label, arm)] = _fixed(result.p_value, 4)
            values[_macro_name("restrictedWins", label, arm)] = str(result.treatment_wins)
            values[_macro_name("restrictedLosses", label, arm)] = str(result.control_wins)
            values[_macro_name("restrictedPairs", label, arm)] = str(result.n_pairs)
    return values


def _is_correct_rescored(reading: Reading) -> int:
    """One when the re-read answer names the key, zero otherwise."""
    return int(
        reading.rescored is not None
        and normalise_answer(reading.rescored) == normalise_answer(reading.expected)
    )


def rescored_macros(
    readings: Sequence[Reading], manifest: Mapping[str, Any], analysis: Mapping[str, Any]
) -> dict[str, str]:
    """The study re-read with a trailing control token stripped, beside the record.

    Qwen3 treats ``/think`` as a thinking-mode switch and, in this study, echoed
    it onto the answer line: ``ANSWER: monitor /think``. The scorer read that as
    an option not on the menu and scored it wrong. It happened 87 times in 3,640
    calls, the key agreed with the word in front of the token on 84 of them, and
    it landed unevenly: 56 on GEPA's winner, 29 on the empty prompt, one each on
    two other arms. In the study's own vocabulary that is a ``verifier_defect``
    (:mod:`decision_evals.scorers.answer`), and because it is uneven it moves
    comparisons rather than every arm together.

    The registered figures stay as registered. This family reports what the same
    records read with the token stripped: accuracy per arm, the registered
    comparisons with Holm over the same family, the template-level test, and the
    control against the baseline, a comparison the registration left outside the
    family and the first draft of the paper read as a finding. It is named
    ``rescored`` and not ``corrected`` for the reason :func:`restricted_macros`
    gives: a re-read chosen after the data are in cannot be the headline.

    ``\\controlToken<Arm>`` counts the arm's refused answers that carried the
    token, ``\\controlTokenCorrect<Arm>`` how many of those named the key, and
    ``\\controlTokenOn<Set><Template><Arm>`` where they landed.
    ``\\controlOverBaseline<Set>`` and ``\\controlOverBaselineNet<Set><Template>``
    give the control against the baseline as registered, so the paper can show
    which template carried it; ``\\rescored...`` prefixes each with the re-read.
    """
    control = str(analysis["control"])
    alpha = float(manifest.get("request", {}).get("alpha", 0.05))
    by_arm: dict[str, dict[tuple[int, str], Reading]] = defaultdict(dict)
    for reading in readings:
        by_arm[reading.arm][reading.item] = reading
    values: dict[str, str] = {}

    carried_total = named_total = 0
    for arm, rows in by_arm.items():
        carried = [r for r in rows.values() if r.parsed is None and r.rescored is not None]
        named = sum(_is_correct_rescored(r) for r in carried)
        carried_total += len(carried)
        named_total += named
        values[_macro_name("controlToken", arm)] = str(len(carried))
        values[_macro_name("controlTokenCorrect", arm)] = str(named)
    values[_macro_name("controlToken", "total")] = str(carried_total)
    values[_macro_name("controlTokenCorrect", "total")] = str(named_total)

    seeds_of = {s["label"]: set(s["seeds"]) for s in manifest.get("request", {}).get("sets") or []}
    for item_set in analysis["sets"]:
        label = item_set["label"]
        seeds = seeds_of.get(label, set())
        items = sorted(item for item in by_arm[control] if item[0] in seeds)
        if not items:
            continue
        templates = sorted({by_arm[control][item].template_id for item in items})

        for arm, rows in by_arm.items():
            scoped = [rows[item] for item in items if item in rows]
            if not scoped:
                continue
            accuracy = sum(_is_correct_rescored(r) for r in scoped) / len(scoped)
            values[_macro_name("rescoredAcc", label, arm)] = _fixed(accuracy, 4)
            for template in templates:
                here = [r for r in scoped if r.template_id == template]
                values[_macro_name("controlTokenOn", label, _template_key(template), arm)] = str(
                    sum(1 for r in here if r.parsed is None and r.rescored is not None)
                )

        family = [c["arm"] for c in item_set["comparisons"] if c["arm"] in by_arm]
        raw: list[float] = []
        for arm in family:
            pairs = [(by_arm[control][item], by_arm[arm][item]) for item in items]
            result = mcnemar_exact(
                [_is_correct_rescored(c) for c, _ in pairs],
                [_is_correct_rescored(t) for _, t in pairs],
            )
            raw.append(result.p_value)
            values[_macro_name("rescoredEffect", label, arm)] = _signed(
                result.proportion_difference, 4
            )
            values[_macro_name("rescoredWins", label, arm)] = str(result.treatment_wins)
            values[_macro_name("rescoredLosses", label, arm)] = str(result.control_wins)
            values[_macro_name("rescoredP", label, arm)] = _fixed(result.p_value, 4)
            flip = cluster_sign_flip(
                [_is_correct_rescored(t) - _is_correct_rescored(c) for c, t in pairs],
                [c.template_id for c, _ in pairs],
                alternative="greater",
            )
            values[_macro_name("rescoredClustered", label, arm)] = _fixed(flip.p_value, 4)
            values[_macro_name("rescoredClusters", label, arm)] = str(flip.n_clusters)
        if raw:
            for arm, adjusted in zip(family, holm(raw, alpha=alpha).adjusted, strict=True):
                values[_macro_name("rescoredQ", label, arm)] = _fixed(adjusted, 4)

        # The control against the baseline, which the registration left outside
        # the family. Reported as registered and re-read, per template, because
        # the first draft of the paper read the registered version as a finding
        # and it was one template's refused answers.
        if BASELINE_ARM in by_arm:
            pairs = [(by_arm[BASELINE_ARM][item], by_arm[control][item]) for item in items]
            for prefix, score in (
                ("controlOverBaseline", _is_correct),
                ("rescoredControlOverBaseline", _is_correct_rescored),
            ):
                result = mcnemar_exact([score(b) for b, _ in pairs], [score(c) for _, c in pairs])
                values[_macro_name(prefix, "wins", label)] = str(result.treatment_wins)
                values[_macro_name(prefix, "losses", label)] = str(result.control_wins)
                values[_macro_name(prefix, "p", label)] = _fixed(result.p_value, 4)
                flip = cluster_sign_flip(
                    [score(c) - score(b) for b, c in pairs],
                    [b.template_id for b, _ in pairs],
                    alternative="greater",
                )
                values[_macro_name(prefix, "clustered", label)] = _fixed(flip.p_value, 4)
                values[_macro_name(prefix, "clusters", label)] = str(flip.n_clusters)
                for template in templates:
                    net = sum(score(c) - score(b) for b, c in pairs if b.template_id == template)
                    values[_macro_name(prefix, "net", label, _template_key(template))] = _signed(
                        net, 0
                    )
    return values


def key_selectivity(
    readings: Sequence[Reading], set_seeds: set[int], template_id: str, arm: str
) -> dict[str, tuple[int, int]]:
    """How an arm's parse failures split across the answers on one template.

    Keyed by the expected answer, valued ``(failed, total)``. A failure rate
    that differs sharply between the two answers is the finding: the arm is not
    dropping items at random, it is dropping the ones whose correct answer it
    will not give, and dropping those is not neutral to any comparison.

    Reported per answer rather than as majority and minority, because these keys
    are balanced by construction and ranking two equal counts would name the
    halves by an accident of sort order.
    """
    rows = [
        r for r in readings if r.arm == arm and r.seed in set_seeds and r.template_id == template_id
    ]
    return {
        label: (
            sum(r.expected == label and r.parsed is None for r in rows),
            sum(r.expected == label for r in rows),
        )
        for label in sorted({r.expected for r in rows})
    }


def at_cap_macros(readings: Sequence[Reading], arms: Sequence[str]) -> dict[str, str]:
    """Per arm, how many generations ran to the output cap without concluding.

    The cap is read off the records as the largest ``output_tokens`` any arm
    reached. The manifest carries ``max_tokens`` and would do, but a cap read
    from the records is a cap some generation actually hit, and a hard-coded
    4096 would silently report zero the day either one changes. A generation
    that stops exactly at the ceiling did not choose to stop.

    This exists because the paper twice claimed runaway generations were a seed
    skill pathology that both evolved winners fixed. In this run the placebo
    produces the most of them, so whatever is happening is a property of putting
    a document in the prompt and not of what the document says.
    """
    if not readings:
        raise FigureError("no readings to count generations over")
    cap = max(r.output_tokens for r in readings)
    values = {_macro_name("outputCap"): str(cap)}
    for arm in arms:
        rows = [r for r in readings if r.arm == arm]
        if not rows:
            continue
        at_cap = sum(r.output_tokens >= cap for r in rows)
        values[_macro_name("atCap", arm)] = str(at_cap)
        values[_macro_name("unparsed", arm)] = str(sum(r.parsed is None for r in rows))
    return values


def screen_macros(run_dir: Path) -> dict[str, str]:
    """The ceiling screen's own numbers, read off the artefact beside the run.

    ``nvbuild-ceiling-screen.json`` is committed, so the figures the ceiling
    section quotes from it are generatable and were typed. The count matters as
    much as the accuracies: the section called this an eleven-model screen, the
    file holds fewer, and eleven is how many models this key can reach under a
    registered ``nvbuild/`` prefix. The harness registers prefixes, not models.
    Absent file is not an error, because the generator has to exit cleanly on a
    checkout with no results. The paper does not build from one: these six are
    among the macros ``ceiling.tex`` would leave undefined.
    """
    path = run_dir / "nvbuild-ceiling-screen.json"
    if not path.is_file():
        return {}
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not rows:
        raise FigureError(f"{path} holds no screened models")
    accuracies = sorted(float(row["accuracy"]) for row in rows)
    asked = {int(row["asked"]) for row in rows}
    return {
        _macro_name("screen", "models"): str(len(rows)),
        _macro_name("screen", "worst"): _fixed(accuracies[0], 3),
        _macro_name("screen", "best"): _fixed(accuracies[-1], 3),
        _macro_name("screen", "atCeiling"): str(sum(a >= 0.999 for a in accuracies)),
        _macro_name("screen", "items"): str(asked.pop()) if len(asked) == 1 else "varied",
        # Accuracy in this artefact is correct over *answered*, not over asked,
        # and one row answered fewer than it was asked. Reporting the gap keeps
        # a perfect score on a short denominator from reading as a perfect score.
        _macro_name("screen", "unanswered"): str(
            sum(int(row["asked"]) - int(row["answered"]) for row in rows)
        ),
    }


def template_range_macros(repo_root: Path) -> dict[str, str]:
    """The integer ranges the corpus draws its thresholds from.

    ``sec:whatengines`` argues that a constant a winner transcribed cannot have
    come from a given template because that template's variable is drawn
    elsewhere. That argument is only as good as the bounds it quotes, and the
    bounds are in committed YAML, so they are read rather than typed.

    Parsed with a regex instead of a YAML loader on purpose: this needs two
    integers from a line whose shape the golden-file tests already pin, and
    adding a parser dependency to the paper's build to read them would be the
    larger change.
    """
    root = repo_root / "datasets" / "templates"
    if not root.is_dir():
        return {}
    values: dict[str, str] = {}
    pattern = re.compile(r"^\s*(\w+):\s*\{int:\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]\s*\}")
    for path in sorted(root.glob("*.yaml")):
        key = _template_key(path.stem)
        for line in path.read_text(encoding="utf-8").splitlines():
            match = pattern.match(line)
            if match is None:
                continue
            name, low, high = match.groups()
            slug = name[:1].upper() + name[1:]
            values[_macro_name("range", key, slug, "low")] = low
            values[_macro_name("range", key, slug, "high")] = high
    return values


def _template_key(template_id: str) -> str:
    """A template id as a macro-name fragment: letters only, digits spelled out.

    ``rel-001-vendor-outage`` becomes ``relZeroZeroOneVendorOutage``. LaTeX
    control sequences take no digits or hyphens, and mangling silently would
    collide ``rel-001`` with ``rel-010``.
    """
    digits = {
        "0": "Zero",
        "1": "One",
        "2": "Two",
        "3": "Three",
        "4": "Four",
        "5": "Five",
        "6": "Six",
        "7": "Seven",
        "8": "Eight",
        "9": "Nine",
    }
    head, *tail = template_id.split("-")
    parts = [head] + [part[:1].upper() + part[1:] for part in tail]
    return "".join("".join(digits.get(ch, ch) for ch in part) for part in parts)


def _accuracy(readings: Sequence[Reading]) -> float:
    """Share answered correctly, unparsed counted wrong, as the study scores it."""
    return sum(_is_correct(r) for r in readings) / len(readings) if readings else 0.0


def _parse_rate(readings: Sequence[Reading]) -> float:
    """Share that produced a readable answer."""
    return sum(r.parsed is not None for r in readings) / len(readings) if readings else 0.0


def _is_correct(reading: Reading) -> int:
    """One when the arm answered this item correctly, zero otherwise.

    An unparsed answer is zero, which is the study's own convention: the scorer
    credits nothing it could not read.
    """
    return int(reading.parsed is not None and reading.parsed == reading.expected)


def arm_order(manifest: Mapping[str, Any]) -> list[str]:
    """The arms in the order the study registered them.

    Reading them off the records instead sorts them alphabetically, which puts
    the two evolved winners on either side of the controls and makes every table
    harder to read than the run's own README.
    """
    return [arm["label"] for arm in manifest["arms"]]


def signal_by_arm(readings: Sequence[Reading], order: Sequence[str]) -> dict[str, ArmSignal]:
    """Per-arm discrimination and bias, computed per template then averaged.

    Averaging over templates rather than pooling items is the whole design:
    templates here mint either 56 or 112 items, so a pooled figure lets the
    larger ones decide the answer.

    A template whose *key* holds a single answer class has no informedness, and
    :func:`~decision_evals.stats.signal.informedness` refuses rather than
    returning zero. Such a template is dropped from that arm's mean and its
    skew is still counted, because skew stays defined where J does not.
    """
    grouped: dict[str, dict[str, list[Reading]]] = defaultdict(lambda: defaultdict(list))
    parsed_counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])

    for reading in readings:
        counts = parsed_counts[reading.arm]
        counts[1] += 1
        if reading.parsed is None:
            continue
        counts[0] += 1
        grouped[reading.arm][reading.template_id].append(reading)

    missing = [arm for arm in order if arm not in grouped]
    if missing:
        raise FigureError(f"the manifest names {missing} and no records file carries them")

    result: dict[str, ArmSignal] = {}
    for arm in order:
        per_template: dict[str, float] = {}
        skews: list[float] = []
        for template, rows in sorted(grouped[arm].items()):
            expected = [row.expected for row in rows]
            parsed = [row.parsed for row in rows]
            positive = sorted(set(expected))[0]
            skews.append(abs(skew(expected, parsed, option=positive)))
            try:
                per_template[template] = informedness(
                    expected, parsed, positive=positive
                ).informedness
            except DegenerateSignalError:
                continue
        if not per_template:
            raise FigureError(f"arm {arm!r} has no template with both answer classes")
        answered, asked = parsed_counts[arm]
        result[arm] = ArmSignal(
            arm=arm,
            parse_rate=answered / asked,
            mean_informedness=sum(per_template.values()) / len(per_template),
            mean_skew=sum(skews) / len(skews),
            per_template=per_template,
        )
    return result


def informedness_deltas(signals: Mapping[str, ArmSignal]) -> list[Delta]:
    """Each arm's informedness against ``off``, with a cluster-bootstrap interval.

    Templates are the cluster and each contributes one paired difference, so the
    resampling unit is the template exactly as it is in the study's own
    analysis. Ten clusters is few and the intervals are correspondingly wide;
    that is the width this design supports rather than a defect in the method.

    Only templates measured in both arms enter a comparison. A template one arm
    could not discriminate on is not a zero for that arm.
    """
    baseline = signals[BASELINE_ARM]
    deltas: list[Delta] = []
    for arm, signal in signals.items():
        if arm == BASELINE_ARM:
            continue
        shared = sorted(set(baseline.per_template) & set(signal.per_template))
        result = cluster_bootstrap_diff(
            [baseline.per_template[t] for t in shared],
            [signal.per_template[t] for t in shared],
            shared,
            n_resamples=BOOTSTRAP_DRAWS,
            seed=BOOTSTRAP_SEED,
        )
        deltas.append(
            Delta(
                arm=arm,
                estimate=result.point_estimate,
                ci_low=result.ci_low,
                ci_high=result.ci_high,
            )
        )
    return deltas


def low_signal_templates(signals: Mapping[str, ArmSignal]) -> list[str]:
    """Templates below :data:`LOW_SIGNAL_J` in every arm that measured them.

    A template that no arm can discriminate on is not contributing difficulty to
    the run. Its items contribute their base rate and whichever way the model
    happens to lean, which is what makes an item count an overstatement of how
    much signal a run carries.
    """
    everywhere = set.intersection(*(set(signal.per_template) for signal in signals.values()))
    return sorted(
        template
        for template in everywhere
        if all(signal.per_template[template] < LOW_SIGNAL_J for signal in signals.values())
    )


def read_study(run_dir: Path) -> Study:
    """Read one published run and compute the decomposition over it, once."""
    manifest = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    readings = load_readings(run_dir)
    signals = signal_by_arm(readings, arm_order(manifest))
    return Study(
        run=run_dir.name,
        analysis=json.loads((run_dir / "analysis.json").read_text(encoding="utf-8")),
        manifest=manifest,
        readings=readings,
        signals=signals,
        deltas=informedness_deltas(signals),
    )


def placebo_macros(repo_root: Path) -> dict[str, str]:
    """The placebo's match against the skill it stands in for.

    A property of the two bodies rather than of any run, and reported by the
    paper, so it is generated here for the same reason everything else is: a
    hand-typed pair of numbers will be wrong after the next edit to either file.

    Both sides go through ``delivered_body``, which is what ``skills.py`` hands
    the gate. Stripping frontmatter from the skill and not from the placebo read
    628 placebo words against 612 until 2026-08-31; the bodies a model receives
    are 557 and 612, and the paper published the inflated pair.

    Returns an empty mapping when either body is absent, so a checkout without
    the skill still builds.
    """
    skill = repo_root / SEED_SKILL
    placebo = repo_root / PLACEBO_SKILL
    if not (skill.is_file() and placebo.is_file()):
        return {}
    match = check_placebo_match(delivered_body(skill), delivered_body(placebo))
    return {
        _macro_name("skill", "words"): str(match.skill_words),
        _macro_name("placebo", "words"): str(match.placebo_words),
        _macro_name("skill", "sections"): str(match.skill_sections),
        _macro_name("placebo", "sections"): str(match.placebo_sections),
        _macro_name("placebo", "tolerance"): f"{match.tolerance * 100:.0f}",
    }


def _macro_name(*parts: str) -> str:
    """Join parts into a LaTeX control sequence name, letters only.

    ``\\newcommand`` accepts no digits or underscores in a name, and a name that
    breaks that rule fails the build with an error pointing at the definition
    rather than at the number. Refusing here names the offending part instead.
    """
    head, *tail = parts
    name = head + "".join(part[:1].upper() + part[1:] for part in tail)
    stripped = name.replace("-", "").replace("_", "")
    if not stripped or not set(stripped) <= _LETTERS:
        raise FigureError(f"{name!r} is not a usable macro name: LaTeX allows letters only")
    return stripped


def _fixed(value: float, places: int) -> str:
    """A number at a fixed width, which is the only rounding that happens here."""
    return f"{value:.{places}f}"


def _signed(value: float, places: int) -> str:
    """A difference, always carrying its sign, so a table column reads straight."""
    return f"{value:+.{places}f}"


def collect(study: Study, repo_root: Path) -> dict[str, str]:
    """Every macro the paper defines, as name to already-formatted value.

    Formatting to a fixed number of places is the only transformation applied to
    a published figure. Everything reported at four places matches the run's own
    README, so a reader comparing the paper against the results directory sees
    the same digits.
    """
    analysis, manifest = study.analysis, study.manifest
    readings, signals = study.readings, study.signals
    arms = arm_order(manifest)

    values: dict[str, str] = {
        _macro_name("study", "run"): study.run,
        _macro_name("study", "model"): manifest["request"]["target_model"],
        _macro_name("study", "control"): analysis["control"],
        _macro_name("study", "arms"): str(len(manifest["arms"])),
        _macro_name("study", "readings"): str(len(readings)),
        _macro_name("study", "templates"): str(len({reading.template_id for reading in readings})),
    }

    sizes = body_tokens(readings, arms)
    # The ratio is against whichever arm the run registered as its control, so a
    # run whose control is not among the arms gets sizes and no ratios rather
    # than a ratio against something that was not the comparison.
    control = sizes.get(str(analysis["control"]), 0)
    for arm, size in sizes.items():
        values[_macro_name("body", arm, "tokens")] = str(size)
        if size and control:
            values[_macro_name("body", arm, "ratio")] = f"{size / control:.2f}"

    for item_set in analysis["sets"]:
        label = item_set["label"]
        values[_macro_name(label, "items")] = str(item_set["n_items"])
        for arm, accuracy in item_set["accuracy"].items():
            values[_macro_name("acc", label, arm)] = _fixed(accuracy, 4)
        for comparison in item_set["comparisons"]:
            arm = comparison["arm"]
            effect = comparison["accuracy"] - comparison["control_accuracy"]
            values[_macro_name("effect", label, arm)] = _signed(effect, 4)
            values[_macro_name("wins", label, arm)] = str(comparison["arm_only"])
            values[_macro_name("losses", label, arm)] = str(comparison["control_only"])
            values[_macro_name("p", label, arm)] = _fixed(comparison["p_value"], 4)
            values[_macro_name("q", label, arm)] = _fixed(comparison["adjusted"], 4)

    for (label, arm), flip in clustered_tests(readings, manifest, analysis["control"]).items():
        values[_macro_name("clustered", label, arm)] = _fixed(flip.p_value, 4)
        values[_macro_name("clusters", label, arm)] = str(flip.n_clusters)
        # The realised floor, which is above the design floor whenever a
        # template nets zero and drops out of the test. That is the number a
        # comparison was actually up against, and it is not knowable until the
        # data are in, unlike the design floor beside it.
        values[_macro_name("clusteredFloor", label, arm)] = _fixed(flip.floor, 4)

    # The design floor is a property of how many templates the set has, not of
    # how many of them happened to move. A tied template can only raise the
    # attainable p, so this is the optimistic bound and it was knowable before
    # the first call.
    for item_set in manifest["request"]["sets"]:
        seeds = set(item_set["seeds"])
        templates = {r.template_id for r in readings if r.seed in seeds}
        values[_macro_name("templates", item_set["label"])] = str(len(templates))
        values[_macro_name("floor", item_set["label"])] = _fixed(2.0 ** -len(templates), 4)

    aa = analysis.get("aa")
    if aa is not None:
        values[_macro_name("aa", "pairs")] = str(aa["n_pairs"])
        values[_macro_name("aa", "disagreements")] = str(aa["arm_only"] + aa["control_only"])
        values[_macro_name("aa", "p")] = _fixed(aa["p_value"], 4)
        values[_macro_name("aa", "accuracy")] = _fixed(aa["accuracy"], 4)
        # Every call the run made. ``studyReadings`` counts the arms only,
        # because ``load_readings`` drops the A/A pass, and quoting it as the
        # run's size understates it by one arm.
        values[_macro_name("study", "calls")] = str(len(readings) + int(aa["n_pairs"]))

    for arm, signal in signals.items():
        values[_macro_name("parseRate", arm)] = _fixed(signal.parse_rate, 3)
        values[_macro_name("meanJ", arm)] = _fixed(signal.mean_informedness, 3)
        values[_macro_name("meanSkew", arm)] = _fixed(signal.mean_skew, 3)

    for delta in study.deltas:
        values[_macro_name("deltaJ", delta.arm)] = _signed(delta.estimate, 3)
        values[_macro_name("deltaJ", delta.arm, "low")] = _signed(delta.ci_low, 3)
        values[_macro_name("deltaJ", delta.arm, "high")] = _signed(delta.ci_high, 3)

    quiet = low_signal_templates(signals)
    # Counted over one arm, because every arm saw the same items and summing
    # across five would report the call count as an item count.
    items = {reading.item: reading.template_id for reading in readings if reading.arm == arms[0]}
    quiet_items = sum(template in quiet for template in items.values())
    total_items = len(items)

    if aa is not None:
        # Arms run in blocks and the A/A pass runs after all of them, so the two
        # passes of the control arm are separated by every arm that follows it.
        # The paper reports that distance because it is what the A/A actually
        # measured: a block design's exposure to drift, over that many calls.
        after = arms[arms.index(analysis["control"]) + 1 :]
        values[_macro_name("aa", "separation")] = str(len(after) * total_items)

    values[_macro_name("lowSignal", "threshold")] = _fixed(LOW_SIGNAL_J, 1)
    values[_macro_name("lowSignal", "templates")] = str(len(quiet))
    values[_macro_name("lowSignal", "items")] = str(quiet_items)
    values[_macro_name("signal", "items")] = str(total_items - quiet_items)
    values[_macro_name("total", "items")] = str(total_items)

    values.update(at_cap_macros(readings, arms))
    values.update(screen_macros(repo_root / STUDY_ROOT / study.run))
    values.update(template_range_macros(repo_root))
    values.update(power_macros(analysis, manifest))
    values.update(per_template_macros(readings, manifest, BASELINE_ARM, analysis["control"]))
    values.update(restricted_macros(readings, manifest, analysis["control"]))
    values.update(rescored_macros(readings, manifest, analysis))
    values.update(placebo_macros(repo_root))

    return values


def render_macros(values: Mapping[str, str]) -> str:
    """The macro file, one definition per line, sorted so a diff is readable."""
    lines = [
        "% Generated by `de figures`. Do not edit.",
        "% Every number the paper reports is defined here and nowhere else.",
        "",
    ]
    lines += [f"\\newcommand{{\\{name}}}{{{value}}}" for name, value in sorted(values.items())]
    return "\n".join(lines) + "\n"


def _accuracy_table(analysis: Mapping[str, Any]) -> list[str]:
    """One booktabs table per item set, arms ordered by accuracy."""
    lines: list[str] = []
    for item_set in analysis["sets"]:
        label = item_set["label"]
        comparisons = {c["arm"]: c for c in item_set["comparisons"]}
        order = sorted(item_set["accuracy"], key=lambda a: -item_set["accuracy"][a])
        lines += [
            f"\\newcommand{{\\{_macro_name(label, 'table')}}}{{%",
            "\\begin{tabular}{lrrrrr}",
            "\\toprule",
            "arm & accuracy & effect & wins/losses & $p$ & Holm $q$ \\\\",
            "\\midrule",
        ]
        for arm in order:
            accuracy = f"\\{_macro_name('acc', label, arm)}"
            if arm in comparisons:
                lines.append(
                    f"\\texttt{{{arm}}} & {accuracy} & \\{_macro_name('effect', label, arm)} & "
                    f"\\{_macro_name('wins', label, arm)} / "
                    f"\\{_macro_name('losses', label, arm)} & "
                    f"\\{_macro_name('p', label, arm)} & "
                    f"\\{_macro_name('q', label, arm)} \\\\"
                )
            else:
                lines.append(f"\\texttt{{{arm}}} & {accuracy} & --- & --- & --- & --- \\\\")
        lines += ["\\bottomrule", "\\end{tabular}}", ""]
    return lines


def _signal_table(signals: Mapping[str, ArmSignal], deltas: Sequence[Delta]) -> list[str]:
    """Discrimination beside accuracy, which is the decomposition's whole point."""
    by_arm = {delta.arm: delta for delta in deltas}
    lines = [
        f"\\newcommand{{\\{_macro_name('signal', 'table')}}}{{%",
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "arm & parse rate & mean $J$ & $\\Delta J$ vs \\texttt{off} & 95\\% CI \\\\",
        "\\midrule",
    ]
    for arm in signals:
        cells = [
            f"\\texttt{{{arm}}}",
            f"\\{_macro_name('parseRate', arm)}",
            f"\\{_macro_name('meanJ', arm)}",
        ]
        if arm in by_arm:
            cells += [
                f"\\{_macro_name('deltaJ', arm)}",
                f"[\\{_macro_name('deltaJ', arm, 'low')}, \\{_macro_name('deltaJ', arm, 'high')}]",
            ]
        else:
            cells += ["---", "---"]
        lines.append(" & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}}", ""]
    return lines


def _template_table(signals: Mapping[str, ArmSignal]) -> list[str]:
    """Per-template informedness, every arm, so the quiet templates are visible."""
    arms = list(signals)
    templates = sorted(set.union(*(set(s.per_template) for s in signals.values())))
    quiet = set(low_signal_templates(signals))
    lines = [
        f"\\newcommand{{\\{_macro_name('template', 'table')}}}{{%",
        "\\begin{tabular}{l" + "r" * len(arms) + "}",
        "\\toprule",
        "template & " + " & ".join(f"\\texttt{{{arm}}}" for arm in arms) + " \\\\",
        "\\midrule",
    ]
    for template in templates:
        marker = "$^{\\dagger}$" if template in quiet else ""
        cells = [
            _fixed(signals[arm].per_template[template], 3)
            if template in signals[arm].per_template
            else "---"
            for arm in arms
        ]
        lines.append(f"\\texttt{{{template}}}{marker} & " + " & ".join(cells) + " \\\\")
    lines += [
        "\\bottomrule",
        "\\end{tabular}}",
        "",
    ]
    return lines


def render_tables(study: Study) -> str:
    """Every table, as a macro apiece so the sections place them."""
    lines = ["% Generated by `de figures`. Do not edit.", ""]
    lines += _accuracy_table(study.analysis)
    lines += _signal_table(study.signals, study.deltas)
    lines += _template_table(study.signals)
    return "\n".join(lines) + "\n"


def render_accuracy_plot(study: Study) -> str:
    """Accuracy by arm on both item sets, in the order the study registered them."""
    analysis = study.analysis
    arms = arm_order(study.manifest)
    lines = [
        "% Generated by `de figures`. Do not edit.",
        "\\begin{tikzpicture}",
        "\\begin{axis}[",
        "  ybar, width=\\linewidth, height=6cm,",
        "  ymin=0.5, ymax=0.9, ylabel={accuracy},",
        "  symbolic x coords={" + ",".join(arms) + "},",
        "  xtick=data, enlarge x limits=0.15,",
        "  legend style={at={(0.5,-0.18)}, anchor=north, legend columns=-1},",
        "]",
    ]
    for item_set in analysis["sets"]:
        points = " ".join(f"({arm},{item_set['accuracy'][arm]:.4f})" for arm in arms)
        lines += [
            f"\\addplot coordinates {{{points}}};",
            f"\\addlegendentry{{{item_set['label']}}}",
        ]
    lines += ["\\end{axis}", "\\end{tikzpicture}", ""]
    return "\n".join(lines)


def render_signal_plot(study: Study) -> str:
    """Informedness against the empty prompt, with cluster-bootstrap intervals."""
    deltas = study.deltas
    lines = [
        "% Generated by `de figures`. Do not edit.",
        "\\begin{tikzpicture}",
        "\\begin{axis}[",
        "  width=\\linewidth, height=6cm,",
        "  xlabel={$\\Delta J$ against \\texttt{off}},",
        "  ytick=data, yticklabels={" + ",".join(d.arm for d in deltas) + "},",
        "  ymin=0.5, ymax=" + f"{len(deltas) + 0.5:.1f}" + ",",
        "]",
        "\\draw[dashed] (axis cs:0,0.5) -- (axis cs:0," + f"{len(deltas) + 0.5:.1f}" + ");",
        "\\addplot+[only marks, error bars/.cd, x dir=both, x explicit]",
        "coordinates {",
    ]
    for index, delta in enumerate(deltas, start=1):
        lines.append(
            f"  ({delta.estimate:.3f},{index}) "
            f"+- ({delta.ci_high - delta.estimate:.3f},0) "
            f"-= ({delta.estimate - delta.ci_low:.3f},0)"
        )
    lines += ["};", "\\end{axis}", "\\end{tikzpicture}", ""]
    return "\n".join(lines)


def write_figures(repo_root: Path, out_dir: Path) -> FiguresResult:
    """Build every artefact under ``out_dir``, or an empty one if nothing ran.

    With no published run this writes a macro file holding no definitions and
    returns cleanly, so a bare checkout gets a generator that exits zero rather
    than one that raises. It does not get a PDF: no tables are written and every
    ``\\NUM`` in the paper would be undefined.
    """
    generated = out_dir / "generated"
    figures = out_dir / "figures"
    generated.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    run_dir = latest_run(repo_root)
    if run_dir is None:
        macros = generated / "macros.tex"
        macros.write_text(render_macros({}), encoding="utf-8")
        return FiguresResult(run=None, macros=0, paths=(macros,))

    study = read_study(run_dir)
    values = collect(study, repo_root)

    written: list[Path] = []
    for path, text in (
        (generated / "macros.tex", render_macros(values)),
        (generated / "tables.tex", render_tables(study)),
        (figures / "accuracy.tex", render_accuracy_plot(study)),
        (figures / "signal.tex", render_signal_plot(study)),
    ):
        path.write_text(text, encoding="utf-8")
        written.append(path)

    return FiguresResult(run=study.run, macros=len(values), paths=tuple(written))
