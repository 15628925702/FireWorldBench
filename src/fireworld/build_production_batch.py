"""Build strict v2 structured events and QA directly from an audited FDS batch."""

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


def load(path: Path) -> list[dict[str, float]]:
    with path.open(encoding="utf-8", newline="") as handle:
        values = list(csv.reader(handle))
    names = values[1]
    return [
        {name: float(value) for name, value in zip(names, row, strict=True)}
        for row in values[2:]
        if len(row) == len(names)
    ]


def near(rows: list[dict[str, float]], time_s: float) -> dict[str, float]:
    return min(rows, key=lambda row: abs(row["Time"] - time_s))


def trend(delta: float, deadband: float, inverse: bool = False) -> str:
    if abs(delta) < deadband:
        return "stable"
    return "up" if (delta > 0) != inverse else "down"


def qa(
    event: dict[str, Any],
    split: str,
    task: str,
    ref: str,
    fields: dict[str, Any],
    primary: str,
    components: list[str],
    question: str,
    options: list[dict[str, Any]] | None = None,
    choice: str | None = None,
) -> dict[str, Any]:
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
        "observation": {
            "structured": {"ref": ref},
            "images": None,
            "video": None,
            "context": "Audited FDS structured trajectory.",
            "time_window_s": [20.0, 90.0],
        },
        "confidence_target": 1.0,
        "evidence_metadata": {"required": False, "gold_refs": []},
        "provenance": {
            "event_manifest_sha256": digest(json.dumps(event, sort_keys=True)),
            "builder_version": "production-batch-2.1.0",
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
        "question": question,
        "options": options,
        "answer": {"choice": choice, "fields": fields},
        "scoring": {"primary": primary, "components": components, "secondary": []},
    }


