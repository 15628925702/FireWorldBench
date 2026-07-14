from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.error_analysis import TAXONOMY, assess_error_analysis, build_error_plan, write_error_decision


def test_error_analysis_is_blocked_without_raw_and_keeps_negative_result_policy() -> None:
    result = assess_error_analysis()

    assert result["status"] == "BLOCKED_NO_RAW_OUTPUT"
    assert result["taxonomy"] == TAXONOMY
    assert result["error_labels"] == []
    assert result["sampling_list"] == []
    assert result["adjudication"]["representative_case_index"] == []
    assert result["negative_results_retained"] is True
    assert result["sampling"]["model_identity_visible"] is False


def test_error_plan_is_deterministic_and_posthoc_selection_is_forbidden() -> None:
    plan = build_error_plan()
    assert plan == build_error_plan()
    assert plan["sampling"]["posthoc_case_selection"] is False
    assert plan["adjudication"]["rater_count"] == 2


def test_error_decision_file_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "errors.json"
    result = write_error_decision(output)
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]


def test_planning_error_analysis_labels_mismatch_and_missing_prediction(tmp_path: Path) -> None:
    sample = {
        "schema_version": "2.0", "sample_id": "FWB-v1-T2-A-case_1-x", "benchmark_version": "planning", "task": "T2-A", "split": "dev_id",
        "scenario": {"case_uid": "case_1", "domain": "fire_physics", "family_uid": "family_1", "intervention": None},
        "observations": [{"observation_id": "obs_1", "modality": "sensor_table", "time_range_s": [0, 1], "content_ref": "fixture", "units": {"time": "s"}, "quality": "valid"}],
        "question": {"format": "structured_json", "prompt": "fixture"}, "answer": {"label": "growth"},
        "physical_trace": {"initial_state": {}, "mechanism_chain": [], "transitions": [], "outcome": {}, "evidence_links": ["obs_1"], "origin": ["deterministic_rule"]},
        "scoring_metadata": {"visibility": "private", "gold_ref": "gold_1", "metric_profile": "T2-A"},
        "provenance": {"source_id": "D01", "source_version": "fixture", "parent_manifest_sha256": "a" * 64, "builder_version": "fixture", "config_sha256": "b" * 64, "annotation_status": "automatic"},
    }
    prediction = {"schema_version": "2.0", "sample_id": sample["sample_id"], "task": "T2-A", "answer": {"label": "developed_or_peak"}, "evidence": ["obs_1"], "uncertainty": {"level": "low", "reason": "fixture"}, "missing_information": []}
    samples_path = tmp_path / "samples.json"
    predictions_path = tmp_path / "predictions.json"
    samples_path.write_text(json.dumps({"samples": [sample]}), encoding="utf-8")
    predictions_path.write_text(json.dumps({"predictions": [prediction]}), encoding="utf-8")

    result = assess_error_analysis(predictions_path, samples_path=samples_path, planning_mode=True)

    assert result["status"] == "COMPLETED_LOCAL_PLANNING_SMOKE_TEST"
    assert result["error_labels"][0]["taxonomy"] == "state"
