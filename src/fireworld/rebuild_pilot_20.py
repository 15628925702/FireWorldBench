"""Rebuild the original twenty FDS pilot runs without trusting legacy outputs.

This is deliberately fail-closed: it records events and usable evidence, then
refuses task labels whose required physical signal is absent.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from fireworld.mini_pilot import (
    FDS_VERSION,
    SMOKEVIEW_VERSION,
    digest,
    file_hash,
    hrr_label,
    label,
    load_devc,
    make_summary,
    opaque_id,
    parse_fds,
    regions,
    smoke_files,
    write_json,
)

THRESHOLDS: Final[dict[str, float | str]] = {
    "version": "pilot-v2.1-frozen",
    "temperature_high_c": 60.0,
    "visibility_high_risk_m": 10.0,
    "temperature_trend_deadband_c": 2.0,
    "visibility_trend_deadband_m": 1.0,
    "rationale": "Frozen before labels; labels require measured threshold crossing.",
}


def event_kind(index: int) -> str:
    if index <= 14:
        return "fire"
    if index <= 16:
        return "no_fire"
    if index <= 18:
        return "ventilation_disturbance"
    return "no_fire"  # Non-fire hard negatives use the fixed L1-1 ontology.


def render_dynamic_images(
    root: Path, run: Path, event_id: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Render loaded Smoke3D fields before setting time, then reject static output."""
    output = root / "derived" / "pilot_20_v2_1" / "I" / event_id
    output.mkdir(parents=True, exist_ok=True)
    soot, temperature = smoke_files(run)
    ssf = output / "render.ssf"
    lines = [
        "RENDERDIR",
        f" {output}",
        "RENDERTYPE",
        " PNG",
        "UNLOADALL",
        "LOADFILE",
        f" {soot}",
        "LOADFILE",
        f" {temperature}",
    ]
    for time_s in (10, 30, 60, 90):
        lines.extend(
            ["SETTIMEVAL", f" {time_s}.0", "RENDERONCE", f"{event_id.lower()}_t{time_s:03d}"]
        )
    ssf.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for image in output.glob("*.png"):
        image.unlink()
    command = [
        "/usr/bin/timeout",
        "180",
        "/root/FDS/FDS6/smvbin/smokeview",
        str(next(run.glob("*.smv")).with_suffix("")),
        "-script",
        str(ssf),
        "-render_overwrite",
    ]
    result = subprocess.run(
        command,
        cwd=run,
        env={**os.environ, "DISPLAY": ":99", "LIBGL_ALWAYS_SOFTWARE": "1"},
        text=True,
        capture_output=True,
        check=False,
    )
    log = output / "render.log"
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    lower = log.read_text(encoding="utf-8", errors="replace").lower()
    images = []
    for time_s in (10, 30, 60, 90):
        image = output / f"{event_id.lower()}_t{time_s:03d}.png"
        images.append(
            {"ref": str(image.relative_to(root)), "time_s": time_s, "sha256": file_hash(image)}
        )
    checks: dict[str, Any] = {
        "returncode": result.returncode,
        "global_times_error": "global_times" in lower,
        "load_error": "error" in lower and "loading file" not in lower,
        "unique_hash_count": len({row["sha256"] for row in images}),
        "log": str(log.relative_to(root)),
    }
    checks["pass"] = (
        checks["returncode"] == 0
        and not checks["global_times_error"]
        and not checks["load_error"]
        and checks["unique_hash_count"] > 1
    )
    if not checks["pass"]:
        raise RuntimeError(f"dynamic visual gate failed for {event_id}: {checks}")
    return images, checks


