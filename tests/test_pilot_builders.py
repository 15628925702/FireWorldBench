from __future__ import annotations

import json
from pathlib import Path

import pytest

from fireworld.task_builders.pilot import BUILDERS, build_l2_1
from fireworld.validation import validate_qa_semantics, validate_schema

FIXTURE = Path(__file__).parent / "fixtures" / "v2" / "minimal_fire_event.json"


def event() -> dict[str, object]:
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    value["status"] = "eligible"
    value["observations"]["images"] = [
        {"ref": "events/opaque/frame.png", "time_s": 10, "sha256": "a" * 64}
    ]
    value["ground_truth"]["labels"] = [
        {
            "name": "class",
            "value": "fire",
            "origin": "simulation_truth",
            "rule_version": "l1-1-0.1",
        },
        {
            "name": "source_region",
            "value": "R1",
            "origin": "simulation_truth",
            "rule_version": "stage-0.1",
        },
        {
            "name": "stage",
            "value": "growth",
            "origin": "deterministic_rule",
            "rule_version": "stage-0.1",
        },
        {
            "name": "comparison",
            "value": "A",
            "origin": "deterministic_rule",
            "rule_version": "cf-0.1",
        },
        {
            "name": "choice",
            "value": "B",
            "origin": "deterministic_rule",
            "rule_version": "l1-2-0.1",
        },
        {
            "name": "consistency",
            "value": "consistent",
            "origin": "deterministic_rule",
            "rule_version": "l1-3-0.1",
        },
        {
            "name": "violation_type",
            "value": None,
            "origin": "deterministic_rule",
            "rule_version": "l1-3-0.1",
        },
        {
            "name": "risk_region",
            "value": "R2",
            "origin": "deterministic_rule",
            "rule_version": "l2-2-0.1",
        },
        {
            "name": "risk_level",
            "value": "high",
            "origin": "deterministic_rule",
            "rule_version": "l2-2-0.1",
        },
        {
            "name": "mechanism",
            "value": "buoyant_plume",
            "origin": "deterministic_rule",
            "rule_version": "l2-3-0.1",
        },
        {
            "name": "temperature_trend",
            "value": "up",
            "origin": "deterministic_rule",
            "rule_version": "l3-1-0.1",
        },
        {
            "name": "smoke_trend",
            "value": "up",
            "origin": "deterministic_rule",
            "rule_version": "l3-1-0.1",
        },
        {
            "name": "visibility_trend",
            "value": "down",
            "origin": "deterministic_rule",
            "rule_version": "l3-1-0.1",
        },
        {
            "name": "first_high_risk_region",
            "value": "R2",
            "origin": "deterministic_rule",
            "rule_version": "l3-2-0.1",
        },
    ]
    value["controls"]["intervention"] = {
        "variable": "hrrpua",
        "value": 250.0,
        "base_event_id": "FWE-000000000001",
    }
    return value


@pytest.mark.parametrize(
    "builder,task", [(builder, task) for task, builder in sorted(BUILDERS.items())]
)
def test_pilot_builder_contract(builder, task: str) -> None:
    qa = builder(event())
    assert validate_schema(qa, "qa.schema.json") == []
    assert validate_qa_semantics(qa) == []
    assert qa["task_id"] == task


def test_builder_refuses_missing_fds_provenance() -> None:
    value = event()
    value["provenance"]["fds"] = None
    with pytest.raises(ValueError, match="FDS provenance"):
        build_l2_1(value)
