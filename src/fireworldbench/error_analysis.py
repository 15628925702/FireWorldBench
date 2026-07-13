"""Blind error-analysis contract with a no-input gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

ERROR_VERSION = "P5-ERROR-001"
TAXONOMY = ["perception", "state", "mechanism", "causal", "temporal", "physical", "uncertainty", "tool", "format"]


def build_error_plan() -> dict[str, Any]:
    return {
        "error_version": ERROR_VERSION,
        "status": "BLOCKED_NO_RAW_OUTPUT",
        "taxonomy": TAXONOMY,
        "sampling": {"method": "pre_registered_stratified_sample", "model_identity_visible": False, "posthoc_case_selection": False},
        "error_labels": [],
        "sampling_list": [],
        "adjudication": {"rater_count": 2, "consistency_required": True, "disagreement_queue": [], "representative_case_index": []},
        "negative_results_retained": True,
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def assess_error_analysis(raw_predictions_path: Path | None = None) -> dict[str, Any]:
    result = build_error_plan()
    blockers: list[str] = []
    if raw_predictions_path is None:
        blockers.append("raw_predictions_missing")
    else:
        payload = json.loads(raw_predictions_path.read_text(encoding="utf-8"))
        predictions = payload.get("predictions", payload) if isinstance(payload, Mapping) else payload
        if not isinstance(predictions, list) or not predictions:
            blockers.append("raw_predictions_empty")
    result["blockers"] = blockers
    result["status"] = "READY_TO_ANALYZE" if not blockers else "BLOCKED_NO_RAW_OUTPUT"
    return result


def write_error_decision(output_path: Path, raw_predictions_path: Path | None = None) -> dict[str, Any]:
    result = assess_error_analysis(raw_predictions_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
