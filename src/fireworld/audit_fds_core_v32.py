"""Fail-closed independent audit for the rebuilt FDS Core v3.2 candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from itertools import pairwise
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageStat

from fireworld.mini_pilot import write_json
from fireworld.validation import (
    validate_event_groups,
    validate_event_semantics,
    validate_qa_semantics,
    validate_schema,
)

VERSION = "fds-core-v3.2.0"
TASKS = {"L1-1", "L1-2", "L1-3", "L2-1", "L2-2", "L2-3", "L3-1", "L3-2", "L3-3"}
HEX_NAME = re.compile(r"^[a-f0-9]{24}\.(json|png|mp4)$")
FORBIDDEN_KEYS = {"transform", "fault_injection", "mechanism", "comparison", "time_s", "source"}


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def keys(value: Any) -> set[str]:
    output: set[str] = set()
    if isinstance(value, dict):
        output.update(map(str, value))
        for item in value.values():
            output.update(keys(item))
    elif isinstance(value, list):
        for item in value:
            output.update(keys(item))
    return output


def refs(item: dict[str, Any]) -> list[str]:
    result: list[str] = []
    observation = item["observation"]
    if observation["structured"]:
        result.append(observation["structured"]["ref"])
    result.extend(observation["images"] or [])
    if observation["video"]:
        result.append(observation["video"])
    result.extend(option["content_ref"] for option in item["options"] or [] if option["content_ref"])
    return result


def artifact_hashes(root: Path, item: dict[str, Any]) -> set[str]:
    return {hashlib.sha256((root / ref).read_bytes()).hexdigest() for ref in refs(item)}


def image_motion(paths: list[Path]) -> tuple[bool, float]:
    if len(paths) < 2 or not all(path.is_file() for path in paths):
        return False, 0.0
    values: list[float] = []
    hashes: list[str] = []
    for path in paths:
        hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
    for first, second in pairwise(paths):
        with Image.open(first).convert("RGB") as a, Image.open(second).convert("RGB") as b:
            values.append(sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3.0)
    return len(set(hashes)) > 1 and max(values, default=0.0) > 0.25, max(values, default=0.0)


def video_motion(path: Path) -> tuple[bool, float, int]:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if probe.returncode:
        return False, 0.0, 0
    duration = float(json.loads(probe.stdout)["format"]["duration"])
    frames = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "12", "-f", "framemd5", "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    hashes = [line.rsplit(",", 1)[-1].strip() for line in frames.stdout.splitlines() if line and not line.startswith("#")]
    return frames.returncode == 0 and 4.0 <= duration <= 12.0 and len(set(hashes)) > 1, duration, len(set(hashes))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    event_paths = sorted((root / "fire_events" / "fds_core_v3_2").glob("FWE-*.json"))
    events: list[dict[str, Any]] = [load(path) for path in event_paths]
    qa: list[dict[str, Any]] = load(root / "qa" / "fds_core_v3_2" / "qa.json")
    eligible = [
        item
        for item in qa
        if item["quality"]["status"]
        in {"eligible", "eligible_expert_review_deferred"}
    ]
    deferred = [
        item
        for item in qa
        if item["quality"]["status"] == "eligible_expert_review_deferred"
    ]

    schema_errors = [
        f"event:{event['event_id']}:{error}"
        for event in events
        for error in validate_schema(event, "fire_event.schema.json") + validate_event_semantics(event)
    ]
    schema_errors.extend(
        f"qa:{item['qa_id']}:{error}"
        for item in qa
        for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)
    )
    schema_errors.extend(validate_event_groups(qa))

    all_refs = sorted({ref for item in qa for ref in refs(item)})
    missing_refs = [ref for ref in all_refs if not (root / ref).is_file()]
    nonopaque_refs = [ref for ref in all_refs if not HEX_NAME.fullmatch(Path(ref).name)]
    payload_key_errors: list[str] = []
    l12_errors: list[str] = []
    l31_errors: list[str] = []
    for item in qa:
        structured = item["observation"]["structured"]
        if structured:
            payload = load(root / structured["ref"])
            forbidden = keys(payload) & FORBIDDEN_KEYS
            if forbidden:
                payload_key_errors.append(f"{item['qa_id']}:{sorted(forbidden)}")
        if item["task_id"] == "L1-2":
            options = item["options"] or []
            if len(options) != 4:
                l12_errors.append(item["qa_id"] + ":not_four")
                continue
            payloads = [load(root / option["content_ref"]) for option in options]
            if any("Time" in keys(payload) or "time_s" in keys(payload) for payload in payloads):
                l12_errors.append(item["qa_id"] + ":time_exposed")
            if len({json.dumps(payload, sort_keys=True) for payload in payloads}) != 4:
                l12_errors.append(item["qa_id"] + ":duplicate_candidate")
        if item["task_id"] == "L3-1":
            payload = load(root / structured["ref"])
            variables = {key for row in payload.get("rows", []) for key in row}
            required = {"temperature_c", "visibility_m", "soot_density_kg_m3"}
            if not required.issubset(variables):
                l31_errors.append(item["qa_id"] + ":missing_independent_variable")

    groups: dict[str, set[str]] = defaultdict(set)
    for item in qa:
        groups[item["event_group"]].add(item["split"])
    artifact_splits: dict[str, set[str]] = defaultdict(set)
    for item in qa:
        for artifact_hash in artifact_hashes(root, item):
            artifact_splits[artifact_hash].add(item["split"])
    exact_cross_split_duplicates = {
        artifact_hash: sorted(splits)
        for artifact_hash, splits in artifact_splits.items()
        if len(splits) > 1
    }
    answer_positions = Counter(item["answer"]["choice"] for item in eligible if item["task_id"] == "L1-2")
    task_counts = Counter(item["task_id"] for item in eligible)
    all_task_counts = Counter(item["task_id"] for item in qa)
    track_counts = Counter(item["track"] for item in qa)
    l1_windows: dict[str, Counter[float]] = defaultdict(Counter)
    for item in eligible:
        if item["task_id"] == "L1-1":
            l1_windows[item["answer"]["fields"]["class"]][item["observation"]["time_window_s"][1]] += 1

    image_results = []
    for item in qa:
        paths = [root / ref for ref in item["observation"]["images"] or []]
        if paths:
            valid, delta = image_motion(paths)
            exif = []
            for path in paths:
                with Image.open(path) as image:
                    if image.getexif():
                        exif.append(str(path))
            image_results.append({"qa_id": item["qa_id"], "valid": valid, "delta": delta, "exif": exif})
    video_results = []
    for ref in sorted({item["observation"]["video"] for item in qa if item["observation"]["video"]}):
        valid, duration, unique = video_motion(root / ref)
        video_results.append({"ref": ref, "valid": valid, "duration_s": duration, "unique_frame_hashes": unique})

    event_observation_errors = []
    soot_events = 0
    for event in events:
        structured = event["observations"]["structured"]
        if not structured or not (root / structured["ref"]).is_file():
            event_observation_errors.append(event["event_id"] + ":missing_canonical")
            continue
        payload = load(root / structured["ref"])
        if payload.get("smoke_available"):
            soot_events += 1
            if "soot_density" not in structured["variables"]:
                event_observation_errors.append(event["event_id"] + ":soot_not_declared")
        elif "soot_density" in structured["variables"]:
            event_observation_errors.append(event["event_id"] + ":false_soot_declaration")

    checks = {
        "schema_semantic": not schema_errors,
        "exactly_180_events": len(events) == 180,
        "qa_4000_6000": 4000 <= len(qa) <= 6000,
        "all_180_events_have_eligible_qa": len({item["event_id"] for item in eligible}) == 180,
        "all_nine_tasks_with_only_l2_3_deferred": set(task_counts) == TASKS
        and set(all_task_counts) == TASKS
        and bool(deferred)
        and all(item["task_id"] == "L2-3" for item in deferred),
        "payloads_resolve": not missing_refs,
        "all_public_refs_opaque": not nonopaque_refs,
        "no_answer_metadata_in_payloads": not payload_key_errors,
        "l1_2_has_no_time_shortcut": not l12_errors,
        "l1_2_answer_positions_balanced": set(answer_positions) == {"A", "B", "C", "D"} and max(answer_positions.values()) - min(answer_positions.values()) <= 1,
        "l1_1_class_window_balanced": set(l1_windows) == {"fire", "no_fire", "ventilation_disturbance", "sensor_fault"} and all(set(value) == {3.0, 6.0, 10.0, 20.0} and len(set(value.values())) == 1 for value in l1_windows.values()),
        "l3_1_has_independent_soot": not l31_errors and task_counts["L3-1"] > 0,
        "canonical_observations_truthful": not event_observation_errors and soot_events == 173,
        "event_group_leakage_zero": not any(len(value) > 1 for value in groups.values()),
        "exact_artifact_cross_split_leakage_zero": not exact_cross_split_duplicates,
        "images_dynamic_and_exif_free": bool(image_results) and all(item["valid"] and not item["exif"] for item in image_results),
        "videos_dynamic": bool(video_results) and all(item["valid"] for item in video_results),
        "tracks_present": set(track_counts) == {"S", "I", "V"},
    }
    report = {
        "schema_version": VERSION,
        "status": "passed_data_gates_pending_release_experiments" if all(checks.values()) else "blocked_by_v3_2_audit",
        "strict_qualified_events": 0,
        "physical_candidates": 180,
        "qa": len(qa),
        "strict_eligible_qa": len(eligible),
        "deferred_l2_3_qa": len(deferred),
        "task_counts_strict": dict(sorted(task_counts.items())),
        "task_counts_all": dict(sorted(all_task_counts.items())),
        "track_counts": dict(sorted(track_counts.items())),
        "soot_events": soot_events,
        "checks": checks,
        "errors": {
            "schema": schema_errors[:100],
            "missing_refs": missing_refs[:100],
            "nonopaque_refs": nonopaque_refs[:100],
            "payload_keys": payload_key_errors[:100],
            "l1_2": l12_errors[:100],
            "l3_1": l31_errors[:100],
            "event_observations": event_observation_errors[:100],
            "exact_artifact_cross_split_duplicates": dict(
                list(exact_cross_split_duplicates.items())[:100]
            ),
        },
        "image_audit": image_results,
        "video_audit": video_results,
    }
    write_json(root / "reports" / "fds_core_v3_2_data_audit.json", report)
    print(json.dumps({"status": report["status"], "checks": checks}, indent=2))
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