def build(root: Path, render_images: bool = False) -> dict[str, Path]:
    event_root = root / "fire_events" / "pilot_20_v2_1"
    derived = root / "derived" / "pilot_20_v2_1" / "S"
    report_root = root / "reports" / "pilot_20_v2_1"
    for directory in (event_root, derived, report_root, root / "qa", root / "splits"):
        directory.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    events: list[dict[str, Any]] = []
    visual_checks: dict[str, Any] = {}
    task_eligibility: dict[str, list[dict[str, Any]]] = {
        task: []
        for task in ("L1-1", "L1-2", "L1-3", "L2-1", "L2-2", "L2-3", "L3-1", "L3-2", "L3-3")
    }
    for index in range(1, 21):
        key = f"pilot_{index:02d}"
        run = root / "fds_runs" / "pilot" / key
        fds = run / f"{key}.fds"
        devc = run / f"{key}_devc.csv"
        out = run / f"{key}.out"
        dimensions, hrr, ventilation = parse_fds(fds)
        rows = load_devc(devc)
        event_id = opaque_id("FWE", f"pilot-20-v2.1:{key}")
        summary_path = derived / event_id / "summary.json"
        write_json(summary_path, make_summary(rows, devc))
        temperatures = [
            value for row in rows for name, value in row.items() if name.startswith("T_")
        ]
        visibilities = [
            value for row in rows for name, value in row.items() if name.startswith("V_")
        ]
        temp_span = max(temperatures) - min(temperatures)
        vis_span = max(visibilities) - min(visibilities)
        max_temp, min_vis = max(temperatures), min(visibilities)
        kind = event_kind(index)
        source = f"R{((index - 1) % 4) + 1}" if hrr > 0 else None
        profile, stage = hrr_label(hrr)
        labels = [
            label("event_class", kind, "simulation_truth"),
            label("hrrpua", hrr, "simulation_truth"),
        ]
        if source:
            labels += [
                label("source_region", source, "simulation_truth"),
                label("stage", stage, "simulation_truth"),
            ]
        event: dict[str, Any] = {
            "schema_version": "2.0.0",
            "event_id": event_id,
            "event_group": opaque_id("FWG", f"pilot-20-v2.1:{key}"),
            "source_domain": "fds",
            "status": "eligible",
            "geometry": {
                "scene_type": "tunnel",
                "coordinate_system": "right-handed-m",
                "dimensions_m": dimensions,
                "regions": regions(dimensions),
            },
            "controls": {
                "source_region": source,
                "hrr_profile": profile,
                "ventilation": {"mode": ventilation},
                "extraction": None,
                "openings": None,
                "random_seed": 20260717 + index,
                "intervention": None,
            },
            "timeline": {"start_s": 0.0, "end_s": 90.0, "sample_interval_s": 1.0},
            "observations": {
                "structured": {
                    "ref": str(summary_path.relative_to(root)),
                    "format": "json",
                    "variables": ["temperature", "visibility"],
                    "units_normalized": True,
                },
                "images": None,
                "video": None,
            },
            "ground_truth": {"labels": labels},
            "provenance": {
                "source_version": "audited-raw-fds-pilot",
                "source_files": [
                    {"opaque_ref": f"raw/{event_id}/input", "sha256": file_hash(fds)},
                    {"opaque_ref": f"raw/{event_id}/sensors", "sha256": file_hash(devc)},
                ],
                "transform_version": "pilot-20-rebuild-2.1.0",
                "created_at": now,
                "fds": {
                    "fds_version": FDS_VERSION,
                    "smokeview_version": SMOKEVIEW_VERSION,
                    "fdgen_version": "not_used",
                    "mesh": {"dimensions_m": dimensions},
                    "boundary_hash": digest(fds.read_bytes()),
                    "random_seed": 20260717 + index,
                    "input_sha256": file_hash(fds),
                    "log_ref": str(out.relative_to(root)),
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
        if render_images and hrr > 0:
            images, checks = render_dynamic_images(root, run, event_id)
            event["observations"]["images"] = images
            visual_checks[event_id] = checks
        events.append(event)
        task_eligibility["L1-1"].append(
            {"event_id": event_id, "eligible": True, "reason": "FDS truth class"}
        )
        temp_deadband = float(THRESHOLDS["temperature_trend_deadband_c"])
        visibility_deadband = float(THRESHOLDS["visibility_trend_deadband_m"])
        task_eligibility["L1-2"].append(
            {
                "event_id": event_id,
                "eligible": temp_span >= temp_deadband or vis_span >= visibility_deadband,
                "reason": "requires non-static future state",
            }
        )
        task_eligibility["L1-3"].append(
            {
                "event_id": event_id,
                "eligible": False,
                "reason": "no independently generated violation observation",
            }
        )
        task_eligibility["L2-1"].append(
            {"event_id": event_id, "eligible": hrr > 0, "reason": "source and stage from FDS input"}
        )
        risk_ok = max_temp >= float(THRESHOLDS["temperature_high_c"]) or min_vis <= float(
            THRESHOLDS["visibility_high_risk_m"]
        )
        for task in ("L2-2", "L3-2"):
            task_eligibility[task].append(
                {
                    "event_id": event_id,
                    "eligible": risk_ok,
                    "reason": "requires measured high-risk threshold crossing",
                }
            )
        task_eligibility["L2-3"].append(
            {
                "event_id": event_id,
                "eligible": False,
                "reason": "device CSV cannot establish one of six mechanisms",
            }
        )
        task_eligibility["L3-1"].append(
            {
                "event_id": event_id,
                "eligible": temp_span >= temp_deadband and vis_span >= visibility_deadband,
                "reason": "requires all three measured trends",
            }
        )
        task_eligibility["L3-3"].append(
            {
                "event_id": event_id,
                "eligible": False,
                "reason": "requires declared A/B family; stored separately",
            }
        )
        write_json(event_root / f"{event_id}.json", event)
    write_json(event_root / "fire_events.json", events)
    split_rows = [
        {
            "event_id": event["event_id"],
            "event_group": event["event_group"],
            "split": "train" if n < 12 else "dev" if n < 16 else "test_iid",
        }
        for n, event in enumerate(events)
    ]
    split_path = root / "splits" / "pilot_20_v2_1_event_group_manifest.json"
    write_json(split_path, split_rows)
    report = {
        "status": "rebuilt_pending_visual_and_qa_gates",
        "independent_events": 20,
        "task_thresholds": THRESHOLDS,
        "task_eligibility": task_eligibility,
        "eligible_counts": {
            task: sum(row["eligible"] for row in checks)
            for task, checks in task_eligibility.items()
        },
        "data_limitation": (
            "No raw pilot device trajectory crosses risk thresholds; "
            "no full nine-task gold QA is emitted."
        ),
        "visual_checks": visual_checks,
        "source": "raw FDS and device CSV, with Smoke3D when --render-images is set",
    }
    report_path = report_root / "pilot_20_rebuild_audit.json"
    write_json(report_path, report)
    return {"events": event_root / "fire_events.json", "split": split_path, "report": report_path}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--render-images", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            {
                key: str(value)
                for key, value in build(args.root.resolve(), args.render_images).items()
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
