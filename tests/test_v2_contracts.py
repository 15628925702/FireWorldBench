from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from fireworld.scoring import aggregate_scores, score_one
from fireworld.validation import (
    validate_event_groups,
    validate_event_semantics,
    validate_qa_semantics,
    validate_schema,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "v2"


def load(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_minimal_fire_event_passes_schema_and_semantics() -> None:
    event = load("minimal_fire_event.json")
    assert validate_schema(event, "fire_event.schema.json") == []
    assert validate_event_semantics(event) == []


def test_event_requires_explicit_observation_keys() -> None:
    event = load("minimal_fire_event.json")
    del event["observations"]["images"]  # type: ignore[index]
    errors = validate_schema(event, "fire_event.schema.json")
    assert any("images" in error and "required" in error for error in errors)


def test_fds_event_requires_fds_provenance() -> None:
    event = load("minimal_fire_event.json")
    event["provenance"]["fds"] = None  # type: ignore[index]
    assert "FDS events require provenance.fds" in validate_event_semantics(event)


def test_minimal_qa_passes_schema_and_semantics() -> None:
    qa = load("minimal_qa.json")
    assert validate_schema(qa, "qa.schema.json") == []
    assert validate_qa_semantics(qa) == []


def test_task_layer_metric_and_track_are_cross_validated() -> None:
    qa = load("minimal_qa.json")
    qa["layer"] = "L1"
    qa["scoring"]["primary"] = "accuracy"  # type: ignore[index]
    qa["track"] = "I"
    errors = validate_qa_semantics(qa)
    assert "L2-1 requires layer L2" in errors
    assert "L2-1 requires primary metric component_accuracy" in errors
    assert "track I requires observation.images" in errors
    assert "track I requires unused observation.structured=null" in errors


def test_source_role_matrix_blocks_fabricated_tasks() -> None:
    qa = load("minimal_qa.json")
    qa["source_domain"] = "dfire"
    qa["track"] = "I"
    qa["observation"]["structured"] = None  # type: ignore[index]
    qa["observation"]["images"] = ["media/frame.jpg"]  # type: ignore[index]
    errors = validate_qa_semantics(qa)
    assert "source dfire is not eligible for task L2-1" in errors


def test_fixed_answer_space_is_enforced() -> None:
    qa = load("minimal_qa.json")
    qa["answer"]["fields"]["stage"] = "flashover-ish"  # type: ignore[index]
    assert "L2-1 has invalid stage: 'flashover-ish'" in validate_qa_semantics(qa)


def test_l1_2_requires_four_options_and_choice() -> None:
    qa = load("minimal_qa.json")
    qa["layer"] = "L1"
    qa["task_id"] = "L1-2"
    qa["scoring"] = {"primary": "accuracy", "components": [], "secondary": []}
    qa["answer"] = {"choice": "A", "fields": {"choice": "A"}}
    qa["options"] = [
        {"id": "A", "content_ref": None, "text": "candidate A"},
        {"id": "B", "content_ref": None, "text": "candidate B"},
    ]
    assert "L1-2 requires exactly four options" in validate_qa_semantics(qa)


def test_event_group_cannot_cross_splits() -> None:
    first = load("minimal_qa.json")
    second = deepcopy(first)
    second["qa_id"] = "FWQ-000000000002"
    second["split"] = "test_iid"
    errors = validate_event_groups([first, second])
    assert errors == ["event_group FWG-000000000001 crosses splits: ['test_iid', 'train']"]


def test_component_accuracy_and_incomplete_overall() -> None:
    qa = load("minimal_qa.json")
    prediction = {"qa_id": qa["qa_id"], "fields": {"source_region": "R1", "stage": "decay"}}
    assert score_one(qa, prediction) == 0.5
    report = aggregate_scores([qa], {str(qa["qa_id"]): prediction})
    assert report["task_scores"] == {"L2-1": 50.0}
    assert report["layer_scores"] == {"L2": 50.0}
    assert report["overall"] is None

def test_release_verifier_checks_accepted_fds_core_when_available() -> None:
    from fireworld.release_verify import verify_fds_core

    release = Path("/root/autodl-tmp/FireWorldBench/2/release/fireworldbench_fds_core_v3_3_1")
    if not release.is_dir():
        return
    result = verify_fds_core(release)
    assert result["ok"]
    assert result["events"] == 180
    assert result["qa_total"] == 4039
    assert result["files_checked"] > 8000

def test_coverage_matrix_keeps_external_sources_out_of_formal_support() -> None:
    from fireworld.coverage import coverage_matrix

    rows = coverage_matrix()
    assert len(rows) == 270
    assert sum(row["eligibility"] == "supported" for row in rows) == 27
    assert {
        row["eligibility"]
        for row in rows
        if row["source_domain"] == "furg_fire_substitute"
    } == {"candidate_substitute", "unsupported"}
    assert all(row["eligibility"] != "supported" for row in rows if row["source_domain"] != "fds")

def test_score_report_has_required_breakdowns() -> None:
    qa = load("minimal_qa.json")
    prediction = {"qa_id": qa["qa_id"], "fields": {"source_region": "R1", "stage": "growth"}}
    report = aggregate_scores([qa], {str(qa["qa_id"]): prediction})
    assert report["breakdowns"]["task_id"]["L2-1"]["n"] == 1
    assert report["breakdowns"]["layer"]["L2"]["task_scores"] == {"L2-1": 100.0}
    assert report["breakdowns"]["track"]["S"]["missing_predictions"] == 0
    assert report["breakdowns"]["source_domain"]["fds"]["n"] == 1
    assert report["breakdowns"]["split"]["train"]["n"] == 1


def test_prediction_semantics_rejects_missing_fields_and_task_mismatch() -> None:
    from fireworld.validation import validate_prediction_semantics

    qa = load("minimal_qa.json")
    prediction = {
        "qa_id": qa["qa_id"],
        "task_id": "L2-1",
        "answer": {"choice": None, "fields": {"source_region": "R1"}},
        "confidence": None,
        "evidence": [],
    }
    assert validate_prediction_semantics(prediction, qa) == [
        "L2-1 prediction missing answer fields: stage"
    ]
    prediction["task_id"] = "L2-2"
    assert "prediction task_id does not match gold task_id" in validate_prediction_semantics(
        prediction, qa
    )


def test_candidate_source_cannot_be_formal_qa() -> None:
    qa = load("minimal_qa.json")
    qa["source_domain"] = "immersed_tunnel"
    errors = validate_qa_semantics(qa)
    assert "source immersed_tunnel is not formally accepted for QA (state=candidate)" in errors

def test_external_domain_is_never_averaged_into_main_scores() -> None:
    qa = load("minimal_qa.json")
    qa["source_domain"] = "immersed_tunnel"
    qa["split"] = "external_cfd"
    prediction = {
        "qa_id": qa["qa_id"],
        "fields": {"source_region": "R1", "stage": "growth"},
    }
    report = aggregate_scores([qa], {str(qa["qa_id"]): prediction})
    assert report["task_scores"] == {}
    assert report["overall"] is None
    assert report["external"] == {
        "external_cfd": {
            "task_scores": {"L2-1": 100.0},
            "missing_predictions": 0,
        }
    }
