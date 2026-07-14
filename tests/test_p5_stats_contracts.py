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


def test_planning_statistics_scores_local_samples_without_opening_formal_gate(tmp_path: Path) -> None:
    sample = {
        "schema_version": "2.0", "sample_id": "FWB-v1-T1-A-case_1-x", "benchmark_version": "planning", "task": "T1-A", "split": "dev_id",
        "scenario": {"case_uid": "case_1", "domain": "fire_physics", "family_uid": "family_1", "intervention": None},
        "observations": [{"observation_id": "obs_1", "modality": "sensor_table", "time_range_s": [0, 1], "content_ref": "fixture", "units": {"time": "s"}, "quality": "valid"}],
        "question": {"format": "structured_json", "prompt": "fixture"}, "answer": {"label": "fire_forming"},
        "physical_trace": {"initial_state": {}, "mechanism_chain": [], "transitions": [], "outcome": {}, "evidence_links": ["obs_1"], "origin": ["deterministic_rule"]},
        "scoring_metadata": {"visibility": "private", "gold_ref": "gold_1", "metric_profile": "T1-A"},
        "provenance": {"source_id": "D01", "source_version": "fixture", "parent_manifest_sha256": "a" * 64, "builder_version": "fixture", "config_sha256": "b" * 64, "annotation_status": "automatic"},
    }
    prediction = {"schema_version": "2.0", "sample_id": sample["sample_id"], "task": "T1-A", "answer": {"label": "fire_forming"}, "evidence": ["obs_1"], "uncertainty": {"level": "low", "reason": "fixture"}, "missing_information": []}
    samples_path = tmp_path / "samples.json"
    predictions_path = tmp_path / "predictions.json"
    samples_path.write_text(json.dumps({"samples": [sample]}), encoding="utf-8-sig")
    predictions_path.write_text(json.dumps({"predictions": [prediction]}), encoding="utf-8-sig")

    result = assess_statistics(predictions_path, samples_path=samples_path, planning_mode=True)

    assert result["status"] == "COMPLETED_LOCAL_PLANNING_SMOKE_TEST"
    assert result["formal_benchmark_eligible"] is False
    assert result["primary_metrics"]["T1-A"]["primary_metric"] == 1.0
