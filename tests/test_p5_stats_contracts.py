from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.stats import assess_statistics, write_statistics_decision


def test_stats_are_blocked_without_raw_predictions() -> None:
    result = assess_statistics()

    assert result["status"] == "BLOCKED_NO_RAW_OUTPUT"
    assert "raw_predictions_missing" in result["blockers"]
    assert result["sample_scores"] == []
    assert result["case_scores"] == []
    assert result["pair_scores"] == []
    assert result["confidence_intervals"] == {}
    assert result["manual_metric_edit"] is False
    assert result["recompute_from_raw_required"] is True


def test_empty_raw_predictions_are_not_zero_metrics(tmp_path: Path) -> None:
    raw = tmp_path / "raw.json"
    raw.write_text('{"predictions": []}\n', encoding="utf-8")
    result = assess_statistics(raw)

    assert result["status"] == "BLOCKED_NO_RAW_OUTPUT"
    assert "raw_predictions_empty" in result["blockers"]
    assert result["primary_metrics"] == {}


def test_stats_decision_file_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "stats.json"
    result = write_statistics_decision(output)
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
