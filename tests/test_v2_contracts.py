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
