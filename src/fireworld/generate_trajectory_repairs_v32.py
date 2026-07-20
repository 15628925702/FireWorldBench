"""Generate physically distinct replacement inputs for duplicate trajectories."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from fireworld.build_global_release import load_events, raw_for_event
from fireworld.generate_production_batch import input_text
from fireworld.mini_pilot import write_json

BATCH = "trajectory_repair_v3_2"


def row_hash(rows: list[dict[str, float]]) -> str:
    value = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode()).hexdigest()


def normalized_fds(text: str) -> str:
    text = re.sub(r"CHID='[^']+'", "CHID='NORMALIZED'", text)
    return re.sub(r"TITLE='[^']+'", "TITLE='NORMALIZED'", text)


def labels(event: dict[str, Any]) -> dict[str, Any]:
    return {item["name"]: item["value"] for item in event["ground_truth"]["labels"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    output = root / "fds_runs" / BATCH
    if output.exists():
        raise ValueError(f"refusing to overwrite {output}")
    event_pairs, batch_index = load_events(root)
    events = {event["event_id"]: event for event, _ in event_pairs}
    split = {event["event_id"]: split_name for event, split_name in event_pairs}
    trajectories: dict[str, list[str]] = defaultdict(list)
    for event, _ in event_pairs:
        trajectories[row_hash(raw_for_event(root, event, batch_index))].append(event["event_id"])

    repair_ids: set[str] = set()
    duplicates: list[dict[str, Any]] = []
    for digest, members in sorted(trajectories.items()):
        if len(members) < 2:
            continue
        keeper = sorted(members)[0]
        repair_ids.update(set(members) - {keeper})
        duplicates.append({"trajectory_sha256": digest, "keeper": keeper, "superseded": sorted(set(members) - {keeper})})

    groups: dict[str, list[str]] = defaultdict(list)
    for event in events.values():
        intervention = (event.get("controls") or {}).get("intervention")
        if intervention:
            groups[event["event_group"]].append(event["event_id"])
    for members in groups.values():
        if repair_ids.intersection(members):
            repair_ids.update(members)

    matrix = json.loads((root / "splits/production_matrix.v2.1.json").read_text())
    matrix_rows = {row["event_id"]: row for row in matrix["rows"]}
    environment_keys = sorted(
        {
            events[event_id]["event_group"]
            if events[event_id]["controls"].get("intervention")
            else event_id
            for event_id in repair_ids
        }
    )
    environment_rank = {key: rank for rank, key in enumerate(environment_keys, 1)}
    output.mkdir(parents=True)
    runs: list[dict[str, Any]] = []
    normalized_inputs: dict[str, str] = {}
    pair_environments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    fire_environment_keys = [
        key
        for key in environment_keys
        if any(
            event_id in repair_ids
            and (events[event_id]["event_group"] if (matrix_rows.get(event_id, {}).get("intervention") or events[event_id]["controls"].get("intervention")) else event_id) == key
            and str(matrix_rows.get(event_id, {}).get("event_class") or labels(events[event_id]).get("event_class")) == "fire"
            for event_id in repair_ids
        )
    ]
    mechanism_by_environment = {
        key: ("buoyant_plume", "ceiling_jet", "smoke_layer", "longitudinal_ventilation", "backlayering", "extraction_dominated")[index % 6]
        for index, key in enumerate(fire_environment_keys)
    }
    for ordinal, event_id in enumerate(sorted(repair_ids), 1):
        event = events[event_id]
        truth = labels(event)
        source = matrix_rows.get(event_id, {})
        event_class = str(source.get("event_class") or truth.get("event_class", "fire"))
        region = str(truth.get("source_region") or event["controls"].get("source_region") or "R1")
        intervention = source.get("intervention") or event["controls"].get("intervention")
        family_key = event["event_group"] if intervention else event_id
        environment_slot = environment_rank[family_key]
        geometry = source.get("geometry")
        if geometry not in {"tunnel_a", "tunnel_b", "room_a", "room_b", "atrium_ood", "corridor_ood"}:
            scene = event["geometry"]["scene_type"]
            geometry = "tunnel_a" if scene == "tunnel" else "room_a"
        base_hrr = float(truth.get("hrrpua") or source.get("hrrpua") or 900.0)
        if intervention:
            hrr = float(intervention["value"])
        elif event_class == "fire":
            hrr = max(350.0, base_hrr * (0.82 + 0.035 * (environment_slot % 11)))
        else:
            hrr = 0.0
        if event_class == "ventilation_disturbance":
            supply = 1.50 + 0.01 * environment_slot
        elif event_class == "fire":
            mechanism = mechanism_by_environment[family_key]
            supply = {
                "buoyant_plume": 0.10,
                "ceiling_jet": 0.20,
                "smoke_layer": 0.30,
                "longitudinal_ventilation": 1.60,
                "backlayering": 0.90,
                "extraction_dominated": 0.35,
            }[mechanism] + 0.001 * environment_slot
            if not intervention:
                hrr = {
                    "buoyant_plume": 2100.0,
                    "ceiling_jet": 1450.0,
                    "smoke_layer": 650.0,
                    "longitudinal_ventilation": 1100.0,
                    "backlayering": 1250.0,
                    "extraction_dominated": 1000.0,
                }[mechanism] + environment_slot
        elif event_class == "no_fire":
            supply = 0.01 + 0.001 * environment_slot
        else:
            supply = 0.05 + 0.01 * environment_slot
        heater = 80.0 + environment_slot if event_class == "non_fire_disturbance" else None
        repair_row = {
            "event_id": event_id,
            "event_group": event["event_group"],
            "event_class": event_class,
            "l1_class": "no_fire" if event_class == "non_fire_disturbance" else event_class,
            "split": split[event_id],
            "geometry": geometry,
            "source_region": region,
            "hrrpua": round(hrr, 3),
            "ventilation_mode": "longitudinal" if supply > 0 else "still",
            "supply_velocity": round(supply, 3),
            "heater_temperature_c": heater,
            "sensor_variant": source.get("sensor_variant", "standard"),
            "counterfactual_family": source.get("counterfactual_family"),
            "intervention": source.get("intervention"),
            "repair_environment_slot": environment_slot,
            "mechanism_target": mechanism_by_environment.get(family_key),
        }
        key = f"tr_{ordinal:03d}"
        run = output / key
        run.mkdir()
        text = input_text(repair_row, key).replace("FireWorldBench v2.1 production", "FireWorldBench v3.2 trajectory repair")
        (run / f"{key}.fds").write_text(text)
        normalized = normalized_fds(text)
        normalized_inputs[event_id] = hashlib.sha256(normalized.encode()).hexdigest()
        runs.append({"run_key": key, "event_id": event_id, "matrix_row": repair_row})
        if intervention:
            without_hrr = re.sub(r"HRRPUA=[0-9.]+", "HRRPUA=NORMALIZED", normalized)
            pair_environments[event["event_group"]].append({"event_id": event_id, "environment_sha256": hashlib.sha256(without_hrr.encode()).hexdigest()})

    pair_errors = {group: members for group, members in pair_environments.items() if len(members) != 2 or len({item["environment_sha256"] for item in members}) != 1}
    collisions = [digest for digest, count in Counter(normalized_inputs.values()).items() if count > 1]
    if collisions or pair_errors:
        raise ValueError({"input_collisions": collisions, "pair_errors": pair_errors})
    manifest = {"schema_version": "fds-core-v3.2.0", "batch": BATCH, "fds_version": "6.11.1", "reason": "replace cross-event duplicate physical trajectories", "old_unique_trajectories": len(trajectories), "repair_runs": len(runs), "duplicate_groups": duplicates, "counterfactual_pair_environment_audit": pair_environments, "normalized_input_unique": True, "runs": runs}
    write_json(output / "input_manifest.json", manifest)
    write_json(root / "reports/fds_core_v3_2_trajectory_repair_plan.json", {"status": "inputs_frozen_ready_for_fds", "old_unique_trajectories": len(trajectories), "repair_runs": len(runs), "duplicate_group_count": len(duplicates), "repair_class_counts": dict(Counter(item["matrix_row"]["event_class"] for item in runs)), "repair_split_counts": dict(Counter(item["matrix_row"]["split"] for item in runs)), "normalized_input_unique": True, "counterfactual_pair_environment_match": not pair_errors})
    print(json.dumps({"repair_runs": len(runs), "duplicate_groups": len(duplicates), "normalized_input_unique": True, "pair_environment_match": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
