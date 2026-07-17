"""Frozen v2 task, source, and track contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskContract:
    layer: str
    primary: str
    answer_fields: tuple[str, ...]


TASKS: dict[str, TaskContract] = {
    "L1-1": TaskContract("L1", "accuracy", ("class",)),
    "L1-2": TaskContract("L1", "accuracy", ("choice",)),
    "L1-3": TaskContract("L1", "accuracy", ("consistency",)),
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

SOURCE_TASKS: dict[str, frozenset[str]] = {
    "fds": frozenset(TASKS),
    "immersed_tunnel": frozenset({"L1-1", "L2-1", "L3-1", "L3-2", "L3-3"}),
    "polyu": frozenset({"L2-3", "L3-1", "L3-3"}),
    "dfire": frozenset({"L1-1"}),
    "fire360": frozenset({"L1-3"}),
    "detectium": frozenset(),
}

SOURCE_TRACKS: dict[str, frozenset[str]] = {
    "fds": frozenset({"S", "I", "V"}),
    "immersed_tunnel": frozenset({"S"}),
    "polyu": frozenset({"S"}),
    "dfire": frozenset({"I"}),
    "fire360": frozenset({"V"}),
    "detectium": frozenset({"I", "V"}),
}

MAIN_SPLITS = frozenset(
    {"train", "dev", "test_iid", "test_ood_geometry", "test_ood_condition", "test_ood_view_sensor"}
)
