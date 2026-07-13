from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.calibration import assess_calibration, write_calibration_decision


def test_calibration_is_blocked_without_paper_ready_inputs_and_model() -> None:
    result = assess_calibration()

    assert result["status"] == "BLOCKED"
    assert "paper_ready_train_dev_manifest_missing" in result["blockers"]
    assert "approved_model_config_missing" in result["blockers"]
    assert result["calibration_results"] == []
    assert result["model_set"] == []
    assert result["test_access_ledger"] == "NO_ACCESS_CONFIRMED"
    assert result["test_asset_read"] is False


def test_train_dev_manifest_without_approved_model_stays_blocked(tmp_path: Path) -> None:
    samples = tmp_path / "samples.json"
    samples.write_text('{"samples": [{"sample_id": "tr-1", "split": "train_id"}, {"sample_id": "dv-1", "split": "dev_id"}]}\n', encoding="utf-8")
    result = assess_calibration(samples_path=samples)

    assert result["train_count"] == 1
    assert result["dev_count"] == 1
    assert "approved_model_config_missing" in result["blockers"]


def test_calibration_refuses_test_sample_manifest(tmp_path: Path) -> None:
    samples = tmp_path / "samples.json"
    samples.write_text('{"samples": [{"sample_id": "te-1", "split": "test_id"}]}\n', encoding="utf-8")
    try:
        assess_calibration(samples_path=samples)
    except ValueError as exc:
        assert "train_id" in str(exc)
    else:
        raise AssertionError("test split must be refused")


def test_calibration_decision_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "calibration.json"
    result = write_calibration_decision(output)
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
