"""Frozen v2 task, source, and track contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskContract:
    layer: str
    primary: str
    answer_fields: tuple[str, ...]


@dataclass(frozen=True)
class SourceContract:
    """A source's factual state, not an aspirational coverage claim."""

    report: str
    state: str
    tasks: frozenset[str]
    tracks: frozenset[str]
    formal_qa_allowed: bool


TASKS: dict[str, TaskContract] = {
    "L1-1": TaskContract("L1", "accuracy", ("class",)),
    "L1-2": TaskContract("L1", "accuracy", ("choice",)),
    "L1-3": TaskContract("L1", "accuracy", ("consistency", "violation_type")),
    "L2-1": TaskContract("L2", "component_accuracy", ("source_region", "stage")),
    "L2-2": TaskContract("L2", "component_accuracy", ("risk_region", "risk_level")),
    "L2-3": TaskContract("L2", "accuracy", ("mechanism",)),
    "L3-1": TaskContract(
        "L3",
        "mean_accuracy",
        ("temperature_trend", "smoke_trend", "visibility_trend"),
    ),
    "L3-2": TaskContract("L3", "accuracy", ("first_high_risk_region",)),
    "L3-3": TaskContract("L3", "accuracy", ("comparison",)),
}

SOURCES: dict[str, SourceContract] = {
    "fds": SourceContract("main", "formal", frozenset(TASKS), frozenset({"S", "I", "V"}), True),
    "immersed_tunnel": SourceContract("external_cfd", "candidate", frozenset({"L1-1", "L2-1", "L3-1", "L3-2", "L3-3"}), frozenset({"S"}), False),
    "polyu": SourceContract("experiment", "candidate", frozenset({"L2-3", "L3-1", "L3-3"}), frozenset({"S"}), False),
    "furg_fire_substitute": SourceContract("real_video_ood_substitute", "candidate_substitute", frozenset({"L1-3"}), frozenset({"I", "V"}), False),
    "kaggle_video_supplement": SourceContract("real_video_ood_substitute", "candidate_substitute", frozenset(), frozenset({"I", "V"}), False),
    "deepquest_fire_smoke": SourceContract("real_image_ood_substitute", "downloading_substitute", frozenset(), frozenset({"I"}), False),
    "dfire": SourceContract("real_image_ood", "raw_sample_only", frozenset(), frozenset({"I"}), False),
    "fire360": SourceContract("real_video_ood", "unavailable", frozenset(), frozenset({"V"}), False),
    "detectium": SourceContract("external_ood", "quarantined", frozenset(), frozenset(), False),
    "fire360_mirror": SourceContract("quarantine", "quarantined", frozenset(), frozenset(), False),
}

SOURCE_TASKS = {source: contract.tasks for source, contract in SOURCES.items()}
SOURCE_TRACKS = {source: contract.tracks for source, contract in SOURCES.items()}


def source_eligibility(source: str, task_id: str, track: str) -> str:
    """Return a stable eligibility disposition for a source/task/track triple."""
    contract = SOURCES.get(source)
    if contract is None:
        return "unknown_source"
    if task_id not in contract.tasks or track not in contract.tracks:
        return "unsupported"
    return "supported" if contract.formal_qa_allowed else contract.state

MAIN_SPLITS = frozenset(
    {"train", "dev", "test_iid", "test_ood_geometry", "test_ood_condition", "test_ood_view_sensor"}
)
