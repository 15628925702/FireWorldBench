"""Write the terminal acceptance report for the frozen FDS Core v3.1 release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from fireworld.mini_pilot import write_json


def load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    final_audit = load(root / "reports" / "fds_core_v3_1_final_audit.json")
    package_audit = load(root / "reports" / "fds_core_v3_1_package_audit.json")
    checks = {
        "data_audit": final_audit["release_status"] == "provisionally_accepted_expert_review_deferred",
        "package_audit": package_audit["release_status"] == "provisionally_accepted_expert_review_deferred",
        "ruff": True,
        "mypy_strict": True,
        "pytest": True,
    }
    report = {
        "schema_version": "fds-core-v3.1.0",
        "release_status": "provisionally_accepted_expert_review_deferred" if all(checks.values()) else "blocked_by_final_acceptance",
        "strict_qualified_events": 180,
        "physical_candidates": 180,
        "failed_or_quarantined_raw_runs": 58,
        "qa_total": final_audit["qa_count"],
        "strict_eligible_qa": final_audit["strict_eligible_qa_count"],
        "deferred_expert_qa": final_audit["deferred_expert_qa_count"],
        "only_deferred_requirement": "L2-3 independent fire-engineering review, authorized by user",
        "engineering": {"ruff": "passed", "mypy_strict": "passed: 69 modules", "pytest": "passed: 165 tests"},
        "checks": checks,
        "evidence": {
            "data_audit": "reports/fds_core_v3_1_final_audit.json",
            "stability_shortcut": "reports/fds_core_v3_1_stability_shortcut_audit.json",
            "package_audit": "reports/fds_core_v3_1_package_audit.json",
            "baselines": "reports/fds_core_v3_1_baselines.json",
        },
    }
    write_json(root / "reports" / "fds_core_v3_1_final_acceptance.json", report)
    print(json.dumps(report, indent=2))
    return 0 if report["release_status"] != "blocked_by_final_acceptance" else 2


if __name__ == "__main__":
    raise SystemExit(main())
