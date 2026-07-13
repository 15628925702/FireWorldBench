from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.main_run import assess_main_run, write_main_run_decision


def prereg(tmp_path: Path) -> Path:
    path = tmp_path / "prereg.json"
    path.write_text('{"status": "BLOCKED_PENDING_APPROVAL", "model_matrix": []}\n', encoding="utf-8")
    return path


def test_main_matrix_is_blocked_without_prereg_model_input_and_runtime(tmp_path: Path) -> None:
    result = assess_main_run(prereg(tmp_path))

    assert result["status"] == "BLOCKED"
    assert "preregistration_not_ready" in result["blockers"]
    assert "approved_model_matrix_missing" in result["blockers"]
    assert "paper_ready_input_manifest_missing" in result["blockers"]
    assert result["run_index"] == []
    assert result["cost_report"] is None
    assert result["runner_reads_gold"] is False
    assert result["test_access_ledger"] == "NO_ACCESS_CONFIRMED"


def test_main_run_accepts_only_known_split_names(tmp_path: Path) -> None:
    inputs = tmp_path / "inputs.json"
    inputs.write_text('{"samples": [{"sample_id": "x", "split": "unknown"}]}\n', encoding="utf-8")
    try:
        assess_main_run(prereg(tmp_path), input_manifest_path=inputs)
    except ValueError as exc:
        assert "unknown split" in str(exc)
    else:
        raise AssertionError("unknown split must be refused")


def test_main_decision_file_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "main.json"
    result = write_main_run_decision(output, prereg(tmp_path))
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
