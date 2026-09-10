#!/usr/bin/env python3
"""Targeted ablation probe: measure the effect of removing memorized constants from evolved winners.

Compares:
  - gepa vs gepa-ablated
  - skillopt vs skillopt-ablated
against their matched placebos and unprompted baselines on the 392 seen items.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals" / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from decision_evals.budget import BudgetLedger  # noqa: E402
from decision_evals.evolution.lineage import body_sha  # noqa: E402
from decision_evals.evolution.run import items_for  # noqa: E402
from decision_evals.evolution.venues import (  # noqa: E402
    assert_cap_fits,
    call_fn,
    context_window,
    venue_for,
)
from decision_evals.generators import parse_roots  # noqa: E402
from decision_evals.runner import run_arm  # noqa: E402
from decision_evals.solvers.arms import build_arm  # noqa: E402
from decision_evals.stats.paired import mcnemar_exact  # noqa: E402

SEEN_TEMPLATES = [
    "hrd-001-warranty-claim",
    "hrd-002-shipping-escalation",
    "hrd-006-appeal-window",
    "rel-003-oncall-escalate",
    "rel-006-refund-request",
    "rel-007-capacity-scale",
    "rel-010-loan-review",
]
SEEN_SEEDS = [10989, 10996]

FROZEN_STUDY_DIR = REPO_ROOT / "results/evolution-study/2026-09-03-e235b98-seven-unseen-v2"
DEFAULT_OUT_DIR = REPO_ROOT / "results/evolution/2026-09-10-prompt-constant-ablation"

ABLATED_ARMS = {
    "gepa-ablated": REPO_ROOT / "datasets/ablations/gepa-ablated.md",
    "skillopt-ablated": REPO_ROOT / "datasets/ablations/skillopt-ablated.md",
}


def load_study_records(arm_label: str) -> dict[tuple[str, int], dict[str, Any]]:
    """Load seen-set records from the published frozen study."""
    path = FROZEN_STUDY_DIR / f"records-{arm_label}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Missing frozen study records: {path}")
    records = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            # Only seen seeds
            if rec.get("seed") in SEEN_SEEDS and rec.get("template_id") in SEEN_TEMPLATES:
                records[(rec["item_id"], rec["seed"])] = rec
    return records


def analyze_ablation(
    ablated_records: dict[tuple[str, int], dict[str, Any]],
    original_records: dict[tuple[str, int], dict[str, Any]],
    placebo_records: dict[tuple[str, int], dict[str, Any]],
    off_records: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Compute paired statistics between original and ablated arms."""
    common_ids = sorted(
        set(ablated_records.keys())
        & set(original_records.keys())
        & set(placebo_records.keys())
        & set(off_records.keys())
    )
    if not common_ids:
        return {"error": "No overlapping items found"}

    ablated_correct = [ablated_records[iid]["correct"] for iid in common_ids]
    original_correct = [original_records[iid]["correct"] for iid in common_ids]
    placebo_correct = [placebo_records[iid]["correct"] for iid in common_ids]
    off_correct = [off_records[iid]["correct"] for iid in common_ids]

    n = len(common_ids)
    acc_ablated = sum(ablated_correct) / n
    acc_original = sum(original_correct) / n
    acc_placebo = sum(placebo_correct) / n
    acc_off = sum(off_correct) / n

    # Paired McNemar: ablated vs original
    mcn_res = mcnemar_exact(
        control=original_correct, treatment=ablated_correct, alternative="two-sided"
    )
    orig_only = mcn_res.control_wins
    abl_only = mcn_res.treatment_wins
    p_val = mcn_res.p_value

    # Per template breakdown
    by_template = defaultdict(lambda: {"ablated": [], "original": [], "placebo": [], "off": []})
    for iid in common_ids:
        tid = ablated_records[iid]["template_id"]
        by_template[tid]["ablated"].append(ablated_records[iid]["correct"])
        by_template[tid]["original"].append(original_records[iid]["correct"])
        by_template[tid]["placebo"].append(placebo_records[iid]["correct"])
        by_template[tid]["off"].append(off_records[iid]["correct"])

    template_stats = {}
    for tid, data in sorted(by_template.items()):
        m = len(data["ablated"])
        template_stats[tid] = {
            "n": m,
            "acc_ablated": sum(data["ablated"]) / m,
            "acc_original": sum(data["original"]) / m,
            "acc_placebo": sum(data["placebo"]) / m,
            "acc_off": sum(data["off"]) / m,
            "delta_vs_original": (sum(data["ablated"]) - sum(data["original"])) / m,
            "delta_vs_placebo": (sum(data["ablated"]) - sum(data["placebo"])) / m,
        }

    return {
        "n_items": n,
        "acc_ablated": acc_ablated,
        "acc_original": acc_original,
        "acc_placebo": acc_placebo,
        "acc_off": acc_off,
        "delta_vs_original": acc_ablated - acc_original,
        "delta_vs_placebo": acc_ablated - acc_placebo,
        "paired_test": {
            "ablated_wins": abl_only,
            "original_wins": orig_only,
            "p_value": p_val,
        },
        "per_template": template_stats,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run targeted ablation probe on prompt constants.")
    parser.add_argument("--model", default="ollama/qwen3:1.7b", help="Target model.")
    parser.add_argument("--num-ctx", type=int, default=16384, help="Context window.")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Output cap.")
    parser.add_argument("--limit", type=int, default=None, help="Limit items per arm for dry runs.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR, help="Output directory.")
    parser.add_argument(
        "--arm",
        choices=["all", "gepa", "skillopt"],
        default="all",
        help="Which ablation arm(s) to run.",
    )
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    roots = parse_roots("datasets/templates,datasets/templates-hard", base=REPO_ROOT)

    # 1. Load seen items
    items = items_for(SEEN_SEEDS, templates=set(SEEN_TEMPLATES), root=roots)
    if args.limit:
        items = items[: args.limit]
    print(f"Loaded {len(items)} items across {len(SEEN_TEMPLATES)} seen templates.")

    # 2. Setup venue and CallFn
    venue = venue_for(args.model)
    window = context_window(venue)
    assert_cap_fits(args.num_ctx or window, args.max_tokens)
    call = call_fn(venue, max_tokens=args.max_tokens, num_ctx=args.num_ctx)

    arms_to_run = (
        ["gepa-ablated", "skillopt-ablated"] if args.arm == "all" else [f"{args.arm}-ablated"]
    )

    ledger = BudgetLedger(
        limit_usd=0.0,
        limit_calls=len(items) * len(arms_to_run) + 10,
        limit_seconds=86400.0,
        bills=venue.bills,
    )

    # 3. Execute runs for ablated arms
    for arm_label in arms_to_run:
        prompt_path = ABLATED_ARMS[arm_label]
        skill_body = prompt_path.read_text(encoding="utf-8")
        arm_prompt = build_arm("candidate", skill_body=skill_body)
        checkpoint = args.out / f"records-{arm_label}.jsonl"

        print(f"\n=== Running {arm_label} ({len(items)} items) -> {checkpoint.name} ===")
        run_arm(
            items=items,
            arm=arm_prompt,
            model=args.model,
            checkpoint=checkpoint,
            call=call,
            ledger=ledger,
            concurrency=1,
            candidate_sha=body_sha(skill_body),
            resume_fields=("item_id", "arm", "seed"),
        )

    # 4. Analysis and Comparison
    print("\n=== Running Analysis ===")
    analysis_results = {}

    off_records = load_study_records("off")

    if "gepa-ablated" in arms_to_run:
        gepa_abl_path = args.out / "records-gepa-ablated.jsonl"
        if gepa_abl_path.exists():
            gepa_abl_recs = {
                (r["item_id"], r["seed"]): r
                for line in gepa_abl_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
                for r in [json.loads(line)]
            }
            gepa_orig_recs = load_study_records("gepa")
            gepa_placebo_recs = load_study_records("placebo-gepa")
            analysis_results["gepa"] = analyze_ablation(
                gepa_abl_recs, gepa_orig_recs, gepa_placebo_recs, off_records
            )

    if "skillopt-ablated" in arms_to_run:
        skillopt_abl_path = args.out / "records-skillopt-ablated.jsonl"
        if skillopt_abl_path.exists():
            skillopt_abl_recs = {
                (r["item_id"], r["seed"]): r
                for line in skillopt_abl_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
                for r in [json.loads(line)]
            }
            skillopt_orig_recs = load_study_records("skillopt")
            skillopt_placebo_recs = load_study_records("placebo-skillopt")
            analysis_results["skillopt"] = analyze_ablation(
                skillopt_abl_recs, skillopt_orig_recs, skillopt_placebo_recs, off_records
            )

    analysis_path = args.out / "analysis.json"
    analysis_path.write_text(json.dumps(analysis_results, indent=2), encoding="utf-8")
    print(f"Analysis saved to {analysis_path}")

    # Print summary tables
    for name, res in analysis_results.items():
        print(f"\n--- Results for {name.upper()}: Original vs Ablated ---")
        print(
            f"Overall Accuracy: Original={res['acc_original']:.4f} | Ablated={res['acc_ablated']:.4f} | Placebo={res['acc_placebo']:.4f} | Off={res['acc_off']:.4f}"
        )
        print(
            f"Delta (Ablated - Original): {res['delta_vs_original']:+.4f} (p = {res['paired_test']['p_value']:.4f})"
        )
        print(
            f"Wins / Losses (Ablated / Original): {res['paired_test']['ablated_wins']} / {res['paired_test']['original_wins']}"
        )
        print(
            f"\n{'Template':<32} {'Orig':>8} {'Ablated':>8} {'Delta':>8} {'Placebo':>8} {'Off':>8}"
        )
        print("-" * 76)
        for tid, tdata in res["per_template"].items():
            print(
                f"{tid:<32} {tdata['acc_original']:8.4f} {tdata['acc_ablated']:8.4f} "
                f"{tdata['delta_vs_original']:+8.4f} {tdata['acc_placebo']:8.4f} {tdata['acc_off']:8.4f}"
            )


if __name__ == "__main__":
    main()
