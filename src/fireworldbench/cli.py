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
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