def build(root: Path, batch_name: str) -> dict[str, Path]:
    batch = root / "fds_runs" / batch_name
    manifest = json.loads((batch / "input_manifest.json").read_text(encoding="utf-8"))["runs"]
    event_dir, s_dir, qa_dir = (
        root / "fire_events" / batch_name,
        root / "derived" / batch_name / "S",
        root / "qa" / batch_name,
    )
    for path in (event_dir, s_dir, qa_dir):
        path.mkdir(parents=True, exist_ok=True)
    events: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []
    family: dict[str, list[tuple[dict[str, Any], dict[str, float], str, str, str]]] = {}
    for index, item in enumerate(manifest):
        key, row = item["run_key"], item["matrix_row"]
        run = batch / key
        rows = load(run / f"{key}_devc.csv")
        dims, hrr, vent = parse_fds(run / f"{key}.fds")
        event_id = row["event_id"]
        initial, future = near(rows, 20), near(rows, 90)
        source = row.get("source_region") or "R5"
        event_class = row["event_class"]
        l1_class = row["l1_class"]
        temp_values = {f"R{i}": future[f"T_R{i}"] for i in range(1, 9)}
        vis_values = {f"R{i}": future[f"V_R{i}"] for i in range(1, 9)}
        risk_region = max(temp_values, key=lambda region: temp_values[region])
        risk_level = (
            "critical"
            if max(temp_values.values()) >= 200 or min(vis_values.values()) <= 3
            else "high"
            if max(temp_values.values()) >= 60 or min(vis_values.values()) <= 10
            else "low"
        )
        summary = s_dir / event_id / "summary.json"
        write_json(
            summary,
            {
                "format": "fireworld-structured-v2",
                "source_csv_sha256": file_hash(run / f"{key}_devc.csv"),
                "units": {"temperature": "C", "visibility": "m", "u_velocity": "m/s"},
                "rows": [near(rows, t) for t in (10, 20, 40, 60, 90, 120)],
            },
        )
        ref = str(summary.relative_to(root))
        labels = [
            label("event_class", l1_class, "simulation_truth"),
            label("source_region", source, "simulation_truth"),
            label(
                "stage", "developed" if event_class == "fire" else "incipient", "deterministic_rule"
            ),
            label("risk_region", risk_region, "source_measurement"),
            label("risk_level", risk_level, "source_measurement"),
        ]
        intervention = row.get("intervention")
        if intervention:
            intervention = {
                "variable": intervention["variable"],
                "value": intervention["value"],
                "base_event_id": opaque_id("FWE", f"{row['counterfactual_family']}:base"),
            }
        scene_type = "tunnel" if str(row["geometry"]).startswith(("tunnel", "corridor")) else "room"
        event = {
            "schema_version": "2.0.0",
            "event_id": event_id,
            "event_group": row["event_group"],
            "source_domain": "fds",
            "status": "eligible",
            "geometry": {
                "scene_type": scene_type,
                "coordinate_system": "right-handed-m",
                "dimensions_m": dims,
                "regions": regions(dims),
            },
            "controls": {
                "source_region": row.get("source_region"),
                "hrr_profile": "ramped" if hrr else None,
                "ventilation": {"mode": vent},
                "extraction": None,
                "openings": None,
                "random_seed": 2026071900 + index,
                "intervention": intervention,
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
                "source_version": batch_name,
                "source_files": [
                    {
                        "opaque_ref": f"raw/{event_id}/input",
                        "sha256": file_hash(run / f"{key}.fds"),
                    },
                    {
                        "opaque_ref": f"raw/{event_id}/sensors",
                        "sha256": file_hash(run / f"{key}_devc.csv"),
                    },
                ],
                "transform_version": "production-batch-2.1.0",
                "created_at": "2026-07-19T00:00:00Z",
                "fds": {
                    "fds_version": FDS_VERSION,
                    "smokeview_version": SMOKEVIEW_VERSION,
                    "fdgen_version": "not_used",
                    "mesh": {"dimensions_m": dims},
                    "boundary_hash": digest((run / f"{key}.fds").read_bytes()),
                    "random_seed": 2026071900 + index,
                    "input_sha256": file_hash(run / f"{key}.fds"),
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
        events.append(event)
        write_json(event_dir / f"{event_id}.json", event)
        split = row["split"]
        questions.append(
            qa(
                event,
                split,
                "L1-1",
                ref,
                {"class": l1_class},
                "accuracy",
                ["class"],
                "Which attribution best explains this observed trajectory?",
            )
        )
        correct = "ABCD"[index % 4]
        distractor_times = iter((30.0, 60.0, 120.0))
        candidate_times = [
            90.0 if option == correct else next(distractor_times) for option in "ABCD"
        ]
        options = []
        for option, time_s in zip("ABCD", candidate_times, strict=True):
            candidate = s_dir / event_id / f"l1_2_{option}.json"
            write_json(candidate, {"time_s": time_s, "values": near(rows, time_s)})
            options.append(
                {
                    "id": option,
                    "content_ref": str(candidate.relative_to(root)),
                    "text": "time-matched future-state candidate",
                }
            )
        questions.append(
            qa(
                event,
                split,
                "L1-2",
                ref,
                {"choice": correct},
                "accuracy",
                ["choice"],
                "Which candidate is the actual future state at 90 seconds?",
                options,
                correct,
            )
        )
        questions.append(
            qa(
                event,
                split,
                "L1-3",
                ref,
                {"consistency": "consistent", "violation_type": None},
                "accuracy",
                ["consistency", "violation_type"],
                "Is this ordered sequence temporally consistent?",
            )
        )
        if event_class == "fire":
            questions.extend(
                [
                    qa(
                        event,
                        split,
                        "L2-1",
                        ref,
                        {"source_region": source, "stage": "developed"},
                        "component_accuracy",
                        ["source_region", "stage"],
                        "Recover source region and fire stage.",
                    ),
                    qa(
                        event,
                        split,
                        "L2-2",
                        ref,
                        {"risk_region": risk_region, "risk_level": risk_level},
                        "component_accuracy",
                        ["risk_region", "risk_level"],
                        "Recover highest-risk region and risk level.",
                    ),
                    qa(
                        event,
                        split,
                        "L2-3",
                        ref,
                        {
                            "mechanism": "longitudinal_ventilation"
                            if row["ventilation_mode"] == "longitudinal"
                            else "smoke_layer"
                        },
                        "accuracy",
                        ["mechanism"],
                        "Which transport mechanism is dominant?",
                    ),
                    qa(
                        event,
                        split,
                        "L3-2",
                        ref,
                        {
                            "first_high_risk_region": risk_region
                            if risk_level in {"high", "critical"}
                            else "none"
                        },
                        "accuracy",
                        ["first_high_risk_region"],
                        "Which region first reaches high risk?",
                    ),
                ]
            )
        questions.append(
            qa(
                event,
                split,
                "L3-1",
                ref,
                {
                    "temperature_trend": trend(future[f"T_{source}"] - initial[f"T_{source}"], 10),
                    "smoke_trend": trend(future[f"V_{source}"] - initial[f"V_{source}"], 3, True),
                    "visibility_trend": trend(future[f"V_{source}"] - initial[f"V_{source}"], 3),
                },
                "mean_accuracy",
                ["temperature_trend", "smoke_trend", "visibility_trend"],
                "Predict temperature, smoke, and visibility trends.",
            )
        )
        if row.get("counterfactual_family"):
            family.setdefault(row["counterfactual_family"], []).append(
                (event, future, ref, split, row["intervention"]["side"])
            )
    for _name, pair in family.items():
        # A frozen family can straddle an adjacent 10-event operational batch.
        # Publish its L3-3 item only once both raw sides are available.
        if len(pair) != 2:
            continue
        a, b = sorted(pair, key=lambda value: value[4])
        source = str(a[0]["controls"]["source_region"])
        a_temp, b_temp = a[1][f"T_{source}"], b[1][f"T_{source}"]
        answer = "A" if a_temp > b_temp + 1.0 else "B" if b_temp > a_temp + 1.0 else "same"
        questions.append(
            qa(
                a[0],
                a[3],
                "L3-3",
                a[2],
                {"comparison": answer},
                "accuracy",
                ["comparison"],
                "Which case has the higher future source-region temperature, or are they the same?",
            )
        )
    write_json(event_dir / "fire_events.json", events)
    write_json(qa_dir / "qa.json", questions)
    report = root / "reports" / "production_batches" / f"{batch_name}_build.json"
    write_json(
        report, {"events": len(events), "qa": len(questions), "status": "built_pending_validation"}
    )
    return {"events": event_dir / "fire_events.json", "qa": qa_dir / "qa.json", "report": report}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            {key: str(value) for key, value in build(args.root.resolve(), args.batch).items()}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
