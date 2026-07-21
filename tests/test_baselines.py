from __future__ import annotations

from fireworld.run_baselines import chance, majorities, predict
from fireworld.validation import validate_prediction_semantics, validate_schema


def qa(task_id: str = "L1-3") -> dict:
    return {
        "qa_id": "FWQ-AAAAAAAAAAAA",
        "task_id": task_id,
        "track": "S",
        "answer": {"choice": None, "fields": {}},
    }


def test_seeded_chance_is_strict_and_conditional() -> None:
    row = chance(qa(), 20260720)
    assert validate_schema(row, "prediction.v2.schema.json") == []
    assert validate_prediction_semantics(row) == []


def test_majority_uses_train_answer_not_test_label() -> None:
    train = [
        {**qa("L1-1"), "answer": {"choice": None, "fields": {"class": "fire"}}},
        {**qa("L1-1"), "answer": {"choice": None, "fields": {"class": "fire"}}},
        {**qa("L1-1"), "answer": {"choice": None, "fields": {"class": "no_fire"}}},
    ]
    winner = majorities(train)[("S", "L1-1")]
    row = predict(qa("L1-1"), *winner)
    assert row["answer"]["fields"]["class"] == "fire"
    assert validate_prediction_semantics(row) == []