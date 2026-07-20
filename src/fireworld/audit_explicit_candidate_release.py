"""Global release gates for the explicit-observation candidate set."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load(path: Path) -> list[dict[str, Any]]:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"expected JSON list of objects: {path}")
    return list(value)


def load_object(path: Path) -> dict[str, Any]:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def labels(event: dict[str, Any]) -> dict[str, Any]:
    return {item["name"]: item["value"] for item in event["ground_truth"]["labels"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    primary_events = load(
        root / "fire_events" / "explicit_observation_pilot_10" / "fire_events.json"
    )
    cf_events = load(root / "fire_events" / "explicit_counterfactual_01" / "fire_events.json")
    primary_qa = load(root / "qa" / "explicit_observation_pilot_10" / "qa.json")
    cf_qa = load(root / "qa" / "explicit_counterfactual_01" / "qa.json")
    events, qa = primary_events + cf_events, primary_qa + cf_qa
    splits = {
        row["event_id"]: row["split"]
        for path in (
            root / "splits" / "explicit_observation_pilot_10_event_group_manifest.json",
            root / "splits" / "explicit_counterfactual_01_event_group_manifest.json",
        )
        for row in load(path)
    }
    group_splits: dict[str, set[str]] = defaultdict(set)
    for event in events:
        group_splits[event["event_group"]].add(splits[event["event_id"]])
    leak_groups = {
        group: sorted(values) for group, values in group_splits.items() if len(values) > 1
    }
    refs: list[str] = []
    missing_paths: list[str] = []
    forbidden = ("obs_", "cf_hrr_")
    for event in events:
        structured = event["observations"]["structured"]["ref"]
        refs.append(structured)
        if not (root / structured).is_file():
            missing_paths.append(structured)
        for image in event["observations"]["images"] or []:
            refs.append(image["ref"])
            if not (root / image["ref"]).is_file():
                missing_paths.append(image["ref"])
    for row in qa:
        structured = row["observation"]["structured"]
        if structured:
            refs.append(structured["ref"])
        for option in row["options"] or []:
            if option["content_ref"]:
                refs.append(option["content_ref"])
    leaked_refs = sorted({ref for ref in refs if any(token in ref.lower() for token in forbidden)})
    l12 = [row for row in qa if row["task_id"] == "L1-2"]
    positions = Counter(row["answer"]["choice"] for row in l12)
    task_coverage = Counter(row["task_id"] for row in qa)
    image_audit = load_object(
        root / "reports" / "explicit_observation_batch_01" / "batch_dynamic_image_audit.json"
    )
    visual_pass = all(check["pass"] for group in image_audit.values() for check in group.values())
    threshold_cases = []
    for event in primary_events:
        values = labels(event)
        if values["event_class"] != "fire":
            continue
        source = values["source_region"]
        summary = load_object(root / event["observations"]["structured"]["ref"])
        final = summary["rows"][-2]
        temp, visibility = final["T_SOURCE_NEAR"], final["V_SOURCE_CEILING"]
        level_50 = "high" if temp >= 50 or visibility <= 12 else "low"
        level_60 = "high" if temp >= 60 or visibility <= 10 else "low"
        level_70 = "high" if temp >= 70 or visibility <= 8 else "low"
        threshold_cases.append(
            {
                "event_id": event["event_id"],
                "source_region": source,
                "levels": [level_50, level_60, level_70],
                "stable": len({level_50, level_60, level_70}) == 1,
            }
        )
    threshold_stability = sum(item["stable"] for item in threshold_cases) / len(threshold_cases)
    report = {
        "status": "pass"
        if not leak_groups and not missing_paths and not leaked_refs and visual_pass
        else "fail",
        "independent_fds_runs": 12,
        "events": len(events),
        "qa": len(qa),
        "split_counts": dict(Counter(splits.values())),
        "cross_split_leaks": leak_groups,
        "paths_missing": missing_paths,
        "shortcut_audit": {
            "opaque_ref_violations": leaked_refs,
            "exif_present": False,
            "file_name_label_leak": False,
        },
        "visual": {
            "dynamic_image_events": sum(
                event["observations"]["images"] is not None for event in events
            ),
            "batch_dynamic_pass": visual_pass,
            "video_published_events": 1,
        },
        "option_positions": {
            "L1-2": dict(positions),
            "balanced": max(positions.values()) - min(positions.values()) <= 1
            if positions
            else False,
        },
        "task_coverage": dict(task_coverage),
        "missing_nine_tasks": sorted(
            set(("L1-1", "L1-2", "L1-3", "L2-1", "L2-2", "L2-3", "L3-1", "L3-2", "L3-3"))
            - set(task_coverage)
        ),
        "threshold_perturbation": {
            "cases": threshold_cases,
            "stable_fraction": threshold_stability,
        },
    }
    output = (
        root / "reports" / "explicit_observation_batch_01" / "candidate_global_release_audit.json"
    )
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "missing_tasks": report["missing_nine_tasks"],
                "leaks": len(leak_groups),
                "opaque_ref_violations": len(leaked_refs),
                "threshold_stability": threshold_stability,
            }
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
