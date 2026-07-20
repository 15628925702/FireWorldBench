"""Render and attach audited dynamic Smoke3D images for a production batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fireworld.render_explicit_observation_images import render


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    events_path = root / "fire_events" / args.batch / "fire_events.json"
    events = json.loads(events_path.read_text(encoding="utf-8"))
    manifest = json.loads(
        (root / "fds_runs" / args.batch / "input_manifest.json").read_text(encoding="utf-8")
    )["runs"]
    by_event = {item["event_id"]: item["run_key"] for item in manifest}
    report: dict[str, Any] = {}
    for event in events:
        is_fire = any(
            label["name"] == "event_class" and label["value"] == "fire"
            for label in event["ground_truth"]["labels"]
        )
        if not is_fire:
            continue
        event_id = event["event_id"]
        images, checks = render(
            root, root / "fds_runs" / args.batch / by_event[event_id], event_id, args.batch
        )
        event["observations"]["images"] = images
        report[event_id] = checks
    events_path.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
    output = root / "reports" / "production_batches" / f"{args.batch}_dynamic_image_audit.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps({"events": len(report), "passed": all(item["pass"] for item in report.values())})
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
