"""Schema and semantic validation for FireWorldBench v2."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from fireworld.contracts import SOURCES, SOURCE_TASKS, SOURCE_TRACKS, TASKS, source_eligibility
from fireworld.prediction_contracts import prediction_contract


class DatasetValidationError(ValueError):
    """Raised when a v2 dataset violates a frozen contract."""


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_schema(instance: object, schema_name: str) -> list[str]:
    schema = load_json(project_root() / "schemas" / schema_name)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'.'.join(str(item) for item in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(
            validator.iter_errors(instance), key=lambda item: list(item.absolute_path)
        )
    ]


def validate_event_semantics(event: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    timeline = event.get("timeline", {})
    if timeline.get("end_s", 0) <= timeline.get("start_s", 0):
        errors.append("timeline.end_s must be greater than timeline.start_s")
    observations = event.get("observations", {})
    if all(observations.get(name) is None for name in ("structured", "images", "video")):
        errors.append("at least one observation modality must be present")
    if event.get("source_domain") == "fds" and event.get("provenance", {}).get("fds") is None:
        errors.append("FDS events require provenance.fds")
    if event.get("source_domain") != "fds" and event.get("provenance", {}).get("fds") is not None:
        errors.append("non-FDS events must set provenance.fds to null")
    images = observations.get("images") or []
    image_times = [image["time_s"] for image in images if "time_s" in image]
    if image_times != sorted(image_times):
        errors.append("image observations must be ordered by time_s")
    return errors


def validate_qa_semantics(qa: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    task_id_value = qa.get("task_id")
    if not isinstance(task_id_value, str):
        return ["task_id must be a string"]
    task_id = task_id_value
    contract = TASKS.get(task_id)
    if contract is None:
        return [f"unknown task_id: {task_id}"]
    if qa.get("layer") != contract.layer:
        errors.append(f"{task_id} requires layer {contract.layer}")
    if qa.get("scoring", {}).get("primary") != contract.primary:
        errors.append(f"{task_id} requires primary metric {contract.primary}")
    fields = qa.get("answer", {}).get("fields", {})
    missing_fields = [name for name in contract.answer_fields if name not in fields]
    if missing_fields:
        errors.append(f"{task_id} missing answer fields: {', '.join(missing_fields)}")

    allowed_values: dict[str, set[str]] = {
        "class": {"fire", "no_fire", "ventilation_disturbance", "sensor_fault"},
        "consistency": {"consistent", "inconsistent"},
        "violation_type": {
            "reverse",
            "jump",
            "disappearance",
            "direction_flip",
            "sensor_conflict",
        },
        "source_region": {f"R{index}" for index in range(1, 9)},
        "stage": {"incipient", "growth", "developed", "decay"},
        "risk_region": {f"R{index}" for index in range(1, 9)},
        "risk_level": {"low", "moderate", "high", "critical"},
        "mechanism": {
            "buoyant_plume",
            "ceiling_jet",
            "smoke_layer",
            "longitudinal_ventilation",
            "backlayering",
            "extraction_dominated",
        },
        "temperature_trend": {"up", "stable", "down"},
        "smoke_trend": {"up", "stable", "down"},
        "visibility_trend": {"up", "stable", "down"},
        "first_high_risk_region": {*(f"R{index}" for index in range(1, 9)), "none"},
        "comparison": {"A", "B", "same"},
    }
    for name in contract.answer_fields:
        if name in allowed_values and fields.get(name) not in allowed_values[name]:
            errors.append(f"{task_id} has invalid {name}: {fields.get(name)!r}")
    violation = fields.get("violation_type")
    if task_id == "L1-3":
        if (
            fields.get("consistency") == "inconsistent"
            and violation not in allowed_values["violation_type"]
        ):
            errors.append("inconsistent L1-3 answers require a valid violation_type")
        if fields.get("consistency") == "consistent" and violation is not None:
            errors.append("consistent L1-3 answers require violation_type=null")

    track_value = qa.get("track")
    if not isinstance(track_value, str):
        errors.append("track must be a string")
        return errors
    track = track_value
    observation = qa.get("observation", {})
    modality_by_track = {"S": "structured", "I": "images", "V": "video"}
    selected = modality_by_track.get(track)
    for modality in modality_by_track.values():
        value = observation.get(modality)
        if modality == selected and value is None:
            errors.append(f"track {track} requires observation.{modality}")
        if modality != selected and value is not None:
            errors.append(f"track {track} requires unused observation.{modality}=null")

    source_value = qa.get("source_domain")
    if not isinstance(source_value, str):
        errors.append("source_domain must be a string")
        return errors
    source = source_value
    source_contract = SOURCES.get(source)
    if source_contract is None:
        errors.append(f"unknown source_domain: {source}")
        return errors
    if task_id not in SOURCE_TASKS.get(source, frozenset()):
        errors.append(f"source {source} is not eligible for task {task_id}")
    if track not in SOURCE_TRACKS.get(source, frozenset()):
        errors.append(f"source {source} is not eligible for track {track}")
    disposition = source_eligibility(source, task_id, track)
    if disposition not in {"supported", "unsupported"}:
        errors.append(
            f"source {source} is not formally accepted for QA "
            f"(state={source_contract.state})"
        )

    if task_id == "L1-2":
        options = qa.get("options") or []
        if len(options) != 4:
            errors.append("L1-2 requires exactly four options")
        option_ids = [option.get("id") for option in options]
        if len(set(option_ids)) != len(option_ids):
            errors.append("option IDs must be unique")
        if qa.get("answer", {}).get("choice") not in {"A", "B", "C", "D"}:
            errors.append("L1-2 requires answer.choice A/B/C/D")
    quality_status = qa.get("quality", {}).get("status")
    ambiguity_reason = qa.get("quality", {}).get("ambiguity_reason")
    if quality_status == "eligible" and ambiguity_reason:
        errors.append("eligible QA must not have an ambiguity_reason")
    if quality_status == "eligible_expert_review_deferred":
        if task_id != "L2-3":
            errors.append("only L2-3 may defer independent expert review")
        if ambiguity_reason != "independent_fire_engineering_review_deferred_by_user":
            errors.append("expert-review-deferred QA requires the frozen deferred-review reason")
    return errors


def validate_prediction_semantics(
    prediction: dict[str, Any], gold: dict[str, Any] | None = None
) -> list[str]:
    """Validate task-specific prediction semantics and optional gold binding."""
    task_id = prediction.get("task_id")
    contract = TASKS.get(task_id) if isinstance(task_id, str) else None
    if contract is None:
        return [f"unknown task_id: {task_id!r}"]
    errors: list[str] = []
    if gold is not None:
        if prediction.get("qa_id") != gold.get("qa_id"):
            errors.append("prediction qa_id does not match bound gold QA")
        if task_id != gold.get("task_id"):
            errors.append("prediction task_id does not match gold task_id")
    answer = prediction.get("answer", {})
    if not isinstance(answer, dict):
        return ["prediction answer must be an object"]
    fields = answer.get("fields", {})
    if not isinstance(fields, dict):
        return ["prediction answer.fields must be an object"]

    machine_contract = prediction_contract(task_id)
    field_contracts = machine_contract["answer_fields"]
    unexpected = sorted(set(fields) - set(field_contracts))
    if unexpected:
        errors.append(f"{task_id} prediction has unexpected fields: {', '.join(unexpected)}")
    missing = [field for field in field_contracts if field not in fields]
    if missing:
        errors.append(f"{task_id} prediction missing answer fields: {', '.join(missing)}")
    for field, allowed in field_contracts.items():
        if field in fields and fields[field] not in allowed:
            errors.append(f"{task_id} prediction has invalid {field}: {fields[field]!r}")

    choice_allowed = machine_contract["choice"]
    choice = answer.get("choice")
    if choice_allowed is None:
        if choice is not None:
            errors.append(f"{task_id} prediction requires answer.choice=null")
    elif choice not in choice_allowed:
        errors.append(f"{task_id} prediction has invalid answer.choice: {choice!r}")
    if machine_contract.get("choice_must_equal_fields_choice"):
        if fields.get("choice") != choice:
            errors.append(f"{task_id} prediction requires fields.choice == answer.choice")

    if task_id == "L1-3":
        consistency = fields.get("consistency")
        violation = fields.get("violation_type")
        if consistency == "consistent" and violation is not None:
            errors.append("consistent L1-3 predictions require violation_type=null")
        if consistency == "inconsistent" and violation is None:
            errors.append("inconsistent L1-3 predictions require a violation_type")
    return errors

def validate_event_groups(rows: Iterable[dict[str, Any]]) -> list[str]:
    assignments: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        assignments[str(row.get("event_group"))].add(str(row.get("split")))
    return [
        f"event_group {group} crosses splits: {sorted(splits)}"
        for group, splits in sorted(assignments.items())
        if len(splits) > 1
    ]


def read_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        with path.open(encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
    value = load_json(path)
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    raise DatasetValidationError(f"{path} must contain a JSON object, list, or JSONL objects")
