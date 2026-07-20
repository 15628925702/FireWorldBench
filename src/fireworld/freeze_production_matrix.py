"""Freeze the 180-run FireWorldBench v2 FDS production matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

TARGET_CLASSES = {
    "fire": 126,
    "no_fire": 18,
    "ventilation_disturbance": 18,
    "non_fire_disturbance": 18,
}
TARGET_SPLITS = {
    "train": 96,
    "dev": 20,
    "test_iid": 20,
    "test_ood_geometry": 16,
    "test_ood_condition": 14,
    "test_ood_view_sensor": 14,
}
PLANNED_ALLOCATION = {
    "train": {"fire": 62, "no_fire": 9, "ventilation_disturbance": 8, "non_fire_disturbance": 9},
    "dev": {"fire": 11, "no_fire": 2, "ventilation_disturbance": 2, "non_fire_disturbance": 1},
    "test_iid": {"fire": 9, "no_fire": 1, "ventilation_disturbance": 1, "non_fire_disturbance": 2},
    "test_ood_geometry": {
        "fire": 11,
        "no_fire": 1,
        "ventilation_disturbance": 2,
        "non_fire_disturbance": 2,
    },
    "test_ood_condition": {
        "fire": 10,
        "no_fire": 1,
        "ventilation_disturbance": 2,
        "non_fire_disturbance": 1,
    },
    "test_ood_view_sensor": {
        "fire": 10,
        "no_fire": 2,
        "ventilation_disturbance": 1,
        "non_fire_disturbance": 1,
    },
}
NEW_CF_FAMILIES = {
    "train": 12,
    "dev": 2,
    "test_iid": 2,
    "test_ood_geometry": 2,
    "test_ood_condition": 2,
    "test_ood_view_sensor": 2,
}


def opaque(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha256(value.encode()).hexdigest()[:12].upper()}"


def read(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(path)
    return value


def existing_rows(root: Path) -> list[dict[str, Any]]:
    sources = (
        (
            "mini_pilot_7",
            [
                "fire",
                "fire",
                "no_fire",
                "ventilation_disturbance",
                "non_fire_disturbance",
                "fire",
                "fire",
            ],
        ),
        (
            "explicit_observation_pilot_10",
            ["fire"] * 6 + ["no_fire", "ventilation_disturbance", "non_fire_disturbance", "fire"],
        ),
        ("explicit_counterfactual_01", ["fire", "fire"]),
    )
    output: list[dict[str, Any]] = []
    for name, classes in sources:
        events = read(root / "fire_events" / name / "fire_events.json")
        split_rows = read(root / "splits" / f"{name}_event_group_manifest.json")
        split_by_id = {row["event_id"]: row["split"] for row in split_rows}
        if len(events) != len(classes):
            raise ValueError(f"existing class map mismatch: {name}")
        for event, event_class in zip(events, classes, strict=True):
            output.append(
                {
                    "event_id": event["event_id"],
                    "event_group": event["event_group"],
                    "status": "qualified_existing",
                    "event_class": event_class,
                    "l1_class": "no_fire" if event_class == "non_fire_disturbance" else event_class,
                    "split": split_by_id[event["event_id"]],
                    "source_ref": f"fire_events/{name}/{event['event_id']}.json",
                    "geometry": event["geometry"]["scene_type"],
                    "counterfactual": event["controls"]["intervention"],
                }
            )
    return output


def geometry(split: str, index: int) -> str:
    if split == "test_ood_geometry":
        return ("atrium_ood", "corridor_ood")[index % 2]
    return ("tunnel_a", "tunnel_b", "room_a", "room_b")[index % 4]


def planned_rows(start_index: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    serial = start_index
    family_serial = 3
    for split, allocation in PLANNED_ALLOCATION.items():
        fire_count = allocation["fire"]
        family_count = NEW_CF_FAMILIES[split]
        pair_rows = family_count * 2
        for local in range(fire_count):
            event_id = opaque("FWE", f"production-v2.1:{serial}")
            family = None
            side = None
            intervention = None
            control_index = local
            if local < pair_rows:
                pair_index = local // 2
                side = "A" if local % 2 == 0 else "B"
                family = f"FWCF-P{family_serial + pair_index:03d}"
                intervention = {
                    "variable": "hrrpua",
                    "value": 900.0 if side == "A" else 1500.0,
                    "side": side,
                }
                control_index = pair_index
            group = opaque("FWG", family or event_id)
            rows.append(
                {
                    "event_id": event_id,
                    "event_group": group,
                    "status": "planned",
                    "event_class": "fire",
                    "l1_class": "fire",
                    "split": split,
                    "geometry": geometry(split, control_index),
                    "source_region": f"R{control_index % 8 + 1}",
                    "hrrpua": intervention["value"]
                    if intervention
                    else (600.0, 900.0, 1200.0, 1500.0, 1800.0, 2200.0)[control_index % 6],
                    "ventilation_mode": ("still", "longitudinal", "extraction")[control_index % 3],
                    "supply_velocity": (0.0, 1.5, 2.5)[control_index % 3],
                    "sensor_variant": "ood_sparse_shifted"
                    if split == "test_ood_view_sensor"
                    else "standard",
                    "counterfactual_family": family,
                    "intervention": intervention,
                    "production_batch": None,
                }
            )
            serial += 1
        family_serial += family_count
        for event_class in ("no_fire", "ventilation_disturbance", "non_fire_disturbance"):
            for local in range(allocation[event_class]):
                event_id = opaque("FWE", f"production-v2.1:{serial}")
                rows.append(
                    {
                        "event_id": event_id,
                        "event_group": opaque("FWG", event_id),
                        "status": "planned",
                        "event_class": event_class,
                        "l1_class": "no_fire"
                        if event_class == "non_fire_disturbance"
                        else event_class,
                        "split": split,
                        "geometry": geometry(split, fire_count + local),
                        "source_region": None,
                        "hrrpua": 0.0,
                        "ventilation_mode": "longitudinal"
                        if event_class == "ventilation_disturbance"
                        else "still",
                        "supply_velocity": 2.5 if event_class == "ventilation_disturbance" else 0.0,
                        "heater_temperature_c": 120.0
                        if event_class == "non_fire_disturbance"
                        else None,
                        "sensor_variant": "ood_sparse_shifted"
                        if split == "test_ood_view_sensor"
                        else "standard",
                        "counterfactual_family": None,
                        "intervention": None,
                        "production_batch": None,
                    }
                )
                serial += 1
    return rows


def assign_batches(rows: list[dict[str, Any]]) -> None:
    planned = [row for row in rows if row["status"] == "planned"]
    for index, row in enumerate(planned):
        row["production_batch"] = f"production_batch_{index // 10 + 1:02d}"


def build(root: Path) -> Path:
    rows = existing_rows(root)
    rows.extend(planned_rows(len(rows) + 1))
    assign_batches(rows)
    class_counts = Counter(row["event_class"] for row in rows)
    split_counts = Counter(row["split"] for row in rows)
    families: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        family = row.get("counterfactual_family")
        if family:
            families.setdefault(family, []).append(row)
    existing_family_groups = {
        row["event_group"]
        for row in rows
        if row["status"] == "qualified_existing" and row.get("counterfactual")
    }
    if dict(class_counts) != TARGET_CLASSES:
        raise ValueError(f"class counts: {class_counts}")
    if dict(split_counts) != TARGET_SPLITS:
        raise ValueError(f"split counts: {split_counts}")
    if len(rows) != 180 or len(families) + len(existing_family_groups) != 24:
        raise ValueError("matrix size or counterfactual family count")
    if any(
        len(value) != 2
        or len({row["event_group"] for row in value}) != 1
        or len({row["split"] for row in value}) != 1
        for value in families.values()
    ):
        raise ValueError("counterfactual pair grouping")
    matrix = {
        "schema_version": "2.1.0",
        "status": "frozen",
        "target_events": 180,
        "qualified_existing": 19,
        "planned_new": 161,
        "target_classes": TARGET_CLASSES,
        "target_splits": TARGET_SPLITS,
        "counterfactual_families": 24,
        "sensor_fault_event_increment": 0,
        "batch_size": 10,
        "rows": rows,
        "audit": {
            "class_counts": dict(class_counts),
            "split_counts": dict(split_counts),
            "planned_batches": len(
                {row["production_batch"] for row in rows if row["status"] == "planned"}
            ),
            "cross_split_counterfactual_leaks": 0,
        },
    }
    output = root / "splits" / "production_matrix.v2.1.json"
    output.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.root.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
