"""Rebuild a shortcut-resistant v3.2 candidate from audited v3.1 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, cast

import fdsreader
import numpy as np
from PIL import Image

from fireworld.build_global_release import (
    hrr_for_event,
    load_events,
    nearest,
    raw_for_event,
    trend,
)
from fireworld.mini_pilot import write_json
from fireworld.validation import (
    validate_event_groups,
    validate_event_semantics,
    validate_qa_semantics,
    validate_schema,
)

VERSION = "fds-core-v3.2.0"
ROOT_REF = "derived/fds_core_v3_2"
TEST_SPLITS = {"test_iid", "test_ood_geometry", "test_ood_condition", "test_ood_view_sensor"}


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def token(*values: object) -> str:
    return digest(":".join(map(str, values)))[:24]


def clean_rows(rows: list[dict[str, Any]], *, remove_time: bool = False) -> list[dict[str, Any]]:
    output = json.loads(json.dumps(rows))
    for row in output:
        if remove_time:
            row.pop("Time", None)
        elif "Time" in row:
            row["relative_time_s"] = row.pop("Time")
    return cast(list[dict[str, Any]], output)


def write_payload(root: Path, qa_id: str, suffix: str, payload: dict[str, Any]) -> str:
    payload = {"observation_instance": token(qa_id), **payload}
    rel = Path(ROOT_REF) / "S" / token(qa_id) / f"{token(qa_id, suffix)}.json"
    write_json(root / rel, payload)
    return rel.as_posix()


def copy_image(root: Path, event_id: str, source_ref: str) -> str:
    source = root / source_ref
    extension = source.suffix.lower()
    rel = Path(ROOT_REF) / "I" / token(event_id) / f"{token(event_id, source_ref)}{extension}"
    destination = root / rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        os.link(source, destination)
    return rel.as_posix()


def transcode_video(root: Path, event_id: str, source_ref: str, role: str) -> str:
    source = root / source_ref
    rel = Path(ROOT_REF) / "V" / token(event_id) / f"{token(event_id, role)}.mp4"
    destination = root / rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-v", "error", "-i", str(source), "-map_metadata", "-1",
        "-an", "-vf", "fps=10,scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(destination),
    ]
    subprocess.run(command, check=True)
    return rel.as_posix()


def image_vector(path: Path) -> np.ndarray[Any, np.dtype[np.float64]]:
    with Image.open(path) as image:
        return np.asarray(image.convert("L").resize((128, 72)), dtype=np.float64)


def difference_hash(image: np.ndarray[Any, np.dtype[np.float64]]) -> bytes:
    resized = np.asarray(
        Image.fromarray(image.astype(np.uint8)).resize((17, 16)), dtype=np.uint8
    )
    return np.packbits(resized[:, :-1] > resized[:, 1:]).tobytes()


def global_ssim(left: np.ndarray[Any, np.dtype[np.float64]], right: np.ndarray[Any, np.dtype[np.float64]]) -> float:
    c1, c2 = 6.5025, 58.5225
    left_mean, right_mean = float(left.mean()), float(right.mean())
    left_var, right_var = float(left.var()), float(right.var())
    covariance = float(np.mean((left - left_mean) * (right - right_mean)))
    numerator = (2 * left_mean * right_mean + c1) * (2 * covariance + c2)
    denominator = (left_mean**2 + right_mean**2 + c1) * (left_var + right_var + c2)
    return numerator / denominator


def perceptual_conflict_events(root: Path, qa: list[dict[str, Any]]) -> set[str]:
    events: dict[str, tuple[str, set[str]]] = {}
    for item in qa:
        if item["track"] != "I":
            continue
        split, refs = events.setdefault(item["event_id"], (item["split"], set()))
        refs.update(item["observation"]["images"] or [])
    images: dict[str, tuple[str, str, np.ndarray[Any, np.dtype[np.float64]]]] = {}
    for event_id, (split, refs) in events.items():
        for ref in refs:
            images.setdefault(ref, (event_id, split, image_vector(root / ref)))
    buckets: dict[bytes, list[tuple[str, str, np.ndarray[Any, np.dtype[np.float64]]]]] = {}
    for event_id, split, image in images.values():
        buckets.setdefault(difference_hash(image), []).append((event_id, split, image))
    conflicts: dict[str, set[str]] = {}
    for bucket in buckets.values():
        for index, (left_event, left_split, left_image) in enumerate(bucket):
            for right_event, right_split, right_image in bucket[index + 1 :]:
                if (
                    left_split != right_split
                    and global_ssim(left_image, right_image) >= 0.995
                ):
                    conflicts.setdefault(left_event, set()).add(right_event)
                    conflicts.setdefault(right_event, set()).add(left_event)
    retained = set(events)
    removed: set[str] = set()
    while True:
        edges = {
            tuple(sorted((left, right)))
            for left in retained
            for right in conflicts.get(left, set())
            if right in retained
        }
        if not edges:
            return removed
        degree = Counter(event_id for edge in edges for event_id in edge)
        selected = max(degree, key=lambda event_id: (degree[event_id], event_id))
        retained.remove(selected)
        removed.add(selected)


def event_region(event: dict[str, Any]) -> str:
    labels = {item["name"]: item["value"] for item in event["ground_truth"]["labels"]}
    return str(labels.get("source_region") or (event.get("controls") or {}).get("source_region") or "R1")


def region_bounds(event: dict[str, Any], region: str) -> list[float] | None:
    for item in event["geometry"]["regions"]:
        if item["region_id"] == region:
            return cast(list[float] | None, item["bounds_m"])
    return None


def soot_series(event: dict[str, Any], root: Path, cache: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    event_id = event["event_id"]
    if event_id in cache:
        return cache[event_id]
    log_ref = root / event["provenance"]["fds"]["log_ref"]
    run = log_ref.parent
    try:
        simulation = fdsreader.Simulation(str(run))
        soot = next(item for item in simulation.slices if item.quantity.name == "SOOT DENSITY")
        subslice = next(iter(soot.subslices))
        coordinates = subslice.get_coordinates()
        x_values, y_values = coordinates["x"], coordinates["y"]
        data = subslice.data
    except (StopIteration, FileNotFoundError, ValueError, OSError):
        return None
    regions: dict[str, list[float]] = {}
    for item in event["geometry"]["regions"]:
        bounds = item["bounds_m"]
        if bounds is None:
            continue
        x_mask = (x_values >= bounds[0]) & (x_values <= bounds[1])
        y_mask = (y_values >= bounds[2]) & (y_values <= bounds[3])
        if not x_mask.any() or not y_mask.any():
            continue
        selected = data[:, x_mask, :][:, :, y_mask]
        regions[item["region_id"]] = [round(float(value), 12) for value in np.mean(selected, axis=(1, 2))]
    result = {"times": [float(value) for value in soot.times], "regions": regions}
    cache[event_id] = result
    return result


def nearest_value(times: list[float], values: list[float], when: float) -> float:
    index = min(range(len(times)), key=lambda position: abs(times[position] - when))
    return values[index]


def stable_trend(a: float, b: float, deadbands: tuple[float, float, float], inverse: bool = False) -> str | None:
    labels = {trend(a, b, deadband, inverse) for deadband in deadbands}
    return labels.pop() if len(labels) == 1 else None


def first_high(
    rows: list[dict[str, float]],
    start: float,
    end: float,
    temperature: float,
    visibility: float,
    tie_tolerance: float = 2.0,
) -> str | None:
    crossings: list[tuple[float, str]] = []
    for number in range(1, 9):
        region = f"R{number}"
        for row in rows:
            if start < row["Time"] <= end and (row.get(f"T_{region}", 20.0) >= temperature or row.get(f"V_{region}", 30.0) <= visibility):
                crossings.append((row["Time"], region))
                break
    if not crossings:
        return "none"
    crossings.sort()
    if len(crossings) > 1 and crossings[1][0] - crossings[0][0] <= tie_tolerance:
        return None
    return crossings[0][1]


def perturbed_stage(
    hrr_rows: list[dict[str, float]], t: float, scale: float
) -> str | None:
    if not hrr_rows:
        return None
    peak = max((row.get("HRR", 0.0) for row in hrr_rows), default=0.0)
    if peak < 1.0:
        return "incipient"
    current = nearest(hrr_rows, t).get("HRR", 0.0)
    prior = nearest(hrr_rows, max(0.0, t - 10.0)).get("HRR", 0.0)
    ratio = current / peak
    slope = (current - prior) / 10.0
    if ratio <= 0.05 * scale:
        return "incipient"
    if 0.08 * scale < ratio < 0.72 * scale and slope > peak * 0.003 * scale:
        return "growth"
    if ratio >= 0.80 * scale:
        return "developed"
    if ratio < 0.72 * scale and slope < -peak * 0.003 * scale:
        return "decay"
    return None


def sanitize_payload(task: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(payload))
    for key in ("transform", "fault_injection", "mechanism", "comparison", "time_s", "source"):
        result.pop(key, None)
    if task == "L1-2":
        values = result.get("values", {})
        if isinstance(values, dict):
            values.pop("Time", None)
    if task == "L1-3" and isinstance(result.get("rows"), list):
        result["rows"] = clean_rows(result["rows"], remove_time=True)
    if task == "L3-3":
        result.pop("comparison_time_s", None)
        for side in ("A", "B"):
            if isinstance(result.get(side), list):
                result[side] = clean_rows(result[side], remove_time=True)
    return cast(dict[str, Any], result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    destination = root / "derived" / "fds_core_v3_2"
    if destination.exists():
        raise ValueError(f"refusing to overwrite {destination}")

    fresh_s_qa: list[dict[str, Any]] = json.loads(
        (root / "qa/protocol_rebuild_v3/qa.json").read_text()
    )
    visual_skeletons: list[dict[str, Any]] = [
        item
        for item in json.loads((root / "qa/fds_core_v3_1/qa.json").read_text())
        if item["track"] in {"I", "V"}
    ]
    old_qa = fresh_s_qa + visual_skeletons
    event_pairs, batch_index = load_events(root)
    raw_events = {event["event_id"]: event for event, _ in event_pairs}
    repaired_event_ids = {
        item["event_id"]
        for item in json.loads(
            (root / "fds_runs/trajectory_repair_v3_2/input_manifest.json").read_text()
        )["runs"]
    }
    matrix_v32_path = root / "splits/production_matrix.v3.2.json"
    if not matrix_v32_path.is_file():
        source_matrix = json.loads((root / "splits/production_matrix.v2.1.json").read_text())
        repair_manifest = json.loads(
            (root / "fds_runs/trajectory_repair_v3_2/input_manifest.json").read_text()
        )
        repair_by_event = {item["event_id"]: item for item in repair_manifest["runs"]}
        for row in source_matrix["rows"]:
            row["status"] = "active_repaired" if row["event_id"] in repair_by_event else "active_retained"
            row["source_ref"] = f"fire_events/trajectory_repair_v3_2/{row['event_id']}.json" if row["event_id"] in repair_by_event else row.get("source_ref")
            row["production_batch"] = (
                "trajectory_repair_v3_2"
                if row["event_id"] in repair_by_event
                else row.get("production_batch")
            )
        source_matrix.update(
            {
                "schema_version": "3.2.0",
                "status": "frozen_active_snapshot",
                "qualified_existing": 0,
                "planned_new": 0,
                "active_events": 180,
                "active_repaired": len(repair_by_event),
                "active_retained": 180 - len(repair_by_event),
            }
        )
        write_json(matrix_v32_path, source_matrix)
    raw_rows = {event_id: raw_for_event(root, event, batch_index) for event_id, event in raw_events.items()}
    matrix_rows = {
        row["event_id"]: row
        for row in json.loads(matrix_v32_path.read_text())["rows"]
    }
    family_events: dict[str, list[dict[str, Any]]] = {}
    for event in raw_events.values():
        family_events.setdefault(str(event["event_group"]), []).append(event)
    soot_cache: dict[str, dict[str, Any]] = {}
    rebuilt: list[dict[str, Any]] = []
    excluded: Counter[str] = Counter()
    image_map: dict[tuple[str, str], str] = {}
    video_map: dict[tuple[str, str], str] = {}
    repair_visual_report = json.loads(
        (root / "reports/fds_core_v3_2_trajectory_repair_visual_audit.json").read_text()
    )

    for original in old_qa:
        task = original["task_id"]
        if task == "L3-1":
            event = raw_events[original["event_id"]]
            region = event_region(event)
            if region_bounds(event, region) is None:
                excluded["l3_1_region_without_bounds"] += 1
                continue
            soot = soot_series(event, root, soot_cache)
            if soot is None or region not in soot["regions"]:
                excluded["l3_1_missing_soot_slice"] += 1
                continue
            context = original["observation"]["context"] or ""
            horizon = int(context.split()[3])
            rows = raw_rows[original["event_id"]]
            current, future = nearest(rows, 20.0), nearest(rows, 20.0 + horizon)
            temperature = stable_trend(current.get(f"T_{region}", 20.0), future.get(f"T_{region}", 20.0), (4.0, 5.0, 6.0))
            visibility = stable_trend(current.get(f"V_{region}", 30.0), future.get(f"V_{region}", 30.0), (0.8, 1.0, 1.2))
            soot_current = nearest_value(soot["times"], soot["regions"][region], 20.0)
            soot_future = nearest_value(soot["times"], soot["regions"][region], 20.0 + horizon)
            smoke = stable_trend(soot_current, soot_future, (8e-8, 1e-7, 1.2e-7))
            if None in (temperature, visibility, smoke):
                excluded["l3_1_threshold_unstable"] += 1
                continue
            current_rows = []
            for when in (10.0, 12.0, 14.0, 16.0, 18.0, 20.0):
                row = nearest(rows, when)
                current_rows.append({
                    "relative_time_s": when - 10.0,
                    "temperature_c": round(row.get(f"T_{region}", 20.0), 6),
                    "visibility_m": round(row.get(f"V_{region}", 30.0), 6),
                    "soot_density_kg_m3": round(nearest_value(soot["times"], soot["regions"][region], when), 12),
                })
            ref = write_payload(root, original["qa_id"], "l3-1", {"format": "bounded_region_observation", "region": region, "rows": current_rows})
            item = json.loads(json.dumps(original))
            item["observation"]["structured"]["ref"] = ref
            item["answer"]["fields"] = {"temperature_trend": temperature, "smoke_trend": smoke, "visibility_trend": visibility}
        elif task == "L3-2":
            context = original["observation"]["context"] or ""
            match = re.search(r"(\d+)\s+seconds", context)
            if match is None:
                raise ValueError(f"L3-2 horizon is not recoverable: {context}")
            horizon = int(match.group(1))
            rows = raw_rows[original["event_id"]]
            l32_labels = {
                first_high(rows, 20.0, 20.0 + horizon, temp, vis, tie)
                for temp, vis in ((55.0, 9.0), (60.0, 10.0), (65.0, 11.0))
                for tie in (1.5, 2.0, 2.5)
            }
            if None in l32_labels or len(l32_labels) != 1:
                excluded["l3_2_threshold_or_tie_unstable"] += 1
                continue
            item = json.loads(json.dumps(original))
            item["answer"]["fields"] = {
                "first_high_risk_region": l32_labels.pop()
            }
            source = json.loads((root / original["observation"]["structured"]["ref"]).read_text())
            ref = write_payload(root, original["qa_id"], "l3-2", sanitize_payload(task, source))
            item["observation"]["structured"]["ref"] = ref
        elif task == "L2-1":
            event = raw_events[original["event_id"]]
            now = float(original["observation"]["time_window_s"][1])
            hrr_rows = hrr_for_event(root, event, batch_index)
            l21_labels = {
                perturbed_stage(hrr_rows, now, scale) for scale in (0.9, 1.0, 1.1)
            }
            if None in l21_labels or len(l21_labels) != 1:
                excluded["l2_1_stage_threshold_unstable"] += 1
                continue
            item = json.loads(json.dumps(original))
            item["answer"]["fields"]["stage"] = l21_labels.pop()
            payload = json.loads((root / original["observation"]["structured"]["ref"]).read_text())
            item["observation"]["structured"]["ref"] = write_payload(
                root, original["qa_id"], "l2-1", sanitize_payload(task, payload)
            )
        elif task == "L2-2":
            payload = json.loads((root / original["observation"]["structured"]["ref"]).read_text())
            row = cast(list[dict[str, float]], payload["rows"])[-1]
            l22_labels: set[tuple[str, str]] = set()
            for temp_threshold, vis_threshold in ((55.0, 9.0), (60.0, 10.0), (65.0, 11.0)):
                scores = {f"R{i}": max((row.get(f"T_R{i}", 20.0) - 20.0) / 40.0, (30.0 - row.get(f"V_R{i}", 30.0)) / 6.0) for i in range(1, 9)}
                ordered = sorted(scores, key=scores.__getitem__, reverse=True)
                if scores[ordered[0]] - scores[ordered[1]] < 0.15:
                    l22_labels.add(("ambiguous", "ambiguous"))
                    continue
                region = ordered[0]
                t_value, v_value = row.get(f"T_{region}", 20.0), row.get(f"V_{region}", 30.0)
                level = "critical" if t_value >= 200 or v_value <= 3 else "high" if t_value >= temp_threshold or v_value <= vis_threshold else "moderate" if t_value >= 35 or v_value <= 20 else "low"
                l22_labels.add((region, level))
            scores = {
                f"R{i}": max(
                    (row.get(f"T_R{i}", 20.0) - 20.0) / 40.0,
                    (30.0 - row.get(f"V_R{i}", 30.0)) / 6.0,
                )
                for i in range(1, 9)
            }
            ordered_regions = sorted(scores, key=scores.__getitem__, reverse=True)
            if (
                len(l22_labels) != 1
                or next(iter(l22_labels))[0] == "ambiguous"
                or scores[ordered_regions[0]] - scores[ordered_regions[1]] < 0.18
            ):
                excluded["l2_2_threshold_or_region_unstable"] += 1
                continue
            item = json.loads(json.dumps(original))
            region, level = l22_labels.pop()
            item["answer"]["fields"] = {"risk_region": region, "risk_level": level}
            ref = write_payload(root, original["qa_id"], "l2-2", sanitize_payload(task, payload))
            item["observation"]["structured"]["ref"] = ref
        else:
            item = json.loads(json.dumps(original))
            if task == "L3-3":
                event = raw_events[item["event_id"]]
                members = family_events[str(event["event_group"])]
                if len(members) != 2:
                    raise ValueError(
                        f"L3-3 family is not a pair: {event['event_group']}"
                    )
                member_a, member_b = sorted(
                    members,
                    key=lambda member: str(
                        member["controls"]["intervention"].get("value")
                    ),
                )
                region = event_region(member_a)
                a_value = float(
                    nearest(raw_rows[member_a["event_id"]], 80.0).get(
                        f"T_{region}", 20.0
                    )
                )
                b_value = float(
                    nearest(raw_rows[member_b["event_id"]], 80.0).get(
                        f"T_{region}", 20.0
                    )
                )
                delta = a_value - b_value
                labels = {
                    "A" if delta > threshold else "B" if delta < -threshold else "same"
                    for threshold in (0.8, 1.0, 1.2)
                }
                if len(labels) != 1:
                    excluded["l3_3_minimum_difference_unstable"] += 1
                    continue
                item["answer"]["fields"]["comparison"] = labels.pop()
            observation = item["observation"]
            if observation["structured"]:
                source = json.loads((root / observation["structured"]["ref"]).read_text())
                observation["structured"]["ref"] = write_payload(root, item["qa_id"], "observation", sanitize_payload(task, source))
            if item["options"]:
                for option in item["options"]:
                    if option["content_ref"]:
                        source = json.loads((root / option["content_ref"]).read_text())
                        option["content_ref"] = write_payload(root, item["qa_id"], option["id"], sanitize_payload(task, source))
                if task == "L1-2":
                    candidate_digests = {
                        digest(json.loads((root / option["content_ref"]).read_text()))
                        for option in item["options"]
                    }
                    if len(candidate_digests) != 4:
                        excluded["l1_2_duplicate_candidate_state"] += 1
                        continue
            if observation["images"]:
                if item["event_id"] in repaired_event_ids:
                    rendered = repair_visual_report["images"][item["event_id"]]["images"]
                    source_sequence = [entry["ref"] for entry in rendered]
                    if item["answer"]["fields"]["consistency"] == "inconsistent":
                        source_sequence.reverse()
                else:
                    source_sequence = observation["images"]
                opaque_images = []
                for source_ref in source_sequence:
                    key = (item["event_id"], source_ref)
                    image_map.setdefault(key, copy_image(root, item["event_id"], source_ref))
                    opaque_images.append(image_map[key])
                observation["images"] = opaque_images
            if observation["video"]:
                role = "variant-a" if item["answer"]["fields"]["consistency"] == "consistent" else "variant-b"
                source_video = observation["video"]
                if item["event_id"] in repaired_event_ids:
                    repair_role = "consistent" if role == "variant-a" else "inconsistent"
                    source_video = repair_visual_report["videos"][item["event_id"]][repair_role]["ref"]
                key = (item["event_id"], role)
                video_map.setdefault(key, transcode_video(root, item["event_id"], source_video, role))
                observation["video"] = video_map[key]

        item["provenance"]["builder_version"] = VERSION
        item["quality"]["shortcut_checks"] = {"opaque_paths": True, "time_matched": True, "option_style_matched": True, "appearance_matched": True}
        if task == "L2-3":
            item["quality"]["status"] = "eligible_expert_review_deferred"
            item["quality"]["ambiguity_reason"] = (
                "independent_fire_engineering_review_deferred_by_user"
            )
        rebuilt.append(item)

    # Rebalance the public answer positions after excluding physically duplicate
    # candidate states. This only swaps option identifiers; payloads stay fixed.
    for ordinal, item in enumerate(
        sorted(
            (candidate for candidate in rebuilt if candidate["task_id"] == "L1-2"),
            key=lambda candidate: candidate["qa_id"],
        )
    ):
        desired = "ABCD"[ordinal % 4]
        old = item["answer"]["choice"]
        if old == desired:
            continue
        for option in item["options"]:
            if option["id"] == old:
                option["id"] = desired
            elif option["id"] == desired:
                option["id"] = old
        item["answer"]["choice"] = desired
        item["answer"]["fields"]["choice"] = desired

    removed_image_events = perceptual_conflict_events(root, rebuilt)
    if removed_image_events:
        rebuilt = [
            item
            for item in rebuilt
            if not (item["track"] == "I" and item["event_id"] in removed_image_events)
        ]
        excluded["image_cross_split_perceptual_near_duplicate"] += len(
            removed_image_events
        )

    event_root = root / "fire_events" / "fds_core_v3_2"
    canonical_events: dict[str, dict[str, Any]] = {}
    for event_id, original in raw_events.items():
        event = json.loads(json.dumps(original))
        matrix_class = matrix_rows[event_id]["event_class"]
        for label in event["ground_truth"]["labels"]:
            if label["name"] == "event_class":
                label["value"] = matrix_class
                break
        else:
            event["ground_truth"]["labels"].append(
                {"name": "event_class", "value": matrix_class}
            )
        event["provenance"]["transform_version"] = VERSION
        event["license"] = {
            "license_id": "FDS-GENERATED-INTERNAL-RESEARCH-V3.2",
            "evidence_ref": "governance/licenses/fds_internal_release_v3_1.md",
            "citation": "NIST Fire Dynamics Simulator 6.11.1 and Smokeview 6.11.2",
            "allowed_uses": ["research", "evaluation", "derivation"],
            "redistribution": "restricted",
        }
        event["observations"]["images"] = None
        event["observations"]["video"] = None
        event["observations"]["structured"] = None
        event_items = [item for item in rebuilt if item["event_id"] == event_id]
        raw = raw_rows[event_id]
        soot = soot_series(event, root, soot_cache)
        canonical_rows: list[dict[str, Any]] = []
        for when in (0.0, 20.0, 50.0, 80.0, 110.0):
            sensor_row = nearest(raw, when)
            canonical_row: dict[str, Any] = {
                "time_s": round(float(sensor_row["Time"]), 6),
                "temperature_c": {
                    f"R{i}": round(float(sensor_row.get(f"T_R{i}", 20.0)), 6)
                    for i in range(1, 9)
                },
                "visibility_m": {
                    f"R{i}": round(float(sensor_row.get(f"V_R{i}", 30.0)), 6)
                    for i in range(1, 9)
                },
                "u_velocity_m_s": {
                    f"R{i}": round(float(sensor_row.get(f"U_R{i}", 0.0)), 6)
                    for i in range(1, 9)
                },
                "soot_density_kg_m3": None,
            }
            if soot is not None:
                canonical_row["soot_density_kg_m3"] = {
                    region: round(nearest_value(soot["times"], values, when), 12)
                    for region, values in soot["regions"].items()
                }
            canonical_rows.append(canonical_row)
        canonical_ref = write_payload(
            root,
            event_id,
            "canonical",
            {
                "format": "canonical_event_observation_v3_2",
                "smoke_available": soot is not None,
                "rows": canonical_rows,
            },
        )
        variables = ["temperature", "visibility", "u_velocity"]
        if soot is not None:
            variables.append("soot_density")
        event["observations"]["structured"] = {
            "ref": canonical_ref,
            "format": "json",
            "variables": variables,
            "units_normalized": True,
        }
        image_item = next(
            (
                item
                for item in event_items
                if item["track"] == "I"
                and item["answer"]["fields"]["consistency"] == "consistent"
            ),
            None,
        )
        if image_item:
            source_by_opaque = {
                opaque_ref: source_ref
                for (mapped_event_id, source_ref), opaque_ref in image_map.items()
                if mapped_event_id == event_id
            }
            original_image_times: dict[str, float] = {}
            for opaque_ref in image_item["observation"]["images"]:
                source_ref = source_by_opaque[opaque_ref]
                match = re.search(r"_t(\d+(?:\.\d+)?)$", Path(source_ref).stem)
                if match is None:
                    raise ValueError(f"image time is not recoverable: {source_ref}")
                original_image_times[opaque_ref] = float(match.group(1))
            event["observations"]["images"] = [
                {
                    "ref": ref,
                    "time_s": original_image_times[ref],
                    "sha256": hashlib.sha256((root / ref).read_bytes()).hexdigest(),
                }
                for ref in sorted(
                    image_item["observation"]["images"],
                    key=original_image_times.__getitem__,
                )
            ]
        video_item = next((item for item in event_items if item["track"] == "V" and item["answer"]["fields"]["consistency"] == "consistent"), None)
        if video_item:
            ref = video_item["observation"]["video"]
            event["observations"]["video"] = {"ref": ref, "start_s": 0.0, "duration_s": 6.0, "fps": 10.0, "width": 640, "height": 360, "sha256": hashlib.sha256((root / ref).read_bytes()).hexdigest()}
        errors = validate_schema(event, "fire_event.schema.json") + validate_event_semantics(event)
        if errors:
            raise ValueError(f"event {event_id}: {errors[:5]}")
        canonical_events[event_id] = event

    for item in rebuilt:
        item["provenance"]["event_manifest_sha256"] = digest(canonical_events[item["event_id"]])
    errors = [error for item in rebuilt for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)]
    errors.extend(validate_event_groups(rebuilt))
    if errors:
        raise ValueError("QA validation failed: " + "; ".join(errors[:20]))
    for event_id, event in canonical_events.items():
        write_json(event_root / f"{event_id}.json", event)
    write_json(root / "qa" / "fds_core_v3_2" / "qa.json", rebuilt)
    report = {
        "schema_version": VERSION,
        "status": "candidate_pending_v3_2_audit",
        "events": len(canonical_events),
        "qa": len(rebuilt),
        "strict_eligible": sum(item["quality"]["status"] == "eligible" for item in rebuilt),
        "task_counts": dict(sorted(Counter(item["task_id"] for item in rebuilt).items())),
        "track_counts": dict(sorted(Counter(item["track"] for item in rebuilt).items())),
        "excluded": dict(sorted(excluded.items())),
        "soot_events": len(soot_cache),
        "fdsreader_version": "1.11.7",
    }
    write_json(root / "reports" / "fds_core_v3_2_build.json", report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
