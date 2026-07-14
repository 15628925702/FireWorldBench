"""Raw-prediction statistics readiness gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from fireworldbench.scorer import score_samples

STATS_VERSION = "P5-STATS-001"


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _load_items(path: Path, field: str) -> list[Mapping[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    value = payload.get(field, payload) if isinstance(payload, dict) else payload
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        raise TypeError(f"{field} must be a JSON list or object with a {field} list")
    return list(value)


def assess_statistics(
    raw_predictions_path: Path | None = None,
    *,
    samples_path: Path | None = None,
    planning_mode: bool = False,
) -> dict[str, Any]:
    blockers: list[str] = []
    raw_sha256: str | None = None
    sample_count = 0
    if raw_predictions_path is None:
        blockers.append("raw_predictions_missing")
    else:
        raw_bytes = raw_predictions_path.read_bytes()
        raw_sha256 = _hash(raw_bytes.decode("utf-8"))
        predictions = _load_items(raw_predictions_path, "predictions")
        sample_count = len(predictions)
        if sample_count == 0:
            blockers.append("raw_predictions_empty")
    scored: dict[str, Any] | None = None
    if planning_mode:
        if samples_path is None:
            blockers.append("planning_samples_missing")
        elif raw_predictions_path is not None:
            samples = _load_items(samples_path, "samples")
            prediction_map = {str(item["sample_id"]): item for item in predictions}
            scored = score_samples(samples, prediction_map)
    else:
        blockers.append("main_run_not_ready")
    status = "COMPLETED_LOCAL_PLANNING_SMOKE_TEST" if planning_mode and not blockers else ("READY_TO_SCORE" if not blockers else "BLOCKED_NO_RAW_OUTPUT")
    return {
        "stats_version": STATS_VERSION,
        "status": status,
        "blockers": blockers,
        "raw_predictions_sha256": raw_sha256,
        "sample_count": sample_count,
        "planning_mode": planning_mode,
        "formal_benchmark_eligible": False if planning_mode else None,
        "sample_scores": [] if scored is None else scored["sample_scores"],
        "case_scores": [] if scored is None else scored["case_aggregates"],
        "pair_scores": [] if scored is None else scored["pair_aggregates"],
        "primary_metrics": {} if scored is None else scored["task_metrics"],
        "confidence_intervals": {},
        "effect_sizes": {},
        "multiple_comparison_report": None,
        "cost_report": None,
        "failure_report": [] if scored is None else scored["failure_counts"],
        "manual_metric_edit": False,
        "recompute_from_raw_required": True,
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def write_statistics_decision(
    output_path: Path,
    raw_predictions_path: Path | None = None,
    *,
    samples_path: Path | None = None,
    planning_mode: bool = False,
) -> dict[str, Any]:
    result = assess_statistics(raw_predictions_path, samples_path=samples_path, planning_mode=planning_mode)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
