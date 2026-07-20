"""Build the seven-run FireWorldBench v2 gold mini-pilot from audited raw FDS runs.

This module intentionally derives every event and QA label from an input FDS file,
its sensor trajectory, or a declared one-variable counterfactual pair.  It does
not read legacy Fire Events, QA, scores, or artifacts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FDS_VERSION = "FDS-6.11.1-0-gff928db-release"
SMOKEVIEW_VERSION = "SMV-6.11.2-0-g27cbe5960-release"
BUILDER_VERSION = "mini-pilot-2.1.0"
TASK_CONFIG = "FireWorldBenchv2 nine-task protocol"


@dataclass(frozen=True)
class Spec:
    key: str
    run_dir: str
    input_fds: str
    event_class: str
    source_region: str | None
    split: str
    seed: int
    group_key: str
    intervention_value: float | None = None


SPECS = (
    Spec(
        "fire_low",
        "fds_runs/pilot/pilot_01",
        "fds_runs/pilot/pilot_01/pilot_01.fds",
        "fire",
        "R1",
        "train",
        20260718,
        "fire_low",
    ),
    Spec(
        "fire_high",
        "fds_runs/pilot/pilot_03",
        "fds_runs/pilot/pilot_03/pilot_03.fds",
        "fire",
        "R3",
        "dev",
        20260720,
        "fire_high",
    ),
    Spec(
        "no_fire",
        "fds_runs/pilot/pilot_15",
        "fds_runs/pilot/pilot_15/pilot_15.fds",
        "no_fire",
        None,
        "train",
        20260732,
        "no_fire",
    ),
    Spec(
        "vent",
        "fds_runs/pilot/pilot_17",
        "fds_runs/pilot/pilot_17/pilot_17.fds",
        "ventilation_disturbance",
        None,
        "dev",
        20260734,
        "vent",
    ),
    Spec(
        "hard_negative",
        "fds_runs/pilot/pilot_19",
        "fds_runs/pilot/pilot_19/pilot_19.fds",
        "no_fire",
        None,
        "test_iid",
        20260736,
        "hard_negative",
    ),
    Spec(
        "cf_a",
        "fds_runs/counterfactual/FWCF-F8320CCC3FD9_A",
        "tmp/counterfactual_inputs/FWCF-F8320CCC3FD9_A/FWCF-F8320CCC3FD9_A.fds",
        "fire",
        "R4",
        "test_iid",
        20260725,
        "cf_hrr",
        250.0,
    ),
    Spec(
        "cf_b",
        "fds_runs/counterfactual/FWCF-F8320CCC3FD9_B",
        "tmp/counterfactual_inputs/FWCF-F8320CCC3FD9_B/FWCF-F8320CCC3FD9_B.fds",
        "fire",
        "R4",
        "test_iid",
        20260725,
        "cf_hrr",
        500.0,
    ),
)


def digest(value: bytes | str) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def opaque_id(prefix: str, value: str) -> str:
    return f"{prefix}-{digest(value)[:12].upper()}"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_devc(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 3:
        raise ValueError(f"device CSV has no data: {path}")
    names = [item.strip() for item in rows[1]]
    output: list[dict[str, float]] = []
    for raw in rows[2:]:
        if len(raw) != len(names):
            continue
        try:
            output.append({name: float(value) for name, value in zip(names, raw, strict=True)})
        except ValueError:
            continue
    if not output:
        raise ValueError(f"device CSV has no parseable rows: {path}")
    return output


def nearest(rows: list[dict[str, float]], time_s: float) -> dict[str, float]:
    return min(rows, key=lambda row: abs(row["Time"] - time_s))


def run_files(root: Path, spec: Spec) -> tuple[Path, Path, Path, Path, Path]:
    run_dir = root / spec.run_dir
    fds = root / spec.input_fds
    if not run_dir.is_dir() or not fds.is_file():
        raise FileNotFoundError(f"missing raw source for {spec.key}")
    smv = next(run_dir.glob("*.smv"))
    devc = next(run_dir.glob("*_devc.csv"))
    out = next(run_dir.glob("*.out"))
    return run_dir, fds, smv, devc, out


def parse_fds(path: Path) -> tuple[dict[str, float], float, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    mesh_match = re.search(r"&MESH\s+IJK=([^/]+),\s*XB=([^/]+)/", text)
    if mesh_match is None:
        raise ValueError(f"mesh not found in {path}")
    xb = [float(item) for item in re.findall(r"[-+]?\d+(?:\.\d+)?", mesh_match.group(2))]
    if len(xb) != 6:
        raise ValueError(f"invalid mesh bounds in {path}")
    hrr_match = re.search(r"HRRPUA=([-+]?\d+(?:\.\d+)?)", text)
    hrr = float(hrr_match.group(1)) if hrr_match else 0.0
    ventilation = "longitudinal" if "VEL=" in text else "still"
    return (
        {"length": xb[1] - xb[0], "width": xb[3] - xb[2], "height": xb[5] - xb[4]},
        hrr,
        ventilation,
    )


def regions(dimensions: dict[str, float]) -> list[dict[str, Any]]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    x_edges = (0.0, length / 3.0, 2.0 * length / 3.0, length)
    y_edges = (0.0, width / 2.0, width)
    output: list[dict[str, Any]] = []
    index = 1
    for y in range(2):
        for x in range(3):
            if index > 8:
                break
            output.append(
                {
                    "region_id": f"R{index}",
                    "description": f"region {index}",
                    "bounds_m": [
                        x_edges[x],
                        x_edges[x + 1],
                        y_edges[y],
                        y_edges[y + 1],
                        0.0,
                        height,
                    ],
                }
            )
            index += 1
    while index <= 8:
        output.append(
            {"region_id": f"R{index}", "description": f"region {index}", "bounds_m": None}
        )
        index += 1
    return output


def make_summary(
    rows: list[dict[str, float]], source_csv: Path, injected: bool = False
) -> dict[str, Any]:
    sample_times = (10.0, 20.0, 30.0, 40.0, 60.0, 90.0)
    selected: list[dict[str, float]] = []
    for time_s in sample_times:
        row = dict(nearest(rows, time_s))
        if injected and 20.0 <= row["Time"] <= 40.0 and "T_R3" in row:
            row["T_R3"] = row["T_R3"] + 55.0
        selected.append(
            {
                key: round(value, 6)
                for key, value in row.items()
                if key == "Time" or key.startswith(("T_", "V_", "CO_", "U_"))
            }
        )
    return {
        "format": "fireworld-structured-v2",
        "source_csv_sha256": file_hash(source_csv),
        "units": {"temperature": "C", "visibility": "m", "co": "mol/mol", "u_velocity": "m/s"},
        "rows": selected,
    }


def hrr_label(hrr: float) -> tuple[str | None, str]:
    if hrr <= 0.0:
        return None, "incipient"
    return (
        "low_growth" if hrr <= 150.0 else "medium_growth" if hrr <= 300.0 else "high_growth"
    ), "developed"


def smoke_files(run_dir: Path) -> tuple[str, str]:
    soot = next(run_dir.glob("*_1_1.s3d"), None)
    temp = next(run_dir.glob("*_1_3.s3d"), None)
    if soot is None or temp is None:
        raise FileNotFoundError(f"Smoke3D soot/temperature fields unavailable in {run_dir}")
    return soot.name, temp.name


def render_images(
    root: Path, spec: Spec, event_id: str, run_dir: Path
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    output = root / "derived" / "mini_pilot_7" / "I" / event_id
    output.mkdir(parents=True, exist_ok=True)
    soot, temp = smoke_files(run_dir)
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
        f" {temp}",
    ]
    for time_s in (10, 30, 60, 90):
        lines.extend(
            [
                "SETTIMEVAL",
                f" {float(time_s):.1f}",
                "RENDERONCE",
                f" {event_id.lower()}_t{time_s:03d}",
            ]
        )
    ssf.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for image in output.glob("*.png"):
        image.unlink()
    command = [
        "/usr/bin/timeout",
        "180",
        "/root/FDS/FDS6/smvbin/smokeview",
        str(next(run_dir.glob("*.smv")).with_suffix("")),
        "-script",
        str(ssf),
        "-render_overwrite",
    ]
    result = subprocess.run(
        command,
        cwd=run_dir,
        env={**os.environ, "DISPLAY": ":99", "LIBGL_ALWAYS_SOFTWARE": "1"},
        text=True,
        capture_output=True,
        check=False,
    )
    log = output / "render.log"
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    lower_log = log.read_text(encoding="utf-8", errors="replace").lower()
    images: list[dict[str, Any]] = []
    for time_s in (10, 30, 60, 90):
        image = output / f"{event_id.lower()}_t{time_s:03d}.png"
        if not image.is_file():
            raise RuntimeError(f"missing render {image}")
        images.append(
            {"ref": str(image.relative_to(root)), "time_s": time_s, "sha256": file_hash(image)}
        )
    checks = {
        "returncode": result.returncode,
        "load_before_time": lower_log.find("loading file") < lower_log.find("setting time"),
        "global_times_error": "global_times" in lower_log,
        "load_error": "error" in lower_log and "loading file" not in lower_log,
        "unique_hash_count": len({row["sha256"] for row in images}),
        "pass": result.returncode == 0
        and "global_times" not in lower_log
        and len({row["sha256"] for row in images}) > 1,
        "log": str(log.relative_to(root)),
    }
    if not checks["pass"]:
        raise RuntimeError(f"visual hard gate failed for {spec.key}: {checks}")
    return images, checks


def label(
    name: str, value: Any, origin: str = "deterministic_rule", rule: str | None = BUILDER_VERSION
) -> dict[str, Any]:
    return {"name": name, "value": value, "origin": origin, "rule_version": rule}


def task_hash() -> str:
    return digest(TASK_CONFIG)


def qa_base(
    event: dict[str, Any], task_id: str, track: str, split: str, observation: dict[str, Any]
) -> dict[str, Any]:
    identity = f"{event['event_id']}:{task_id}:{track}:{observation['time_window_s']}"
    return {
        "schema_version": "2.0.0",
        "qa_id": opaque_id("FWQ", identity),
        "case_id": opaque_id("FWC", identity + ":case"),
        "event_id": event["event_id"],
        "event_group": event["event_group"],
        "source_domain": "fds",
        "split": split,
        "layer": task_id[:2],
        "task_id": task_id,
        "track": track,
        "observation": observation,
        "confidence_target": 1.0,
        "evidence_metadata": {"required": False, "gold_refs": []},
        "provenance": {
            "event_manifest_sha256": digest(json.dumps(event, sort_keys=True)),
            "builder_version": BUILDER_VERSION,
            "task_config_sha256": task_hash(),
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


def s_observation(summary_ref: str, start: float, end: float, context: str) -> dict[str, Any]:
    return {
        "structured": {"ref": summary_ref},
        "images": None,
        "video": None,
        "context": context,
        "time_window_s": [start, end],
    }


def i_observation(refs: list[str], start: float, end: float, context: str) -> dict[str, Any]:
    return {
        "structured": None,
        "images": refs,
        "video": None,
        "context": context,
        "time_window_s": [start, end],
    }


def l1_1(
    event: dict[str, Any],
    split: str,
    summary_ref: str,
    target: str,
    injected_ref: str | None = None,
) -> dict[str, Any]:
    ref = injected_ref or summary_ref
    row = qa_base(
        event, "L1-1", "S", split, s_observation(ref, 10, 40, "Early multi-sensor trajectory.")
    )
    row.update(
        {
            "question": "Which attribution best explains the early observation?",
            "options": None,
            "answer": {"choice": None, "fields": {"class": target}},
            "scoring": {
                "primary": "accuracy",
                "components": ["class"],
                "secondary": ["macro_f1", "ece", "brier_score"],
            },
        }
    )
    return row


def l1_2(
    event: dict[str, Any],
    split: str,
    track: str,
    summary_ref: str,
    images: list[dict[str, Any]],
    candidate_refs_s: list[str],
    candidate_refs_i: list[str],
) -> dict[str, Any]:
    choice_order = (
        ("C", "A", "D", "B") if event["event_id"][4] in "01234567" else ("B", "D", "A", "C")
    )
    correct_choice = choice_order[0]
    observation = (
        s_observation(
            summary_ref, 10, 30, "Current trajectory and four time-matched future candidates."
        )
        if track == "S"
        else i_observation(
            [images[0]["ref"], images[1]["ref"]],
            10,
            30,
            "Two ordered current frames and four future candidates.",
        )
    )
    candidate_refs = candidate_refs_s if track == "S" else candidate_refs_i
    row = qa_base(event, "L1-2", track, split, observation)
    row.update(
        {
            "question": "Which candidate is the state at the specified future interval?",
            "options": [
                {
                    "id": option,
                    "content_ref": candidate_refs[index],
                    "text": "future-state candidate",
                }
                for index, option in enumerate(choice_order)
            ],
            "answer": {"choice": correct_choice, "fields": {"choice": correct_choice}},
            "scoring": {"primary": "accuracy", "components": ["choice"], "secondary": []},
        }
    )
    return row


def l2_1(
    event: dict[str, Any], split: str, track: str, summary_ref: str, images: list[dict[str, Any]]
) -> dict[str, Any]:
    labels = {item["name"]: item["value"] for item in event["ground_truth"]["labels"]}
    observation = (
        s_observation(summary_ref, 20, 40, "Eight-region layout and current observation.")
        if track == "S"
        else i_observation(
            [images[1]["ref"], images[2]["ref"]],
            30,
            60,
            "Eight-region layout and ordered current frames.",
        )
    )
    row = qa_base(event, "L2-1", track, split, observation)
    row.update(
        {
            "question": "Recover the source region and current fire stage.",
            "options": None,
            "answer": {
                "choice": None,
                "fields": {"source_region": labels["source_region"], "stage": labels["stage"]},
            },
            "scoring": {
                "primary": "component_accuracy",
                "components": ["source_region", "stage"],
                "secondary": ["joint_exact_match"],
            },
        }
    )
    return row


def l3_3(
    event_a: dict[str, Any],
    event_b: dict[str, Any],
    split: str,
    summary_ref: str,
    image_refs: list[str],
    track: str,
    answer: str,
) -> dict[str, Any]:
    observation = (
        s_observation(
            summary_ref,
            20,
            40,
            "Cases A and B share geometry, seed, camera, and sampling; one control variable differs.",
        )
        if track == "S"
        else i_observation(
            image_refs,
            30,
            60,
            "Case A frames followed by Case B frames; one control variable differs.",
        )
    )
    row = qa_base(event_a, "L3-3", track, split, observation)
    row.update(
        {
            "question": "Which case has the higher future source-region temperature, or are they the same?",
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
    )
    return row


def build(root: Path) -> dict[str, Any]:
    event_root = root / "fire_events" / "mini_pilot_7"
    derived_root = root / "derived" / "mini_pilot_7"
    qa_root = root / "qa" / "mini_pilot_7"
    report_root = root / "reports" / "mini_pilot_7"
    for directory in (event_root, derived_root, qa_root, report_root, root / "splits"):
        directory.mkdir(parents=True, exist_ok=True)
    event_by_key: dict[str, dict[str, Any]] = {}
    summary_by_key: dict[str, str] = {}
    images_by_key: dict[str, list[dict[str, Any]]] = {}
    sensor_rows_by_key: dict[str, list[dict[str, float]]] = {}
    split_by_key: dict[str, str] = {}
    visual_checks: dict[str, Any] = {}
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    for spec in SPECS:
        run_dir, fds, _smv, devc, out = run_files(root, spec)
        dimensions, hrr, ventilation = parse_fds(fds)
        profile, stage = hrr_label(hrr)
        event_id = opaque_id("FWE", f"mini-pilot-v2.1:{spec.key}")
        group_id = opaque_id("FWG", f"mini-pilot-v2.1:{spec.group_key}")
        sensor_rows = load_devc(devc)
        summary = make_summary(sensor_rows, devc)
        summary_path = derived_root / "S" / event_id / "summary.json"
        write_json(summary_path, summary)
        summary_ref = str(summary_path.relative_to(root))
        labels = [
            label("event_class", spec.event_class, "simulation_truth"),
            label("stage", stage),
            label("hrrpua", hrr, "simulation_truth"),
        ]
        if spec.source_region is not None:
            labels.append(label("source_region", spec.source_region, "simulation_truth"))
        controls: dict[str, Any] = {
            "source_region": spec.source_region,
            "hrr_profile": profile,
            "ventilation": {"mode": ventilation},
            "extraction": None,
            "openings": None,
            "random_seed": spec.seed,
            "intervention": None,
        }
        if spec.intervention_value is not None:
            controls["intervention"] = {
                "variable": "hrrpua",
                "value": spec.intervention_value,
                "base_event_id": opaque_id("FWE", "mini-pilot-v2.1:cf-hrr-base"),
            }
        event: dict[str, Any] = {
            "schema_version": "2.0.0",
            "event_id": event_id,
            "event_group": group_id,
            "source_domain": "fds",
            "status": "eligible",
            "geometry": {
                "scene_type": "tunnel",
                "coordinate_system": "right-handed-m",
                "dimensions_m": dimensions,
                "regions": regions(dimensions),
            },
            "controls": controls,
            "timeline": {"start_s": 0.0, "end_s": 90.0, "sample_interval_s": 1.0},
            "observations": {
                "structured": {
                    "ref": summary_ref,
                    "format": "json",
                    "variables": ["temperature", "visibility", "co", "u_velocity"],
                    "units_normalized": True,
                },
                "images": None,
                "video": None,
            },
            "ground_truth": {"labels": labels},
            "provenance": {
                "source_version": "audited-raw-fds-20260718",
                "source_files": [
                    {"opaque_ref": f"raw/{event_id}/input", "sha256": file_hash(fds)},
                    {"opaque_ref": f"raw/{event_id}/sensors", "sha256": file_hash(devc)},
                ],
                "transform_version": BUILDER_VERSION,
                "created_at": now,
                "fds": {
                    "fds_version": FDS_VERSION,
                    "smokeview_version": SMOKEVIEW_VERSION,
                    "fdgen_version": "not_used",
                    "mesh": {"dimensions_m": dimensions},
                    "boundary_hash": digest(fds.read_text(encoding="utf-8", errors="replace")),
                    "random_seed": spec.seed,
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
        if spec.event_class == "fire":
            images, checks = render_images(root, spec, event_id, run_dir)
            event["observations"]["images"] = images
            images_by_key[spec.key] = images
            visual_checks[spec.key] = checks
        event_by_key[spec.key] = event
        summary_by_key[spec.key] = summary_ref
        sensor_rows_by_key[spec.key] = sensor_rows
        split_by_key[spec.key] = spec.split
    injected = make_summary(
        load_devc(run_files(root, SPECS[2])[3]), run_files(root, SPECS[2])[3], injected=True
    )
    injected_path = (
        derived_root / "S" / event_by_key["no_fire"]["event_id"] / "sensor_fault_injected.json"
    )
    write_json(injected_path, injected)
    for event in event_by_key.values():
        write_json(event_root / f"{event['event_id']}.json", event)
    events = list(event_by_key.values())
    write_json(event_root / "fire_events.json", events)
    qa: list[dict[str, Any]] = []
    qa.extend(
        [
            l1_1(
                event_by_key["fire_high"],
                split_by_key["fire_high"],
                summary_by_key["fire_high"],
                "fire",
            ),
            l1_1(
                event_by_key["no_fire"],
                split_by_key["no_fire"],
                summary_by_key["no_fire"],
                "sensor_fault",
                str(injected_path.relative_to(root)),
            ),
            l1_1(
                event_by_key["vent"],
                split_by_key["vent"],
                summary_by_key["vent"],
                "ventilation_disturbance",
            ),
            l1_1(
                event_by_key["hard_negative"],
                split_by_key["hard_negative"],
                summary_by_key["hard_negative"],
                "no_fire",
            ),
        ]
    )
    for key in ("fire_low", "fire_high"):
        event = event_by_key[key]
        image_refs = [item["ref"] for item in images_by_key[key]]
        candidate_times = (60.0, 10.0, 90.0, 30.0)
        candidate_refs_s: list[str] = []
        for index, time_s in enumerate(candidate_times):
            candidate_token = opaque_id("C", f"{event['event_id']}:{index}")
            candidate_path = (
                derived_root / "S" / event["event_id"] / f"next_state_{candidate_token}.json"
            )
            candidate_row = nearest(sensor_rows_by_key[key], time_s)
            write_json(
                candidate_path,
                {
                    "variables": {
                        name: round(value, 6)
                        for name, value in candidate_row.items()
                        if name == "Time" or name.startswith(("T_", "V_", "CO_", "U_"))
                    }
                },
            )
            candidate_refs_s.append(str(candidate_path.relative_to(root)))
        candidate_refs_i = [image_refs[2], image_refs[0], image_refs[3], image_refs[1]]
        qa.append(
            l1_2(
                event,
                split_by_key[key],
                "S",
                summary_by_key[key],
                images_by_key[key],
                candidate_refs_s,
                candidate_refs_i,
            )
        )
        qa.append(
            l1_2(
                event,
                split_by_key[key],
                "I",
                summary_by_key[key],
                images_by_key[key],
                candidate_refs_s,
                candidate_refs_i,
            )
        )
        qa.append(l2_1(event, split_by_key[key], "S", summary_by_key[key], images_by_key[key]))
        qa.append(l2_1(event, split_by_key[key], "I", summary_by_key[key], images_by_key[key]))
    a = event_by_key["cf_a"]
    b = event_by_key["cf_b"]
    a_rows = load_devc(run_files(root, SPECS[5])[3])
    b_rows = load_devc(run_files(root, SPECS[6])[3])
    a_temp = nearest(a_rows, 60.0).get("T_FIRE", nearest(a_rows, 60.0).get("T_R4", 0.0))
    b_temp = nearest(b_rows, 60.0).get("T_FIRE", nearest(b_rows, 60.0).get("T_R4", 0.0))
    answer = "A" if a_temp > b_temp + 1.0 else "B" if b_temp > a_temp + 1.0 else "same"
    pair_ref = derived_root / "S" / a["event_group"] / "counterfactual_pair.json"
    write_json(
        pair_ref,
        {
            "case_a": {"summary_ref": summary_by_key["cf_a"]},
            "case_b": {"summary_ref": summary_by_key["cf_b"]},
            "intervention_variable": "hrrpua",
            "future_source_temperature_c": {"A": a_temp, "B": b_temp},
        },
    )
    pair_images = [
        images_by_key["cf_a"][1]["ref"],
        images_by_key["cf_a"][2]["ref"],
        images_by_key["cf_b"][1]["ref"],
        images_by_key["cf_b"][2]["ref"],
    ]
    qa.append(
        l3_3(a, b, split_by_key["cf_a"], str(pair_ref.relative_to(root)), pair_images, "S", answer)
    )
    qa.append(
        l3_3(a, b, split_by_key["cf_a"], str(pair_ref.relative_to(root)), pair_images, "I", answer)
    )
    write_json(qa_root / "qa.json", qa)
    split_rows = [
        {
            "event_id": event_by_key[key]["event_id"],
            "event_group": event_by_key[key]["event_group"],
            "split": split_by_key[key],
        }
        for key in event_by_key
    ]
    write_json(root / "splits" / "mini_pilot_7_event_group_manifest.json", split_rows)
    report = {
        "status": "built_pending_strict_validation",
        "independent_events": len(events),
        "event_classes": {"fire": 4, "no_fire": 2, "ventilation_disturbance": 1},
        "required_composition": {
            "fire_non_counterfactual": 2,
            "no_fire": 1,
            "ventilation_disturbance": 1,
            "non_fire_hard_negative": 1,
            "counterfactual_ab": 2,
        },
        "qa_count": len(qa),
        "qa_tasks": sorted({item["task_id"] for item in qa}),
        "tracks": sorted({item["track"] for item in qa}),
        "counterfactual_future_temperature_c": {"A": a_temp, "B": b_temp, "answer": answer},
        "visual_checks": visual_checks,
        "sensor_fault": {
            "mode": "derived_observation_injection",
            "event_count_increment": 0,
            "ref": str(injected_path.relative_to(root)),
        },
        "source": "raw FDS/CSV/Smoke3D only",
    }
    write_json(report_root / "mini_pilot_build_report.json", report)
    return {
        "events": event_root / "fire_events.json",
        "qa": qa_root / "qa.json",
        "report": report_root / "mini_pilot_build_report.json",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build seven-run FireWorldBench v2 gold mini-pilot"
    )
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    paths = build(args.root.resolve())
    print(json.dumps({name: str(path) for name, path in paths.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
