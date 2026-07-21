from __future__ import annotations

from fireworld.contracts import TASKS
from fireworld.prediction_contracts import (
    load_prediction_contract,
    prediction_contract_sha256,
    prompt_contract,
    response_json_schema,
)
from fireworld.validation import validate_prediction_semantics, validate_schema


def prediction(task_id: str, fields: dict, choice=None) -> dict:
    return {
        "schema_version": "2.0.0",
        "qa_id": "FWQ-AAAAAAAAAAAA",
        "task_id": task_id,
        "answer": {"choice": choice, "fields": fields},
        "confidence": 0.5,
        "evidence": [],
    }


def test_contract_covers_all_tasks_and_matches_active_fields() -> None:
    contract = load_prediction_contract()
    assert set(contract["tasks"]) == set(TASKS)
    assert len(prediction_contract_sha256()) == 64
    for task_id, task in TASKS.items():
        assert tuple(contract["tasks"][task_id]["answer_fields"]) == task.answer_fields


def test_prompt_contract_contains_enums_and_exact_keys() -> None:
    contract = prompt_contract("L2-1")
    assert contract["model_response_keys"] == [
        "choice", "fields", "confidence", "evidence"
    ]
    assert contract["answer_fields"]["stage"] == [
        "incipient", "growth", "developed", "decay"
    ]
    assert contract["forbidden_extra_fields"] is True


def test_semantics_reject_alias_extra_and_invalid_enum() -> None:
    alias = prediction(
        "L1-3",
        {"temporal_consistency": "consistent", "violation_type": None},
    )
    errors = validate_prediction_semantics(alias)
    assert any("unexpected fields: temporal_consistency" in error for error in errors)
    assert any("missing answer fields: consistency" in error for error in errors)

    invalid = prediction("L3-1", {
        "temperature_trend": "increasing",
        "smoke_trend": "stable",
        "visibility_trend": "down",
    })
    assert validate_prediction_semantics(invalid) == [
        "L3-1 prediction has invalid temperature_trend: 'increasing'"
    ]


def test_l12_choice_and_l13_conditional_are_fail_closed() -> None:
    mismatch = prediction("L1-2", {"choice": "B"}, choice="A")
    assert validate_prediction_semantics(mismatch) == [
        "L1-2 prediction requires fields.choice == answer.choice"
    ]
    invalid_consistency = prediction(
        "L1-3", {"consistency": "consistent", "violation_type": "jump"}
    )
    assert validate_prediction_semantics(invalid_consistency) == [
        "consistent L1-3 predictions require violation_type=null"
    ]


def test_complete_prediction_passes_schema_and_semantics() -> None:
    item = prediction("L2-2", {"risk_region": "R4", "risk_level": "high"})
    assert validate_schema(item, "prediction.v2.schema.json") == []
    assert validate_prediction_semantics(item) == []

def test_response_schema_is_strict_and_task_specific() -> None:
    schema = response_json_schema("L3-2")
    assert schema["additionalProperties"] is False
    assert schema["properties"]["fields"]["additionalProperties"] is False
    assert schema["properties"]["fields"]["required"] == ["first_high_risk_region"]
    assert schema["properties"]["fields"]["properties"]["first_high_risk_region"]["enum"][-1] == "none"
