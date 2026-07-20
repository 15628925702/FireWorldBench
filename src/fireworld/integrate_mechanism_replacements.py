"""Materialize calibrated mechanism runs as six matrix-preserving replacement events."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    plan = json.loads((root / "splits" / "mechanism_replacements.v1.json").read_text())
    output = root / "fire_events" / "mechanism_replacements"
    output.mkdir(parents=True, exist_ok=True)
    s_root = root / "derived" / "mechanism_replacements" / "S"
    for item in plan["replacements"]:
        run = root / item["calibration_fds_run"]
        key = run.name
        csv_path = run / f"{key}_devc.csv"
        values = list(csv.reader(csv_path.open(encoding="utf-8")))
        names = values[1]
        rows = [
            {name: float(value) for name, value in zip(names, row, strict=True)}
            for row in values[2:]
            if len(row) == len(names)
        ]
        summary = s_root / item["target_event_id"] / "summary.json"
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(
            json.dumps(
                {
                    "format": "fireworld-mechanism-calibration-v1",
                    "source_csv_sha256": sha(csv_path),
                    "rows": rows,
                },
                indent=2,
            )
            + "\n"
        )
        event = {
            "schema_version": "2.0.0",
            "event_id": item["target_event_id"],
            "event_group": item["target_event_group"],
            "source_domain": "fds",
            "status": "eligible",
            "geometry": {
                "scene_type": "tunnel",
                "coordinate_system": "right-handed-m",
                "dimensions_m": {"length": 20.0, "width": 10.0, "height": 5.0},
                "regions": [],
            },
            "controls": {
                "source_region": "R5",
                "hrr_profile": "ramped",
                "ventilation": {"mode": item["mechanism"]},
                "extraction": None,
                "openings": None,
                "random_seed": 20260720,
                "intervention": None,
            },
            "timeline": {"start_s": 0.0, "end_s": 120.0, "sample_interval_s": 1.0},
            "observations": {
                "structured": {
                    "ref": str(summary.relative_to(root)),
                    "format": "json",
                    "variables": ["temperature", "visibility", "u_velocity"],
                    "units_normalized": True,
                },
                "images": None,
                "video": None,
            },
            "ground_truth": {
                "labels": [
                    {
                        "name": "event_class",
                        "value": "fire",
                        "origin": "simulation_truth",
                        "rule_version": None,
                    },
                    {
                        "name": "mechanism",
                        "value": item["mechanism"],
                        "origin": "deterministic_rule",
                        "rule_version": "mechanism-rule-calibration.v1",
                    },
                ]
            },
            "provenance": {
                "source_version": "mechanism-replacement-v1",
                "source_files": [
                    {
                        "opaque_ref": f"raw/{item['target_event_id']}/input",
                        "sha256": sha(run / f"{key}.fds"),
                    },
                    {
                        "opaque_ref": f"raw/{item['target_event_id']}/sensors",
                        "sha256": sha(csv_path),
                    },
                ],
                "transform_version": "mechanism-replacement-v1",
                "created_at": "2026-07-20T00:00:00Z",
                "fds": {
                    "fds_version": "6.11.1",
                    "smokeview_version": "6.11.2",
                    "fdgen_version": "not_used",
                    "mesh": {"dimensions_m": {"length": 20.0, "width": 10.0, "height": 5.0}},
                    "boundary_hash": sha(run / f"{key}.fds"),
                    "random_seed": 20260720,
                    "input_sha256": sha(run / f"{key}.fds"),
                    "log_ref": str((run / f"{key}_fds.log").relative_to(root)),
                    "run_status": "success",
                },
            },
            "license": {
                "license_id": "NIST-generated-output-review-pending",
                "evidence_ref": "governance/licenses/fds.md",
                "citation": "NIST Fire Dynamics Simulator and Smokeview",
                "allowed_uses": ["research", "evaluation", "derivation"],
                "redistribution": "unknown",
            },
        }
        (output / f"{item['target_event_id']}.json").write_text(json.dumps(event, indent=2) + "\n")
        item["status"] = "integrated"
        item["event_ref"] = str((output / f"{item['target_event_id']}.json").relative_to(root))
    (root / "splits" / "mechanism_replacements.v1.json").write_text(
        json.dumps(plan, indent=2) + "\n"
    )
    print(json.dumps({"integrated": len(plan["replacements"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
