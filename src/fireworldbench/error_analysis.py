"""Blind error-analysis contract with a no-input gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from fireworldbench.scorer import score_samples

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


def _items(path: Path, field: str) -> list[Mapping[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    value = payload.get(field, payload) if isinstance(payload, Mapping) else payload
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        raise TypeError(f"{field} must be a JSON list or object with a {field} list")
    return list(value)


def _taxonomy(task: str, missing: bool) -> str:
    if missing:
        return "format"
    return {
        "T1-C": "uncertainty",
        "T2-A": "state",
        "T2-B": "mechanism",
        "T2-C": "physical",
        "T3-A": "temporal",
        "T3-B": "causal",
        "T3-C": "causal",
    }.get(task, "perception")


def assess_error_analysis(
    raw_predictions_path: Path | None = None,
    *,
    samples_path: Path | None = None,
    planning_mode: bool = False,
) -> dict[str, Any]:
    result = build_error_plan()
    blockers: list[str] = []
    if raw_predictions_path is None:
        blockers.append("raw_predictions_missing")
    else:
        predictions = _items(raw_predictions_path, "predictions")
        if not predictions:
            blockers.append("raw_predictions_empty")
    result["blockers"] = blockers
    if planning_mode and samples_path is None:
        blockers.append("planning_samples_missing")
    if planning_mode and not blockers and raw_predictions_path is not None and samples_path is not None:
        samples = _items(samples_path, "samples")
        prediction_map = {str(item["sample_id"]): item for item in predictions}
        scored = score_samples(samples, prediction_map)
        labels = []
        for item in scored["sample_scores"]:
            if item["primary_score"] == 1.0:
                continue
            missing = item["status"] == "missing_prediction"
            labels.append({
                "sample_id": item["sample_id"],
                "task": item["task"],
                "taxonomy": _taxonomy(str(item["task"]), missing),
                "status": item["status"],
                "review_status": "AUTOMATIC_PRELIMINARY_REQUIRES_TWO_RATERS",
            })
        result.update({
            "status": "COMPLETED_LOCAL_PLANNING_SMOKE_TEST",
            "planning_mode": True,
            "formal_benchmark_eligible": False,
            "error_labels": labels,
            "sampling_list": [item["sample_id"] for item in scored["sample_scores"]],
            "failure_summary": scored["failure_counts"],
        })
    else:
        result["status"] = "READY_TO_ANALYZE" if not blockers else "BLOCKED_NO_RAW_OUTPUT"
    return result


def write_error_decision(
    output_path: Path,
    raw_predictions_path: Path | None = None,
    *,
    samples_path: Path | None = None,
    planning_mode: bool = False,
) -> dict[str, Any]:
    result = assess_error_analysis(raw_predictions_path, samples_path=samples_path, planning_mode=planning_mode)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
