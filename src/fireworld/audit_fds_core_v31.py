"""Run the final non-expert acceptance audit for the v3.1 frozen snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
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

TASKS = {"L1-1", "L1-2", "L1-3", "L2-1", "L2-2", "L2-3", "L3-1", "L3-2", "L3-3"}
DEFERRED_TASK = "L2-3"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image_motion(paths: list[Path]) -> tuple[bool, float, list[str]]:
    if len(paths) < 2 or not all(path.is_file() for path in paths):
        return False, 0.0, []
    hashes = [sha256(path) for path in paths]
    values: list[float] = []
    for first, second in pairwise(paths):
        with Image.open(first).convert("RGB") as a, Image.open(second).convert("RGB") as b:
            values.append(sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3.0)
    return (
        len(set(hashes)) > 1 and max(values, default=0.0) > 0.25,
        max(values, default=0.0),
        hashes,
    )


def video_motion(path: Path) -> tuple[bool, float, int]:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode:
        return False, 0.0, 0
    try:
        duration = float(json.loads(probe.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False, 0.0, 0
    frames = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "12", "-f", "framemd5", "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    if frames.returncode:
        return False, duration, 0
    hashes = [
        line.split(",")[-1]
        for line in frames.stdout.splitlines()
        if line and not line.startswith("#")
    ]
    return (
        4.0 <= duration <= 12.0 and len(hashes) >= 2 and len(set(hashes)) > 1,
        duration,
        len(set(hashes)),
    )


def structured_time_errors(root: Path, item: dict[str, Any]) -> list[str]:
    ref = item["observation"]["structured"]
    if not ref:
        return []
    path = root / ref["ref"]
    if not path.is_file():
        return [f"missing:{item['qa_id']}:{ref['ref']}"]
    try:
        rows = json.loads(path.read_text()).get("rows", [])
    except (OSError, json.JSONDecodeError):
        return [f"unreadable:{item['qa_id']}:{ref['ref']}"]
    end = item["observation"]["time_window_s"][1]
    times = [
        row.get("Time")
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("Time"), (int, float))
    ]
    return [f"future:{item['qa_id']}" for value in times if value > end + 1e-6]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    event_paths = sorted((root / "fire_events" / "fds_core_v3_1").glob("FWE-*.json"))
    events = [json.loads(path.read_text()) for path in event_paths]
    qa: list[dict[str, Any]] = json.loads((root / "qa" / "fds_core_v3_1" / "qa.json").read_text())
    schema_errors = [
        f"event:{event['event_id']}:{error}"
        for event in events
        for error in validate_schema(event, "fire_event.schema.json")
        + validate_event_semantics(event)
    ]
    schema_errors.extend(
        f"qa:{item['qa_id']}:{error}"
        for item in qa
        for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)
    )
    schema_errors.extend(validate_event_groups(qa))
    refs: set[str] = {"governance/licenses/fds_internal_release_v3_1.md"}
    time_errors: list[str] = []
    option_errors: list[str] = []
    for item in qa:
        time_errors.extend(structured_time_errors(root, item))
        observation = item["observation"]
        if observation["structured"]:
            refs.add(observation["structured"]["ref"])
        refs.update(observation["images"] or [])
        if observation["video"]:
            refs.add(observation["video"])
        for option in item["options"] or []:
            if option["content_ref"]:
                refs.add(option["content_ref"])
        if item["task_id"] == "L1-2":
            options = item["options"] or []
            if len(options) != 4 or {entry["id"] for entry in options} != {"A", "B", "C", "D"}:
                option_errors.append(item["qa_id"] + ":not_four_way")
            if item["answer"]["choice"] not in {entry["id"] for entry in options}:
                option_errors.append(item["qa_id"] + ":answer_not_in_options")
    for event in events:
        observation = event["observations"]
        if observation["structured"]:
            refs.add(observation["structured"]["ref"])
        refs.update(entry["ref"] for entry in observation["images"] or [])
        if observation["video"]:
            refs.add(observation["video"]["ref"])
        refs.add(event["license"]["evidence_ref"] or "")
    refs.discard("")
    missing_refs = sorted(ref for ref in refs if not (root / ref).is_file())
    image_report: list[dict[str, Any]] = []
    for event in events:
        paths = [root / entry["ref"] for entry in event["observations"]["images"] or []]
        if paths:
            valid, delta, hashes = image_motion(paths)
            image_report.append(
                {
                    "event_id": event["event_id"],
                    "valid": valid,
                    "max_pixel_delta": delta,
                    "unique_hashes": len(set(hashes)),
                }
            )
    video_report: list[dict[str, Any]] = []
    for event in events:
        video = event["observations"]["video"]
        if video:
            valid, duration, unique = video_motion(root / video["ref"])
            video_report.append(
                {
                    "event_id": event["event_id"],
                    "valid": valid,
                    "duration_s": duration,
                    "unique_frame_hashes": unique,
                }
            )
    eligible = [item for item in qa if item["quality"]["status"] == "eligible"]
    deferred = [
        item
        for item in qa
        if item["task_id"] == DEFERRED_TASK
        and item["quality"]["ambiguity_reason"] == "expert_review_deferred_by_user"
    ]
    l1 = [item for item in eligible if item["task_id"] == "L1-1"]
    class_windows: dict[str, Counter[float]] = defaultdict(Counter)
    for item in l1:
        class_windows[item["answer"]["fields"]["class"]][
            item["observation"]["time_window_s"][1]
        ] += 1
    option_positions = Counter(
        item["answer"]["choice"] for item in eligible if item["task_id"] == "L1-2"
    )
    task_counts = Counter(item["task_id"] for item in eligible)
    all_task_counts = Counter(item["task_id"] for item in qa)
    split_groups: dict[str, set[str]] = defaultdict(set)
    for item in qa:
        split_groups[item["event_group"]].add(item["split"])
    filenames = [Path(ref).name.lower() for ref in refs]
    forbidden_tokens = ["answer", "label", "correct", "fire_yes", "fire_no"]
    filename_shortcuts = sorted(
        name for name in filenames if any(token in name for token in forbidden_tokens)
    )
    status = {
        "schema_semantic_and_split": not schema_errors,
        "exactly_180_events": len(events) == 180,
        "strict_eligible_qa_4000_6000": 4000 <= len(eligible) <= 6000,
        "all_events_have_strict_eligible_qa": len({item["event_id"] for item in eligible}) == 180,
        "nine_tasks_present_with_only_expert_deferred": set(task_counts) == TASKS - {DEFERRED_TASK}
        and all_task_counts[DEFERRED_TASK] > 0,
        "expert_deferral_is_only_l2_3": len(deferred)
        == len([item for item in qa if item["quality"]["status"] != "eligible"]),
        "all_payloads_resolve": not missing_refs,
        "no_future_structured_rows": not time_errors,
        "l1_2_four_way_and_balanced": not option_errors
        and set(option_positions) == {"A", "B", "C", "D"}
        and max(option_positions.values()) - min(option_positions.values()) <= 1,
        "l1_1_class_and_window_balanced": set(class_windows)
        == {"fire", "no_fire", "ventilation_disturbance", "sensor_fault"}
        and all(
            set(counts) == {3.0, 6.0, 10.0, 20.0} and len(set(counts.values())) == 1
            for counts in class_windows.values()
        ),
        "dynamic_images_pass": all(row["valid"] for row in image_report),
        "dynamic_videos_pass": all(row["valid"] for row in video_report),
        "event_group_leakage_zero": not any(len(value) > 1 for value in split_groups.values()),
        "no_filename_shortcut_tokens": not filename_shortcuts,
    }
    report = {
        "schema_version": "fds-core-v3.1.0",
        "release_status": "provisionally_accepted_expert_review_deferred"
        if all(status.values())
        else "blocked_by_final_audit",
        "expert_review_policy": "deferred_by_user_only_for_L2-3",
        "event_count": len(events),
        "qa_count": len(qa),
        "strict_eligible_qa_count": len(eligible),
        "deferred_expert_qa_count": len(deferred),
        "task_counts_strict": dict(sorted(task_counts.items())),
        "task_counts_all": dict(sorted(all_task_counts.items())),
        "l1_1_class_windows": {
            key: dict(sorted(value.items())) for key, value in sorted(class_windows.items())
        },
        "l1_2_answer_positions": dict(sorted(option_positions.items())),
        "checks": status,
        "errors": {
            "schema": schema_errors[:100],
            "time": time_errors[:100],
            "options": option_errors[:100],
            "missing_refs": missing_refs[:100],
            "filename_shortcuts": filename_shortcuts[:100],
        },
        "dynamic_images": image_report,
        "dynamic_videos": video_report,
    }
    write_json(root / "reports" / "fds_core_v3_1_final_audit.json", report)
    print(json.dumps({"release_status": report["release_status"], "checks": status}, indent=2))
    return 0 if report["release_status"] != "blocked_by_final_audit" else 2


if __name__ == "__main__":
    raise SystemExit(main())
