"""Guarded preregistered robustness transformation plan."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

ROBUST_VERSION = "P5-ROBUST-001"


def build_robustness_manifest() -> dict[str, Any]:
    transformations = [
        {"name": "sensor_noise", "target": "numeric_observations", "label_invariant_required": True},
        {"name": "missing_observation", "target": "numeric_observations", "label_invariant_required": True},
        {"name": "sensor_fault", "target": "sensor_observations", "label_invariant_required": True},
        {"name": "visual_degradation", "target": "approved_visual_inputs", "label_invariant_required": True},
        {"name": "wording_variation", "target": "prompt_surface_form", "label_invariant_required": True},
        {"name": "tool_failure", "target": "tool_trace", "label_invariant_required": True},
    ]
    return {
        "robustness_version": ROBUST_VERSION,
        "status": "BLOCKED_NO_MAIN_RUN",
        "transformations": transformations,
        "label_change_is_not_robustness_evidence": True,
        "runs": [],
        "transformation_manifest": transformations,
        "performance_slices": [],
        "failure_slices": [],
        "cost_slices": [],
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def assess_robustness(main_run: Mapping[str, Any]) -> dict[str, Any]:
    result = build_robustness_manifest()
    blockers: list[str] = []
    if main_run.get("status") != "READY_TO_RUN":
        blockers.append("main_run_not_ready")
    if not main_run.get("run_index"):
        blockers.append("main_run_index_empty")
    result["blockers"] = blockers
    result["status"] = "READY_TO_RUN" if not blockers else "BLOCKED_NO_MAIN_RUN"
    return result


def write_robustness_decision(main_run_path: Path, output_path: Path) -> dict[str, Any]:
    main_run = json.loads(main_run_path.read_text(encoding="utf-8"))
    if not isinstance(main_run, Mapping):
        raise TypeError("main-run decision must be a JSON object")
    result = assess_robustness(main_run)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
