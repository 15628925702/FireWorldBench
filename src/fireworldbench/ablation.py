"""Guarded preregistered ablation plan and no-run decision."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

ABLATION_VERSION = "P5-ABLATION-001"


def build_ablation_plan() -> dict[str, Any]:
    return {
        "ablation_version": ABLATION_VERSION,
        "status": "BLOCKED_NO_MAIN_RUN",
        "factors": [
            {"name": "information_budget", "baseline": "text_only_table", "variants": ["retrieval", "plot", "formula_fds_proxy", "tool_use"], "changed_factor_count": 1},
            {"name": "evidence_visibility", "baseline": "all_approved_observations", "variants": ["reduced_observations"], "changed_factor_count": 1},
            {"name": "uncertainty_reporting", "baseline": "enabled", "variants": ["disabled"], "changed_factor_count": 1},
        ],
        "main_run_required": True,
        "ablation_runs": [],
        "parameter_diffs": [],
        "paired_result_index": [],
        "extra_findings_label": "exploratory_only",
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def assess_ablation(main_run: Mapping[str, Any]) -> dict[str, Any]:
    result = build_ablation_plan()
    blockers: list[str] = []
    if main_run.get("status") != "READY_TO_RUN":
        blockers.append("main_run_not_ready")
    if not main_run.get("run_index"):
        blockers.append("main_run_index_empty")
    result["blockers"] = blockers
    result["status"] = "READY_TO_RUN" if not blockers else "BLOCKED_NO_MAIN_RUN"
    return result


def write_ablation_decision(main_run_path: Path, output_path: Path) -> dict[str, Any]:
    main_run = json.loads(main_run_path.read_text(encoding="utf-8"))
    if not isinstance(main_run, Mapping):
        raise TypeError("main-run decision must be a JSON object")
    result = assess_ablation(main_run)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
