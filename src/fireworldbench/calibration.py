"""Final train/dev calibration readiness gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

CALIBRATION_VERSION = "P5-FINAL-CALIBRATION-001"
ALLOWED_SPLITS = {"train_id", "dev_id"}
PROTECTED_PARTS = {"test", "test_gold", "test_input", "private", "gold"}


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _assert_safe_path(path: Path) -> None:
    blocked = sorted({part.casefold() for part in path.parts} & PROTECTED_PARTS)
    if blocked:
        raise PermissionError(f"calibration refuses protected path component(s): {blocked}")


def assess_calibration(
    *,
    samples_path: Path | None = None,
    model_config_path: Path | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    train_count = 0
    dev_count = 0
    samples_sha256: str | None = None
    if samples_path is None:
        blockers.append("paper_ready_train_dev_manifest_missing")
    else:
        _assert_safe_path(samples_path)
        sample_bytes = samples_path.read_bytes()
        samples_sha256 = _hash(sample_bytes.decode("utf-8"))
        payload = json.loads(sample_bytes.decode("utf-8"))
        samples = payload.get("samples", payload) if isinstance(payload, Mapping) else payload
        if not isinstance(samples, list):
            raise TypeError("calibration samples must be a JSON list or an object with a samples list")
        if any(sample.get("split") not in ALLOWED_SPLITS for sample in samples if isinstance(sample, Mapping)):
            raise ValueError("calibration only permits train_id or dev_id")
        train_count = sum(1 for sample in samples if isinstance(sample, Mapping) and sample.get("split") == "train_id")
        dev_count = sum(1 for sample in samples if isinstance(sample, Mapping) and sample.get("split") == "dev_id")
        if train_count == 0 or dev_count == 0:
            blockers.append("train_and_dev_both_required")
    approved_model_ids: list[str] = []
    model_config_sha256: str | None = None
    if model_config_path is None:
        blockers.append("approved_model_config_missing")
    else:
        _assert_safe_path(model_config_path)
        model_bytes = model_config_path.read_bytes()
        model_config_sha256 = _hash(model_bytes.decode("utf-8"))
        config = json.loads(model_bytes.decode("utf-8"))
        default_config = config.get("default_config", {}) if isinstance(config, Mapping) else {}
        if isinstance(default_config, Mapping) and default_config.get("approved") is True and default_config.get("model_id"):
            approved_model_ids.append(str(default_config["model_id"]))
        else:
            blockers.append("approved_model_id_missing")
    blockers.append("approved_calibration_runtime_missing")
    return {
        "calibration_version": CALIBRATION_VERSION,
        "status": "READY_TO_CALIBRATE" if not blockers else "BLOCKED",
        "blockers": blockers,
        "train_count": train_count,
        "dev_count": dev_count,
        "samples_sha256": samples_sha256,
        "model_config_sha256": model_config_sha256,
        "model_set": approved_model_ids,
        "checkpoint_manifest": [],
        "prompt_hashes": [],
        "calibration_results": [],
        "selection_log": [],
        "sealed_run_plan_input": {"source": "P4-PILOT-FREEZE-001", "test_selection": False, "model_set_change": False},
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_tuning": False,
        "test_asset_read": False,
    }


def write_calibration_decision(output_path: Path, *, samples_path: Path | None = None, model_config_path: Path | None = None) -> dict[str, Any]:
    result = assess_calibration(samples_path=samples_path, model_config_path=model_config_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
