"""Schema and cross-field validation for P2-SCHEMA-001."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

TASK_LABELS: dict[str, set[str]] = {
    "T1-A": {"fire_forming", "not_fire_forming", "insufficient_information"},
    "T1-B": {"fire", "non_fire", "ventilation_disturbance", "sensor_fault", "insufficient_information"},
    "T1-C": {"query_observation", "stop_and_decide", "insufficient_information"},
    "T2-A": {"baseline_or_no_fire", "forming_or_early", "growth", "developed_or_peak", "decay_or_ventilation_change", "state_unknown"},
    "T2-B": {"buoyant_plume", "ceiling_jet", "longitudinal_ventilation", "sidewall_extraction", "backlayering", "smoke_layer_formation", "sensor_artifact", "multiple_mechanisms", "mechanism_unknown"},
    "T2-C": {"consistent", "inconsistent", "underdetermined"},
    "T3-A": {"increase", "decrease", "stable", "mixed_or_non_monotonic", "trend_unknown"},
    "T3-B": {"case_a_higher_risk", "case_b_higher_risk", "no_material_difference", "pair_invalid", "underdetermined"},
    "T3-C": {"trace_supported", "trace_partially_supported", "trace_unknown"},
}


def _schema_path(name: str) -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / name


def _load_validator(name: str) -> Draft202012Validator:
    schema = json.loads(_schema_path(name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _errors(validator: Draft202012Validator, value: dict[str, Any]) -> list[str]:
    return [f"{'.'.join(str(x) for x in error.absolute_path)}: {error.message}" for error in validator.iter_errors(value)]


def validate_sample(sample: dict[str, Any]) -> list[str]:
    errors = _errors(_load_validator("benchmark_sample.v2.schema.json"), sample)
    if errors:
        return errors
    task = sample["task"]
    label = sample["answer"].get("label")
    if label not in TASK_LABELS[task]:
        errors.append(f"answer.label is invalid for {task}: {label!r}")
    observation_ids = [item["observation_id"] for item in sample["observations"]]
    if len(observation_ids) != len(set(observation_ids)):
        errors.append("observations contain duplicate observation_id")
    if sample["physical_trace"]["evidence_links"]:
        missing = set(sample["physical_trace"]["evidence_links"]) - set(observation_ids)
        if missing:
            errors.append(f"physical_trace references unknown observations: {sorted(missing)}")
    for observation in sample["observations"]:
        if any(not unit.strip() or unit.upper() == "UNKNOWN" for unit in observation["units"].values()):
            errors.append(f"unknown/empty unit in {observation['observation_id']}")
    if task == "T3-B" and label not in {"pair_invalid", "underdetermined"}:
        intervention = sample["scenario"].get("intervention")
        if not isinstance(intervention, dict) or intervention.get("single_variable") is not True:
            errors.append("T3-B causal label requires scenario.intervention.single_variable=true")
    return errors


def validate_prediction(prediction: dict[str, Any], sample: dict[str, Any] | None = None) -> list[str]:
    errors = _errors(_load_validator("prediction.v2.schema.json"), prediction)
    forbidden = {"gold", "gold_ref", "physical_trace", "scoring_metadata", "provenance"}
    leaked = forbidden.intersection(prediction)
    if leaked:
        errors.append(f"prediction contains private fields: {sorted(leaked)}")
    if sample is not None:
        if prediction.get("sample_id") != sample.get("sample_id"):
            errors.append("prediction.sample_id does not match sample.sample_id")
        if prediction.get("task") != sample.get("task"):
            errors.append("prediction.task does not match sample.task")
        known = {item["observation_id"] for item in sample.get("observations", [])}
        unknown = set(prediction.get("evidence", [])) - known
        if unknown:
            errors.append(f"prediction references unknown observations: {sorted(unknown)}")
    return errors
