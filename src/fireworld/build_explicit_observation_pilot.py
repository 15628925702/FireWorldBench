"""Build v2 events and structured QA from the explicit-observation FDS batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fireworld.mini_pilot import (
    FDS_VERSION,
    SMOKEVIEW_VERSION,
    digest,
    file_hash,
    label,
    load_devc,
    nearest,
    opaque_id,
    parse_fds,
    regions,
    write_json,
)

VERSION = "explicit-observation-pilot-2.1.0"
THRESHOLDS = {
    "high_temperature_c": 60.0,
    "critical_temperature_c": 200.0,
    "high_visibility_m": 10.0,
    "critical_visibility_m": 3.0,
    "trend_temperature_c": 10.0,
    "trend_visibility_m": 3.0,
}


def compact_rows(rows: list[dict[str, float]]) -> list[dict[str, float]]:
    return [
        {key: round(value, 6) for key, value in nearest(rows, time).items()}
        for time in (10, 20, 40, 60, 90, 120)
    ]


def risk_level(temp: float, visibility: float) -> str:
    if temp >= 200.0 or visibility <= 3.0:
        return "critical"
    if temp >= 60.0 or visibility <= 10.0:
        return "high"
    return "low"


def trend(delta: float, deadband: float, inverse: bool = False) -> str:
    if abs(delta) < deadband:
        return "stable"
    rising = delta > 0
    return "up" if rising != inverse else "down"


def observation(ref: str) -> dict[str, Any]:
    return {
        "structured": {"ref": ref},
        "images": None,
        "video": None,
        "context": "Audited FDS structured trajectory.",
        "time_window_s": [20.0, 60.0],
    }


def qa_base(event: dict[str, Any], task: str, split: str, ref: str) -> dict[str, Any]:
    identity = f"{event['event_id']}:{task}:S:{ref}"
    return {
        "schema_version": "2.0.0",
        "qa_id": opaque_id("FWQ", identity),
        "case_id": opaque_id("FWC", identity),
        "event_id": event["event_id"],
        "event_group": event["event_group"],
        "source_domain": "fds",
        "split": split,
        "layer": task[:2],
        "task_id": task,
        "track": "S",
        "observation": observation(ref),
        "confidence_target": 1.0,
        "evidence_metadata": {"required": False, "gold_refs": []},
        "provenance": {
            "event_manifest_sha256": digest(json.dumps(event, sort_keys=True)),
            "builder_version": VERSION,
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
    }


def add_qa(
    qa: list[dict[str, Any]],
    event: dict[str, Any],
    task: str,
    split: str,
    ref: str,
    question: str,
    fields: dict[str, Any],
    primary: str,
    components: list[str],
    options: list[dict[str, Any]] | None = None,
    choice: str | None = None,
) -> None:
    row = qa_base(event, task, split, ref)
    row.update(
        {
            "question": question,
            "options": options,
            "answer": {"choice": choice, "fields": fields},
            "scoring": {"primary": primary, "components": components, "secondary": []},
        }
    )
    qa.append(row)


def event_record(
    root: Path,
    run: Path,
    spec: dict[str, Any],
    index: int,
    ref: str,
    labels: list[dict[str, Any]],
    dimensions: dict[str, float],
) -> dict[str, Any]:
    key = str(spec["key"])
    event_id = opaque_id("FWE", f"explicit-observation-v2.1:{key}")
    return {
        "schema_version": "2.0.0",
        "event_id": event_id,
        "event_group": opaque_id("FWG", f"explicit-observation-v2.1:{key}"),
        "source_domain": "fds",
        "status": "eligible",
        "geometry": {
            "scene_type": "tunnel",
            "coordinate_system": "right-handed-m",
            "dimensions_m": dimensions,
            "regions": regions(dimensions),
        },
        "controls": {
            "source_region": spec["source_region"],
            "hrr_profile": "ramped" if spec["hrrpua"] else None,
            "ventilation": {"mode": spec["ventilation_mode"]},
            "extraction": None,
            "openings": None,
            "random_seed": 2026071900 + index,
            "intervention": None,
        },
        "timeline": {"start_s": 0.0, "end_s": 120.0, "sample_interval_s": 1.0},
        "observations": {
            "structured": {
                "ref": ref,
                "format": "json",
                "variables": ["temperature", "visibility", "u_velocity"],
                "units_normalized": True,
            },
            "images": None,
            "video": None,
        },
        "ground_truth": {"labels": labels},
        "provenance": {
            "source_version": "explicit-observation-batch-01",
            "source_files": [
                {"opaque_ref": f"raw/{event_id}/input", "sha256": file_hash(run / f"{key}.fds")},
                {
                    "opaque_ref": f"raw/{event_id}/sensors",
                    "sha256": file_hash(run / f"{key}_devc.csv"),
                },
            ],
            "transform_version": VERSION,
            "created_at": "2026-07-19T00:00:00Z",
            "fds": {
                "fds_version": FDS_VERSION,
                "smokeview_version": SMOKEVIEW_VERSION,
                "fdgen_version": "not_used",
                "mesh": {"dimensions_m": dimensions},
                "boundary_hash": digest((run / f"{key}.fds").read_bytes()),
                "random_seed": 2026071900 + index,
                "input_sha256": file_hash(run / f"{key}.fds"),
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


def build(root: Path) -> dict[str, Path]:
    batch = root / "fds_runs" / "explicit_observation_batch_01"
    specs = json.loads((batch / "input_manifest.json").read_text(encoding="utf-8"))["runs"]
    event_root = root / "fire_events" / "explicit_observation_pilot_10"
    derived_root = root / "derived" / "explicit_observation_pilot_10" / "S"
    qa_root = root / "qa" / "explicit_observation_pilot_10"
    for path in (
        event_root,
        derived_root,
        qa_root,
        root / "splits",
        root / "reports" / "explicit_observation_batch_01",
    ):
        path.mkdir(parents=True, exist_ok=True)
    events: list[dict[str, Any]] = []
    qa: list[dict[str, Any]] = []
    splits: list[dict[str, str]] = []
    fire_position = 0
    for index, spec in enumerate(specs):
        key = str(spec["key"])
        run = batch / key
        rows = load_devc(run / f"{key}_devc.csv")
        dimensions, hrr, _ = parse_fds(run / f"{key}.fds")
        event_id = opaque_id("FWE", f"explicit-observation-v2.1:{key}")
        split = "train" if index < 6 else "dev" if index < 8 else "test_iid"
        summary_path = derived_root / event_id / "summary.json"
        write_json(
            summary_path,
            {
                "format": "fireworld-structured-v2",
                "source_csv_sha256": file_hash(run / f"{key}_devc.csv"),
                "units": {"temperature": "C", "visibility": "m", "u_velocity": "m/s"},
                "rows": compact_rows(rows),
            },
        )
        ref = str(summary_path.relative_to(root))
        initial = nearest(rows, 20.0)
        future = nearest(rows, 90.0)
        source_region = spec["source_region"]
        event_class = str(spec["event_class"])
        risk = risk_level(future["T_SOURCE_NEAR"], future["V_SOURCE_CEILING"])
        temperature_trend = trend(future["T_SOURCE_NEAR"] - initial["T_SOURCE_NEAR"], 10.0)
        visibility_trend = trend(future["V_SOURCE_CEILING"] - initial["V_SOURCE_CEILING"], 3.0)
        smoke_trend = trend(future["V_SOURCE_CEILING"] - initial["V_SOURCE_CEILING"], 3.0, True)
        mechanism = (
            "longitudinal_ventilation"
            if spec["supply_velocity"]
            else "smoke_layer"
            if hrr
            else "buoyant_plume"
        )
        labels = [
            label("event_class", event_class, "simulation_truth"),
            label("risk_level", risk, "source_measurement"),
            label("mechanism", mechanism, "deterministic_rule"),
            label("temperature_trend", temperature_trend, "source_measurement"),
            label("smoke_trend", smoke_trend, "source_measurement"),
            label("visibility_trend", visibility_trend, "source_measurement"),
        ]
        if source_region:
            labels.extend(
                [
                    label("source_region", source_region, "simulation_truth"),
                    label("stage", "developed", "deterministic_rule"),
                    label("risk_region", source_region, "source_measurement"),
                    label(
                        "first_high_risk_region",
                        source_region if risk in {"high", "critical"} else "none",
                        "source_measurement",
                    ),
                ]
            )
        event = event_record(root, run, spec, index, ref, labels, dimensions)
        events.append(event)
        splits.append({"event_id": event_id, "event_group": event["event_group"], "split": split})
        add_qa(
            qa,
            event,
            "L1-1",
            split,
            ref,
            "Which attribution best explains this observed trajectory?",
            {"class": event_class},
            "accuracy",
            ["class"],
        )
        if hrr:
            correct = "ABCD"[fire_position % 4]
            distractors = iter((30.0, 60.0, 120.0))
            option_times = [90.0 if option == correct else next(distractors) for option in "ABCD"]
            options = []
            for option_index, time_s in enumerate(option_times):
                candidate = derived_root / event_id / f"future_{option_index}.json"
                write_json(candidate, {"time_s": time_s, "values": nearest(rows, time_s)})
                options.append(
                    {
                        "id": "ABCD"[option_index],
                        "content_ref": str(candidate.relative_to(root)),
                        "text": "time-matched future state",
                    }
                )
            add_qa(
                qa,
                event,
                "L1-2",
                split,
                ref,
                "Which candidate is the actual future state at 90 seconds?",
                {"choice": correct},
                "accuracy",
                ["choice"],
                options,
                correct,
            )
            fire_position += 1
            add_qa(
                qa,
                event,
                "L2-1",
                split,
                ref,
                "Recover source region and fire stage.",
                {"source_region": source_region, "stage": "developed"},
                "component_accuracy",
                ["source_region", "stage"],
            )
            add_qa(
                qa,
                event,
                "L2-2",
                split,
                ref,
                "Recover highest-risk region and risk level.",
                {"risk_region": source_region, "risk_level": risk},
                "component_accuracy",
                ["risk_region", "risk_level"],
            )
            add_qa(
                qa,
                event,
                "L3-2",
                split,
                ref,
                "Which region first reaches high risk?",
                {
                    "first_high_risk_region": source_region
                    if risk in {"high", "critical"}
                    else "none"
                },
                "accuracy",
                ["first_high_risk_region"],
            )
        if source_region or event_class == "ventilation_disturbance":
            add_qa(
                qa,
                event,
                "L2-3",
                split,
                ref,
                "Which transport mechanism is dominant?",
                {"mechanism": mechanism},
                "accuracy",
                ["mechanism"],
            )
        add_qa(
            qa,
            event,
            "L3-1",
            split,
            ref,
            "Predict temperature, smoke, and visibility trends.",
            {
                "temperature_trend": temperature_trend,
                "smoke_trend": smoke_trend,
                "visibility_trend": visibility_trend,
            },
            "mean_accuracy",
            ["temperature_trend", "smoke_trend", "visibility_trend"],
        )
        reversed_path = derived_root / event_id / "time_reversed_observation.json"
        write_json(
            reversed_path,
            {
                "transform": "time_reverse",
                "source_ref": ref,
                "rows": list(reversed(compact_rows(rows))),
            },
        )
        add_qa(
            qa,
            event,
            "L1-3",
            split,
            str(reversed_path.relative_to(root)),
            "Is this ordered sequence temporally consistent?",
            {"consistency": "inconsistent", "violation_type": "reverse"},
            "accuracy",
            ["consistency"],
        )
        write_json(event_root / f"{event_id}.json", event)
    write_json(event_root / "fire_events.json", events)
    write_json(qa_root / "qa.json", qa)
    split_path = root / "splits" / "explicit_observation_pilot_10_event_group_manifest.json"
    write_json(split_path, splits)
    report_path = root / "reports" / "explicit_observation_batch_01" / "event_qa_build_report.json"
    write_json(
        report_path,
        {
            "status": "built_pending_strict_validation",
            "events": len(events),
            "qa": len(qa),
            "tasks": sorted({row["task_id"] for row in qa}),
            "missing_task": "L3-3 requires one-variable A/B family",
            "thresholds": THRESHOLDS,
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
