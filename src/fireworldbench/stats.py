"""Raw-prediction statistics readiness gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

STATS_VERSION = "P5-STATS-001"


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def assess_statistics(raw_predictions_path: Path | None = None) -> dict[str, Any]:
    blockers: list[str] = []
    raw_sha256: str | None = None
    sample_count = 0
    if raw_predictions_path is None:
        blockers.append("raw_predictions_missing")
    else:
        raw_bytes = raw_predictions_path.read_bytes()
        raw_sha256 = _hash(raw_bytes.decode("utf-8"))
        payload = json.loads(raw_bytes.decode("utf-8"))
        predictions = payload.get("predictions", payload) if isinstance(payload, dict) else payload
        if not isinstance(predictions, list):
            raise TypeError("raw predictions must be a JSON list or an object with a predictions list")
        sample_count = len(predictions)
        if sample_count == 0:
            blockers.append("raw_predictions_empty")
    blockers.append("main_run_not_ready")
    return {
        "stats_version": STATS_VERSION,
        "status": "READY_TO_SCORE" if not blockers else "BLOCKED_NO_RAW_OUTPUT",
        "blockers": blockers,
        "raw_predictions_sha256": raw_sha256,
        "sample_count": sample_count,
        "sample_scores": [],
        "case_scores": [],
        "pair_scores": [],
        "primary_metrics": {},
        "confidence_intervals": {},
        "effect_sizes": {},
        "multiple_comparison_report": None,
        "cost_report": None,
        "failure_report": [],
        "manual_metric_edit": False,
        "recompute_from_raw_required": True,
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def write_statistics_decision(output_path: Path, raw_predictions_path: Path | None = None) -> dict[str, Any]:
    result = assess_statistics(raw_predictions_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
