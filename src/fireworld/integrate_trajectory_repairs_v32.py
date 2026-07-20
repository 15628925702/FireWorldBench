"""Build replacement Fire Events after the repair physical audit passes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fireworld.build_production_batch import build
from fireworld.mini_pilot import write_json

BATCH = "trajectory_repair_v3_2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    audit = json.loads((root / "reports/fds_core_v3_2_trajectory_repair_physical_audit.json").read_text())
    if audit["status"] != "passed":
        raise ValueError("repair physical audit has not passed")
    output = root / "fire_events" / BATCH
    if output.exists():
        raise ValueError(f"refusing to overwrite {output}")
    build(root, BATCH)
    events_path = output / "fire_events.json"
    events = json.loads(events_path.read_text())
    manifest = json.loads((root / "fds_runs" / BATCH / "input_manifest.json").read_text())
    by_event = {item["event_id"]: item for item in manifest["runs"]}
    previous_events = {
        path.stem: json.loads(path.read_text())
        for path in (root / "fire_events/fds_core_v3_1").glob("FWE-*.json")
    }
    for event in events:
        row = by_event[event["event_id"]]["matrix_row"]
        for label in event["ground_truth"]["labels"]:
            if label["name"] == "event_class":
                label["value"] = row["event_class"]
        event["ground_truth"]["labels"] = [
            label
            for label in event["ground_truth"]["labels"]
            if label["name"] != "hrrpua"
        ]
        event["ground_truth"]["labels"].append(
            {
                "name": "hrrpua",
                "value": row["hrrpua"],
                "origin": "simulation_truth",
                "rule_version": None,
            }
        )
        event["controls"]["intervention"] = previous_events[event["event_id"]]["controls"].get(
            "intervention"
        )
        if row["event_class"] in {"no_fire", "ventilation_disturbance"}:
            event["controls"]["source_region"] = None
            event["ground_truth"]["labels"] = [
                label
                for label in event["ground_truth"]["labels"]
                if label["name"] != "source_region"
            ]
        event["provenance"]["source_version"] = "trajectory-repair-v3.2"
        event["provenance"]["transform_version"] = "trajectory-repair-v3.2.0"
        event["controls"]["random_seed"] = 2026072000 + int(by_event[event["event_id"]]["run_key"][-3:])
        event["provenance"]["fds"]["random_seed"] = event["controls"]["random_seed"]
        event["controls"]["ventilation"] = {
            "mode": row["ventilation_mode"],
            "supply_velocity_m_s": row["supply_velocity"],
        }
        event["controls"]["extraction"] = (
            {"mode": "mechanical_ceiling_exhaust", "velocity_m_s": 2.0}
            if row.get("mechanism_target") == "extraction_dominated"
            else None
        )
        event["license"] = {
            "license_id": "FDS-GENERATED-INTERNAL-RESEARCH-V3.2",
            "evidence_ref": "governance/licenses/fds_internal_release_v3_1.md",
            "citation": "NIST Fire Dynamics Simulator 6.11.1 and Smokeview 6.11.2",
            "allowed_uses": ["research", "evaluation", "derivation"],
            "redistribution": "restricted",
        }
    write_json(events_path, events)
    for event in events:
        write_json(output / f"{event['event_id']}.json", event)
    report = {"schema_version": "fds-core-v3.2.0", "status": "integrated_pending_global_rebuild", "events": len(events), "source_batch": BATCH}
    write_json(root / "reports/fds_core_v3_2_trajectory_repair_integration.json", report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
