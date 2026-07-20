"""Terminal fail-closed acceptance for formally reviewed FDS Core v3.3."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from fireworld.mini_pilot import write_json

VERSION = "fds-core-v3.3.1"
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
    release = root / "release/fireworldbench_fds_core_v3_3_1"
    manifest = load(release / "release_manifest.json")
    package = load(root / "reports/fds_core_v3_3_1_package_audit.json")
    predecessor = load(root / "reports/fds_core_v3_2_final_acceptance.json")
    transition = load(root / "reports/fds_core_v3_3_formal_transition_audit.json")
    expert = load(root / "reports/private/fds_core_v3_3_expert_review_record.json")
    engineering = load(root / "reports/fds_core_v3_2_engineering_audit.json")
    missing = [name for name in manifest["files"] if not (release / name).is_file()]
    mismatches = [
        name
        for name, expected in manifest["files"].items()
        if (release / name).is_file() and sha256(release / name) != expected
    ]
    checks = {
        "design_pdf_sha256": sha256(root / "2.方案研究/FireWorldBenchv2(1).pdf")
        == PDF_SHA256,
        "expert_review_completed": expert["status"] == "completed"
        and expert["reviewed_qa_count"] == 6,
        "formal_transition_audit": transition["status"]
        == "passed_pending_formal_package",
        "formal_package_audit": package["release_status"] == "formally_accepted"
        and all(package["checks"].values()),
        "engineering_audit": engineering["status"] == "passed",
        "manifest_status": manifest["status"] == "formally_accepted",
        "manifest_files_present_and_unchanged": not missing and not mismatches,
        "same_snapshot": manifest["snapshot_id"] == package["snapshot_id"],
        "predecessor_snapshot_resolves": manifest["predecessor_snapshot_id"]
        == predecessor["snapshot_id"],
        "counts": manifest["events"] == 180 and manifest["qa_total"] == 4039,
        "expert_review_no_longer_deferred": manifest["expert_review_status"]
        == "completed",
    }
    accepted = all(checks.values())
    report = {
        "schema_version": VERSION,
        "release_status": "formally_accepted" if accepted else "blocked_by_final_acceptance",
        "snapshot_id": manifest["snapshot_id"],
        "strict_qualified_events": 180 if accepted else 0,
        "physical_candidates": 180,
        "historical_failed_or_quarantined_raw_runs": 58,
        "qa_total": manifest["qa_total"],
        "task_counts": manifest["task_counts"],
        "track_counts": manifest["track_counts"],
        "expert_review_status": "completed",
        "checks": checks,
        "errors": {"missing_package_files": missing, "package_hash_mismatches": mismatches},
        "evidence": {
            "package": "release/fireworldbench_fds_core_v3_3_1",
            "package_audit": "reports/fds_core_v3_3_1_package_audit.json",
            "formal_transition": "reports/fds_core_v3_3_formal_transition_audit.json",
            "expert_review_private": "reports/private/fds_core_v3_3_expert_review_record.json",
        },
    }
    write_json(root / "reports/fds_core_v3_3_1_final_acceptance.json", report)
    print(json.dumps(report, indent=2))
    return 0 if accepted else 2


if __name__ == "__main__":
    raise SystemExit(main())
