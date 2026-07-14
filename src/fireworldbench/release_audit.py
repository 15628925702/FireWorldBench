"""Final release-freeze audit without external release side effects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RELEASE_VERSION = "P7-RELEASE-001"


def assess_release_freeze() -> dict[str, Any]:
    critical_risks = [
        "frozen_results_missing",
        "paper_export_missing",
        "anonymous_package_missing",
        "clean_room_reproduction_missing",
        "external_release_approval_missing",
        "github_history_sync_blocked",
    ]
    return {
        "release_version": RELEASE_VERSION,
        "status": "BLOCKED_CRITICAL_RISKS",
        "critical_risks": critical_risks,
        "stage_gates": {
            "P2_P3_contracts": "FROZEN",
            "P4_baselines_and_pilot": "FROZEN_OR_BLOCKED",
            "P5_results_and_claims": "BLOCKED_NO_RESULTS",
            "P6_tables_figures_text_audit_export": "BLOCKED_NO_FROZEN_RESULTS",
            "P7_anonymization_reproduction": "BLOCKED_NO_INPUT",
        },
        "version_audit": {"status": "RECORDED", "code_commit": None, "configs": [], "environment": None},
        "checksum_audit": {"status": "BLOCKED_NO_EXPORT", "manifests": [], "checksums": []},
        "paper_data_audit": {"status": "BLOCKED_NO_FROZEN_RESULTS", "tables": [], "figures": [], "text_numbers": []},
        "anonymous_reproduction_audit": {"status": "BLOCKED_NO_INPUT", "anonymous_package": None, "reproduction": None},
        "external_release": {
            "user_approval": False,
            "tag_created": False,
            "github_release_created": False,
            "push_performed": False,
        },
        "manifest_self_hash_excluded": True,
        "local_freeze_only": True,
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def write_release_audit(output_path: Path) -> dict[str, Any]:
    result = assess_release_freeze()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
