"""Write the terminal fail-closed acceptance for the immutable v3.2 package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from fireworld.mini_pilot import write_json

VERSION = "fds-core-v3.2.0"
PDF_SHA256 = "ba63ab8428d1f759629a89864af7f623589d023dd6d5a29e4940fc6d629a19a6"


def load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text()))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    release = root / "release/fireworldbench_fds_core_v3_2"
    manifest = load(release / "release_manifest.json")
    package_audit = load(root / "reports/fds_core_v3_2_package_audit.json")
    data_audit = load(root / "reports/fds_core_v3_2_data_audit.json")
    stability = load(root / "reports/fds_core_v3_2_stability_shortcut_audit.json")
    engineering = load(root / "reports/fds_core_v3_2_engineering_audit.json")
    physical = load(root / "reports/fds_core_v3_2_trajectory_repair_physical_audit.json")
    unique = load(root / "reports/fds_core_v3_2_global_trajectory_uniqueness.json")
    visual = load(root / "reports/fds_core_v3_2_trajectory_repair_visual_audit.json")
    baselines = load(root / "reports/fds_core_v3_2_baselines.json")
    pdf = root / "2.方案研究/FireWorldBenchv2(1).pdf"
    missing_files = [
        name for name in manifest["files"] if not (release / name).is_file()
    ]
    hash_mismatches = [
        name
        for name, expected in manifest["files"].items()
        if (release / name).is_file() and sha256(release / name) != expected
    ]
    checks = {
        "design_pdf_sha256": pdf.is_file() and sha256(pdf) == PDF_SHA256,
        "physical_repair_audit": physical["status"] == "passed",
        "global_180_trajectory_unique": unique["status"] == "passed"
        and unique["events"] == 180
        and unique["unique_trajectories"] == 180,
        "dynamic_visual_audit": visual["status"] == "passed",
        "data_audit": data_audit["status"]
        == "passed_data_gates_pending_release_experiments",
        "stability_shortcut_audit": stability["status"]
        == "passed_pending_package_audit",
        "engineering_audit": engineering["status"] == "passed",
        "baseline_and_oracle_replay": baselines[
            "oracle_self_check_excluded_from_results"
        ]["overall"]
        == 100.0
        and baselines["llm_judge_used"] is False,
        "package_audit": package_audit["release_status"]
        == "provisionally_accepted_expert_review_deferred"
        and all(package_audit["checks"].values()),
        "manifest_status": manifest["status"]
        == "provisionally_accepted_expert_review_deferred",
        "manifest_files_present_and_unchanged": not missing_files
        and not hash_mismatches,
        "same_snapshot": package_audit["snapshot_id"] == manifest["snapshot_id"],
        "counts": manifest["events"] == 180 and 4000 <= manifest["qa_total"] <= 6000,
        "expert_review_is_only_deferred_requirement": manifest[
            "expert_review_status"
        ]
        == "deferred_by_user_L2-3_only",
    }
    accepted = all(checks.values())
    report = {
        "schema_version": VERSION,
        "release_status": (
            "provisionally_accepted_expert_review_deferred"
            if accepted
            else "blocked_by_final_acceptance"
        ),
        "snapshot_id": manifest["snapshot_id"],
        "strict_qualified_events": 180 if accepted else 0,
        "physical_candidates": 180,
        "historical_failed_or_quarantined_raw_runs": 58,
        "qa_total": manifest["qa_total"],
        "task_counts": manifest["task_counts"],
        "track_counts": manifest["track_counts"],
        "expert_review_status": "deferred_by_user_L2-3_only",
        "only_deferred_requirement": "independent fire-engineering review of six L2-3 mechanism labels",
        "checks": checks,
        "errors": {
            "missing_package_files": missing_files,
            "package_hash_mismatches": hash_mismatches,
        },
        "evidence": {
            "package": "release/fireworldbench_fds_core_v3_2",
            "package_audit": "reports/fds_core_v3_2_package_audit.json",
            "data_audit": "reports/fds_core_v3_2_data_audit.json",
            "stability_shortcut": "reports/fds_core_v3_2_stability_shortcut_audit.json",
            "engineering": "reports/fds_core_v3_2_engineering_audit.json",
            "baselines": "reports/fds_core_v3_2_baselines.json",
        },
    }
    write_json(root / "reports/fds_core_v3_2_final_acceptance.json", report)
    print(json.dumps(report, indent=2))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
