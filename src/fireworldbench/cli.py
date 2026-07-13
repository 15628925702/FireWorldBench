"""Minimal CLI for project bootstrap checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from fireworldbench import __version__
from fireworldbench.project_checks import discover_project_root, validate_project
from fireworldbench.pipeline import build_canonical, inventory, write_json
from fireworldbench.t1_builder import build_t1
from fireworldbench.t2_builder import build_t2
from fireworldbench.t3_builder import build_t3
from fireworldbench.scorer import score_files
from fireworldbench.expert import consistency_file
from fireworldbench.release import build_mvp_rc1
from fireworldbench.harness import run_harness
from fireworldbench.baseline import run_baseline_file
from fireworldbench.vision_baseline import assess_visual_baseline_file
from fireworldbench.llm_baseline import run_llm_pilot_file
from fireworldbench.tool_tracks import run_tool_ablation_file
from fireworldbench.pilot_freeze import write_pilot_plan
from fireworldbench.fdgen import write_fdgen_decision
from fireworldbench.benchmark_integration import write_integration_decision
from fireworldbench.calibration import write_calibration_decision
from fireworldbench.preregister import write_preregistration
from fireworldbench.main_run import write_main_run_decision
from fireworldbench.ablation import write_ablation_decision
from fireworldbench.robustness import write_robustness_decision
from fireworldbench.stats import write_statistics_decision
from fireworldbench.error_analysis import write_error_decision
from fireworldbench.claims import write_claims_matrix


def doctor(root: Path) -> int:
    errors = validate_project(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"FireWorldBench {__version__}: project bootstrap invariants verified at {root}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fwb")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor_parser = subparsers.add_parser("doctor", help="validate project bootstrap invariants")
    doctor_parser.add_argument(
        "--root",
        type=Path,
        help="project root; otherwise discover from cwd",
    )
    inventory_parser = subparsers.add_parser("pipeline-inventory", help="hash source files without modifying them")
    inventory_parser.add_argument("--root", type=Path, required=True)
    inventory_parser.add_argument("--output", type=Path, required=True)
    pipeline_parser = subparsers.add_parser("pipeline-build", help="build canonical records and case graph")
    pipeline_parser.add_argument("--root", type=Path, required=True)
    pipeline_parser.add_argument("--source-dataset-id", default="UNKNOWN")
    pipeline_parser.add_argument("--output", type=Path, required=True)
    t1_parser = subparsers.add_parser("build-t1", help="build T1-A/B/C train or dev samples")
    t1_parser.add_argument("--input", type=Path, required=True, help="canonical pipeline JSON")
    t1_parser.add_argument("--split", choices=("train_id", "dev_id"), default="dev_id")
    t1_parser.add_argument("--output", type=Path, required=True)
    t2_parser = subparsers.add_parser("build-t2", help="build T2-A/B/C train or dev samples")
    t2_parser.add_argument("--input", type=Path, required=True, help="canonical pipeline JSON")
    t2_parser.add_argument("--split", choices=("train_id", "dev_id"), default="dev_id")
    t2_parser.add_argument("--output", type=Path, required=True)
    t3_parser = subparsers.add_parser("build-t3", help="build T3-A/B/C train or dev samples")
    t3_parser.add_argument("--input", type=Path, required=True, help="canonical pipeline JSON")
    t3_parser.add_argument("--split", choices=("train_id", "dev_id"), default="dev_id")
    t3_parser.add_argument("--output", type=Path, required=True)
    score_parser = subparsers.add_parser("score", help="score predictions against explicit samples")
    score_parser.add_argument("--samples", type=Path, required=True)
    score_parser.add_argument("--predictions", type=Path, required=True)
    score_parser.add_argument("--output", type=Path, required=True)
    expert_parser = subparsers.add_parser("expert-consistency", help="compute two-rater calibration agreement")
    expert_parser.add_argument("--input", type=Path, required=True)
    expert_parser.add_argument("--output", type=Path, required=True)
    release_parser = subparsers.add_parser("mvp-build", help="build reproducible MVP RC1 public/private packages")
    release_parser.add_argument("--input", type=Path, required=True)
    release_parser.add_argument("--output", type=Path, required=True)
    harness_parser = subparsers.add_parser("harness-run", help="run a train/dev-only adapter harness")
    harness_parser.add_argument("--samples", type=Path, required=True)
    harness_parser.add_argument("--output", type=Path, required=True)
    harness_parser.add_argument("--max-retries", type=int, default=0)
    harness_parser.add_argument("--timeout-s", type=float, default=30.0)
    baseline_parser = subparsers.add_parser("baseline-run", help="run deterministic train/dev baselines")
    baseline_parser.add_argument("--samples", type=Path, required=True)
    baseline_parser.add_argument("--output", type=Path, required=True)
    baseline_parser.add_argument("--strategy", choices=("chance", "majority", "domain_threshold", "traditional_ml", "temporal_persistence"), required=True)
    baseline_parser.add_argument("--train-samples", type=Path)
    vision_parser = subparsers.add_parser("vision-baseline", help="record the train/dev-only visual baseline decision")
    vision_parser.add_argument("--output", type=Path, required=True)
    vision_parser.add_argument("--samples", type=Path)
    vision_parser.add_argument("--visual-root", type=Path)
    llm_parser = subparsers.add_parser("llm-pilot", help="run or record a frozen train/dev-only LLM pilot")
    llm_parser.add_argument("--config", type=Path, required=True)
    llm_parser.add_argument("--output", type=Path, required=True)
    llm_parser.add_argument("--samples", type=Path)
    tool_parser = subparsers.add_parser("tool-ablation", help="run or record independent train/dev-only tool tracks")
    tool_parser.add_argument("--config", type=Path, required=True)
    tool_parser.add_argument("--output", type=Path, required=True)
    tool_parser.add_argument("--samples", type=Path)
    pilot_parser = subparsers.add_parser("pilot-freeze", help="write the frozen train/dev pilot plan")
    pilot_parser.add_argument("--output", type=Path, required=True)
    fdgen_parser = subparsers.add_parser("fdgen-assess", help="audit frozen FD-Gen readiness without generating scenes")
    fdgen_parser.add_argument("--plan", type=Path, required=True)
    fdgen_parser.add_argument("--output", type=Path, required=True)
    integration_parser = subparsers.add_parser("benchmark-integrate", help="audit generated-case integration readiness")
    integration_parser.add_argument("--fdgen-decision", type=Path, required=True)
    integration_parser.add_argument("--output", type=Path, required=True)
    calibration_parser = subparsers.add_parser("calibration-assess", help="audit final train/dev calibration readiness")
    calibration_parser.add_argument("--output", type=Path, required=True)
    calibration_parser.add_argument("--samples", type=Path)
    calibration_parser.add_argument("--model-config", type=Path)
    prereg_parser = subparsers.add_parser("prereg-freeze", help="write the frozen preregistration and test embargo")
    prereg_parser.add_argument("--output", type=Path, required=True)
    main_parser = subparsers.add_parser("main-run-assess", help="audit frozen main-matrix execution readiness")
    main_parser.add_argument("--prereg", type=Path, required=True)
    main_parser.add_argument("--output", type=Path, required=True)
    main_parser.add_argument("--calibration", type=Path)
    main_parser.add_argument("--inputs", type=Path)
    ablation_parser = subparsers.add_parser("ablation-assess", help="audit preregistered ablation readiness")
    ablation_parser.add_argument("--main-run", type=Path, required=True)
    ablation_parser.add_argument("--output", type=Path, required=True)
    robust_parser = subparsers.add_parser("robustness-assess", help="audit preregistered robustness readiness")
    robust_parser.add_argument("--main-run", type=Path, required=True)
    robust_parser.add_argument("--output", type=Path, required=True)
    stats_parser = subparsers.add_parser("stats-assess", help="audit raw-prediction statistics readiness")
    stats_parser.add_argument("--output", type=Path, required=True)
    stats_parser.add_argument("--raw-predictions", type=Path)
    error_parser = subparsers.add_parser("error-assess", help="audit blind error-analysis readiness")
    error_parser.add_argument("--output", type=Path, required=True)
    error_parser.add_argument("--raw-predictions", type=Path)
    claims_parser = subparsers.add_parser("claims-freeze", help="write the claims-evidence freeze matrix")
    claims_parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        try:
            root = args.root.resolve() if args.root else discover_project_root()
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}")
            return 2
        return doctor(root)
    if args.command == "pipeline-inventory":
        try:
            result = inventory(args.root)
            write_json(result, args.output)
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"file_count": result["file_count"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "pipeline-build":
        try:
            result = build_canonical(args.root, source_dataset_id=args.source_dataset_id)
            write_json(result, args.output)
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"record_count": result["record_count"], "failure_count": result["failure_count"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "build-t1":
        try:
            payload = json.loads(args.input.read_text(encoding="utf-8"))
            result = build_t1(payload.get("records", []), split=args.split, parent_manifest_sha256=payload.get("manifest_sha256"))
            write_json(result, args.output)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"sample_count": result["sample_count"], "failure_count": result["failure_count"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "build-t2":
        try:
            payload = json.loads(args.input.read_text(encoding="utf-8"))
            result = build_t2(payload.get("records", []), split=args.split, parent_manifest_sha256=payload.get("manifest_sha256"))
            write_json(result, args.output)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"sample_count": result["sample_count"], "failure_count": result["failure_count"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "build-t3":
        try:
            payload = json.loads(args.input.read_text(encoding="utf-8"))
            result = build_t3(payload.get("records", []), split=args.split, parent_manifest_sha256=payload.get("manifest_sha256"))
            write_json(result, args.output)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"sample_count": result["sample_count"], "failure_count": result["failure_count"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "score":
        try:
            result = score_files(args.samples, args.predictions, args.output)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"sample_count": len(result["sample_scores"]), "failure_counts": result["failure_counts"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "expert-consistency":
        try:
            result = consistency_file(args.input, args.output)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"paired_sample_count": result["paired_sample_count"], "adjudication_required": len(result["adjudication_required"]), "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "mvp-build":
        try:
            result = build_mvp_rc1(args.input, args.output)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == "harness-run":
        try:
            payload = json.loads(args.samples.read_text(encoding="utf-8"))
            samples = payload.get("samples", payload) if isinstance(payload, dict) else payload
            result = run_harness(samples, args.output, max_retries=args.max_retries, timeout_s=args.timeout_s)
        except (OSError, ValueError, TypeError, json.JSONDecodeError, PermissionError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"run_id": result["run_id"], "sample_count": result["sample_count"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "baseline-run":
        try:
            result = run_baseline_file(args.samples, args.output, args.strategy, args.train_samples)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"strategy": result["strategy"], "sample_count": result["sample_count"], "failure_count": result["failure_count"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "vision-baseline":
        try:
            result = assess_visual_baseline_file(args.output, samples_path=args.samples, visual_root=args.visual_root)
        except (OSError, ValueError, TypeError, json.JSONDecodeError, PermissionError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "sample_count": result["sample_count"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "llm-pilot":
        try:
            result = run_llm_pilot_file(args.samples, args.config, args.output)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "sample_count": result["sample_count"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "tool-ablation":
        try:
            result = run_tool_ablation_file(args.config, args.output, args.samples)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "track_count": len(result["tracks"]), "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "pilot-freeze":
        try:
            result = write_pilot_plan(args.output)
        except (OSError, ValueError, TypeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "plan_sha256": result["plan_sha256"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "fdgen-assess":
        try:
            result = write_fdgen_decision(args.plan, args.output)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "blocker_count": len(result["blockers"]), "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "benchmark-integrate":
        try:
            result = write_integration_decision(args.fdgen_decision, args.output)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "input_case_count": result["input_case_count"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "calibration-assess":
        try:
            result = write_calibration_decision(args.output, samples_path=args.samples, model_config_path=args.model_config)
        except (OSError, ValueError, TypeError, json.JSONDecodeError, PermissionError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "blocker_count": len(result["blockers"]), "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "prereg-freeze":
        try:
            result = write_preregistration(args.output)
        except (OSError, ValueError, TypeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "plan_sha256": result["plan_sha256"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "main-run-assess":
        try:
            result = write_main_run_decision(args.output, args.prereg, calibration_path=args.calibration, input_manifest_path=args.inputs)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "blocker_count": len(result["blockers"]), "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "ablation-assess":
        try:
            result = write_ablation_decision(args.main_run, args.output)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "factor_count": len(result["factors"]), "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "robustness-assess":
        try:
            result = write_robustness_decision(args.main_run, args.output)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "transformation_count": len(result["transformations"]), "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "stats-assess":
        try:
            result = write_statistics_decision(args.output, args.raw_predictions)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "sample_count": result["sample_count"], "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "error-assess":
        try:
            result = write_error_decision(args.output, args.raw_predictions)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "taxonomy_count": len(result["taxonomy"]), "output": str(args.output)}, ensure_ascii=False))
        return 0
    if args.command == "claims-freeze":
        try:
            result = write_claims_matrix(args.output)
        except (OSError, ValueError, TypeError) as exc:
            print(f"ERROR: {exc}")
            return 2
        print(json.dumps({"status": result["status"], "claim_count": len(result["claims"]), "output": str(args.output)}, ensure_ascii=False))
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
