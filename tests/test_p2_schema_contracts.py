from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.schema_validation import validate_prediction, validate_sample


FIXTURES = Path(__file__).parent / "fixtures" / "p2_schema"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_sample_and_prediction() -> None:
    sample = load("valid_sample.json")
    prediction = load("valid_prediction.json")
    assert validate_sample(sample) == []
    assert validate_prediction(prediction, sample) == []


def test_private_gold_and_unknown_evidence_are_rejected() -> None:
    sample = load("valid_sample.json")
    prediction = load("invalid_prediction_private_gold.json")
    errors = validate_prediction(prediction, sample)
    assert any("private fields" in error for error in errors)
    assert any("unknown observations" in error for error in errors)


def test_invalid_pair_and_unit_are_rejected() -> None:
    sample = load("invalid_sample_pair_unit.json")
    errors = validate_sample(sample)
    assert any("unknown/empty unit" in error for error in errors)
    assert any("single_variable" in error for error in errors)


def test_boundary_refusal_is_valid() -> None:
    sample = load("boundary_refusal_sample.json")
    assert validate_sample(sample) == []
