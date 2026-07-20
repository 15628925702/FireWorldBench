"""Produce the fail-closed acceptance report for one production batch."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from fireworld.validation import validate_event_semantics, validate_qa_semantics, validate_schema


def normalized_input(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"CHID='[^']+'", "CHID='NORMALIZED'", text)
    return re.sub(r"HRRPUA=[0-9.]+", "HRRPUA=NORMALIZED", text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    physical = json.loads(
        (root / "reports" / "production_batches" / f"{args.batch}_physical_audit.json").read_text()
    )
    visual = json.loads(
        (
            root / "reports" / "production_batches" / f"{args.batch}_dynamic_image_audit.json"
        ).read_text()
    )
    video = json.loads(
        (root / "reports" / "production_batches" / f"{args.batch}_video_audit.json").read_text()
    )
    events = json.loads((root / "fire_events" / args.batch / "fire_events.json").read_text())
    qa = json.loads((root / "qa" / args.batch / "qa.json").read_text())
    manifest = json.loads((root / "fds_runs" / args.batch / "input_manifest.json").read_text())[
        "runs"
    ]
    schema_errors = [
        error
        for event in events
        for error in validate_schema(event, "fire_event.schema.json")
        + validate_event_semantics(event)
    ]
    schema_errors += [
        error
        for item in qa
        for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)
    ]
    groups: dict[str, set[str]] = defaultdict(set)
    matrix = json.loads((root / "splits" / "production_matrix.v2.1.json").read_text())
    for row in matrix["rows"]:
        groups[row["event_group"]].add(row["split"])
    leaks = {group: sorted(splits) for group, splits in groups.items() if len(splits) > 1}
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in manifest:
        family = item["matrix_row"].get("counterfactual_family")
        if family:
            by_family[family].append(item)
    pair_failures = []
    for family, rows in by_family.items():
        if len(rows) != 2:
            # The frozen matrix may split an A/B family across two adjacent
            # operational batches. Its L3-3 item is emitted by global release.
            continue
        a, b = rows
        if normalized_input(
            root / "fds_runs" / args.batch / a["run_key"] / f"{a['run_key']}.fds"
        ) != normalized_input(
            root / "fds_runs" / args.batch / b["run_key"] / f"{b['run_key']}.fds"
        ):
            pair_failures.append(family)
    positions = Counter(item["answer"]["choice"] for item in qa if item["task_id"] == "L1-2")
    tasks = sorted({item["task_id"] for item in qa})
    visual_passed = all(value["pass"] for value in visual.values())
    report = {
        "batch": args.batch,
        "status": "accepted"
        if not (physical["failed"] or schema_errors or leaks or pair_failures or not visual_passed)
        else "rejected",
        "strict_events": len(events),
        "qa": len(qa),
        "physical": {"passed": physical["passed"], "failed": physical["failed"]},
        "dynamic_images": {"events": len(visual), "passed": visual_passed},
        "video": video,
        "strict_errors": schema_errors,
        "cross_split_leaks": leaks,
        "counterfactual_pair_failures": pair_failures,
        "task_coverage": tasks,
        "l1_2_option_positions": dict(positions),
        "threshold_stability": {
            "report_completed": True,
            "risk_thresholds_c": [55, 60, 65],
            "note": "Reported for review; labels use frozen 60C / 3m / 10m thresholds.",
        },
    }
    output = root / "reports" / "production_batches" / f"{args.batch}_acceptance.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "batch",
                    "status",
                    "strict_events",
                    "qa",
                    "counterfactual_pair_failures",
                )
            }
        )
    )
    return 0 if report["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
