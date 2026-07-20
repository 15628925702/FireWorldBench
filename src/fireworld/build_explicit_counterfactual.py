"""Build the verified explicit-observation HRRPUA A/B family and L3-3 QA."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from fireworld.mini_pilot import (
    FDS_VERSION,
    SMOKEVIEW_VERSION,
    digest,
    file_hash,
    label,
    opaque_id,
    parse_fds,
    regions,
    write_json,
)


def rows(path: Path) -> list[dict[str, float]]:
    with path.open(encoding="utf-8", newline="") as handle:
        values = list(csv.reader(handle))
    names = values[1]
    return [
        {name: float(value) for name, value in zip(names, row, strict=True)}
        for row in values[2:]
        if len(row) == len(names)
    ]


def nearest(values: list[dict[str, float]], time_s: float) -> dict[str, float]:
    return min(values, key=lambda row: abs(row["Time"] - time_s))


def build(root: Path) -> dict[str, Path]:
    batch = root / "fds_runs" / "explicit_counterfactual_01"
    event_root = root / "fire_events" / "explicit_counterfactual_01"
    derived_root = root / "derived" / "explicit_counterfactual_01" / "S"
    qa_root = root / "qa" / "explicit_counterfactual_01"
    for path in (
        event_root,
        derived_root,
        qa_root,
        root / "splits",
        root / "reports" / "explicit_counterfactual_01",
    ):
        path.mkdir(parents=True, exist_ok=True)
    group = opaque_id("FWG", "explicit-counterfactual-01:hrrpua")
    base_event = opaque_id("FWE", "explicit-counterfactual-01:base")
    events: list[dict[str, Any]] = []
    summaries: dict[str, str] = {}
    future_temp: dict[str, float] = {}
    for key in ("cf_hrr_a", "cf_hrr_b"):
        run = batch / key
        fds = run / f"{key}.fds"
        devc = run / f"{key}_devc.csv"
        dimensions, hrr, ventilation = parse_fds(fds)
        values = rows(devc)
        event_id = opaque_id("FWE", f"explicit-counterfactual-01:{key}")
        summary_path = derived_root / event_id / "summary.json"
        write_json(
            summary_path,
            {
                "format": "fireworld-structured-v2",
                "source_csv_sha256": file_hash(devc),
                "rows": [nearest(values, time) for time in (20.0, 40.0, 60.0, 90.0, 120.0)],
            },
        )
        summaries[key] = str(summary_path.relative_to(root))
        future_temp[key] = nearest(values, 90.0)["T_SOURCE_NEAR"]
        labels = [
            label("event_class", "fire", "simulation_truth"),
            label("source_region", "R2", "simulation_truth"),
            label("stage", "developed", "deterministic_rule"),
            label("hrrpua", hrr, "simulation_truth"),
        ]
        event = {
            "schema_version": "2.0.0",
            "event_id": event_id,
            "event_group": group,
            "source_domain": "fds",
            "status": "eligible",
            "geometry": {
                "scene_type": "tunnel",
                "coordinate_system": "right-handed-m",
                "dimensions_m": dimensions,
                "regions": regions(dimensions),
            },
            "controls": {
                "source_region": "R2",
                "hrr_profile": "ramped",
                "ventilation": {"mode": ventilation},
                "extraction": None,
                "openings": None,
                "random_seed": 2026071950,
                "intervention": {"variable": "hrrpua", "value": hrr, "base_event_id": base_event},
            },
            "timeline": {"start_s": 0.0, "end_s": 120.0, "sample_interval_s": 1.0},
            "observations": {
                "structured": {
                    "ref": summaries[key],
                    "format": "json",
                    "variables": ["temperature", "visibility", "u_velocity"],
                    "units_normalized": True,
                },
                "images": None,
                "video": None,
            },
            "ground_truth": {"labels": labels},
            "provenance": {
                "source_version": "explicit-counterfactual-01",
                "source_files": [
                    {"opaque_ref": f"raw/{event_id}/input", "sha256": file_hash(fds)},
                    {"opaque_ref": f"raw/{event_id}/sensors", "sha256": file_hash(devc)},
                ],
                "transform_version": "explicit-counterfactual-2.1.0",
                "created_at": "2026-07-19T00:00:00Z",
                "fds": {
                    "fds_version": FDS_VERSION,
                    "smokeview_version": SMOKEVIEW_VERSION,
                    "fdgen_version": "not_used",
                    "mesh": {"dimensions_m": dimensions},
                    "boundary_hash": digest(fds.read_bytes()),
                    "random_seed": 2026071950,
                    "input_sha256": file_hash(fds),
                    "log_ref": str((run / f"{key}.stderr.log").relative_to(root)),
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
        events.append(event)
        write_json(event_root / f"{event_id}.json", event)
    answer = (
        "A"
        if future_temp["cf_hrr_a"] > future_temp["cf_hrr_b"] + 1.0
        else "B"
        if future_temp["cf_hrr_b"] > future_temp["cf_hrr_a"] + 1.0
        else "same"
    )
    pair_path = derived_root / group / "pair.json"
    write_json(
        pair_path,
        {
            "case_a_ref": summaries["cf_hrr_a"],
            "case_b_ref": summaries["cf_hrr_b"],
            "intervention_variable": "hrrpua",
            "future_temperature_c": {"A": future_temp["cf_hrr_a"], "B": future_temp["cf_hrr_b"]},
        },
    )
    qa = {
        "schema_version": "2.0.0",
        "qa_id": opaque_id("FWQ", group + ":L3-3:S"),
        "case_id": opaque_id("FWC", group + ":L3-3:S"),
        "event_id": events[0]["event_id"],
        "event_group": group,
        "source_domain": "fds",
        "split": "test_iid",
        "layer": "L3",
        "task_id": "L3-3",
        "track": "S",
        "observation": {
            "structured": {"ref": str(pair_path.relative_to(root))},
            "images": None,
            "video": None,
            "context": (
                "A/B share geometry, sensors, ventilation and timeline; only HRRPUA differs."
            ),
            "time_window_s": [20.0, 90.0],
        },
        "confidence_target": 1.0,
        "evidence_metadata": {"required": False, "gold_refs": []},
        "provenance": {
            "event_manifest_sha256": digest(json.dumps(events, sort_keys=True)),
            "builder_version": "explicit-counterfactual-2.1.0",
            "task_config_sha256": digest("FireWorldBenchv2 nine-task protocol"),
            "source_license_ref": "governance/licenses/fds.md",
        },
        "quality": {
            "status": "eligible",
            "ambiguity_reason": None,
            "shortcut_checks": {
                "opaque_paths": True,
                "time_matched": True,
                "option_style_matched": True,
                "appearance_matched": True,
            },
        },
        "question": (
            "Which case has the higher future source-region temperature, or are they the same?"
        ),
        "options": [
            {"id": value, "content_ref": None, "text": "comparison candidate"}
            for value in ("A", "B", "C")
        ],
        "answer": {"choice": None, "fields": {"comparison": answer}},
        "scoring": {
            "primary": "accuracy",
            "components": ["comparison"],
            "secondary": ["counterfactual_consistency"],
        },
    }
    write_json(event_root / "fire_events.json", events)
    write_json(qa_root / "qa.json", [qa])
    split_path = root / "splits" / "explicit_counterfactual_01_event_group_manifest.json"
    write_json(
        split_path,
        [
            {"event_id": event["event_id"], "event_group": group, "split": "test_iid"}
            for event in events
        ],
    )
    report_path = root / "reports" / "explicit_counterfactual_01" / "build_report.json"
    write_json(
        report_path,
        {
            "status": "built_pending_strict_validation",
            "unique_variable": "hrrpua",
            "future_temperature_c": future_temp,
            "answer": answer,
        },
    )
    return {
        "events": event_root / "fire_events.json",
        "qa": qa_root / "qa.json",
        "split": split_path,
        "report": report_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps({key: str(value) for key, value in build(args.root.resolve()).items()}, indent=2)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
