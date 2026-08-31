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
import string
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from decision_evals.skills import delivered_body
from decision_evals.solvers.arms import check_placebo_match
from decision_evals.stats.cluster import cluster_bootstrap_diff
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

#: Resampling draws for the cluster bootstrap. Matches the notebook entry of
#: 2026-08-28, so the paper reproduces the intervals published there rather than
#: near-misses of them.
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
    A bare checkout with no results is not an error: the Makefile promises the
    skeleton compiles before any run has happened.
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
            readings.append(
                Reading(
                    arm=arm,
                    item_id=row["item_id"],
                    template_id=row["template_id"],
                    seed=int(row["seed"]),
                    expected=row["expected"],
                    parsed=row["parsed"] if row["parse_status"] == "parsed" else None,
                )
            )
    if not readings:
        raise FigureError(f"no arm records under {run_dir}")
    return readings


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

    A template whose parsed answers hold a single class has no informedness, and
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

    aa = analysis.get("aa")
    if aa is not None:
        values[_macro_name("aa", "pairs")] = str(aa["n_pairs"])
        values[_macro_name("aa", "disagreements")] = str(aa["arm_only"] + aa["control_only"])
        values[_macro_name("aa", "p")] = _fixed(aa["p_value"], 4)
        values[_macro_name("aa", "accuracy")] = _fixed(aa["accuracy"], 4)

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
    returns cleanly. ``paper/Makefile`` promises exactly that, so the skeleton
    compiles from a bare checkout and a reader who has not run anything still
    gets a PDF.
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
