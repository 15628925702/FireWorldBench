"""Guarded assessment for the preregistered main matrix."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

MAIN_VERSION = "P5-MAIN-001"
ALLOWED_SPLITS = {"train_id", "dev_id", "test_id", "test_ood", "external_test"}


def assess_main_run(
    prereg_path: Path,
    *,
    calibration_path: Path | None = None,
    input_manifest_path: Path | None = None,
) -> dict[str, Any]:
    prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
    if not isinstance(prereg, Mapping):
        raise TypeError("preregistration must be a JSON object")
    blockers: list[str] = []
    if prereg.get("status") != "READY_TO_RUN":
        blockers.append("preregistration_not_ready")
    model_matrix = prereg.get("model_matrix", [])
    if not any(isinstance(slot, Mapping) and slot.get("model_id") for slot in model_matrix):
        blockers.append("approved_model_matrix_missing")
    if calibration_path is None:
        blockers.append("calibration_gate_missing")
    else:
        calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
        if not isinstance(calibration, Mapping) or calibration.get("status") != "READY_TO_CALIBRATE":
            blockers.append("calibration_not_ready")
    input_count = 0
    if input_manifest_path is None:
        blockers.append("paper_ready_input_manifest_missing")
    else:
        payload = json.loads(input_manifest_path.read_text(encoding="utf-8"))
        samples = payload.get("samples", payload) if isinstance(payload, Mapping) else payload
        if not isinstance(samples, list):
            raise TypeError("main input manifest must be a JSON list or an object with a samples list")
        input_count = len(samples)
        if any(isinstance(sample, Mapping) and sample.get("split") not in ALLOWED_SPLITS for sample in samples):
            raise ValueError("main input contains an unknown split")
    blockers.append("approved_main_runtime_missing")
    return {
        "main_version": MAIN_VERSION,
        "status": "READY_TO_RUN" if not blockers else "BLOCKED",
        "blockers": blockers,
        "input_count": input_count,
        "run_index": [],
        "run_directories": [],
        "raw_response_manifests": [],
        "failure_report": [],
        "cost_report": None,
        "overwrite_existing_runs": False,
        "runner_reads_gold": False,
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def write_main_run_decision(
    output_path: Path,
    prereg_path: Path,
    *,
    calibration_path: Path | None = None,
    input_manifest_path: Path | None = None,
) -> dict[str, Any]:
    result = assess_main_run(prereg_path, calibration_path=calibration_path, input_manifest_path=input_manifest_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
