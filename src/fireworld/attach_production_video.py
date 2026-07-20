"""Attach one audited continuous-time video to its production Fire Event."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    events_path = root / "fire_events" / args.batch / "fire_events.json"
    events: list[dict[str, Any]] = json.loads(events_path.read_text(encoding="utf-8"))
    event = next(
        (
            item
            for item in events
            if any(
                label["name"] == "event_class" and label["value"] == "fire"
                for label in item["ground_truth"]["labels"]
            )
        ),
        None,
    )
    if event is None:
        report = root / "reports" / "production_batches" / f"{args.batch}_video_audit.json"
        report.write_text(
            json.dumps({"published": False, "reason": "batch contains no fire event"}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"published": False}))
        return 0
    video = root / "derived" / args.batch / "V" / f"{event['event_id']}_dynamic.mp4"
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_name,width,height,avg_frame_rate,nb_frames",
            "-of",
            "json",
            str(video),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    metadata = json.loads(probe.stdout)
    stream = metadata["streams"][0]
    duration = float(metadata["format"]["duration"])
    numerator, denominator = (int(value) for value in stream["avg_frame_rate"].split("/"))
    fps = numerator / denominator
    checks = {
        "codec_h264": stream["codec_name"] == "h264",
        "duration_in_range": 4 <= duration <= 12,
        "frame_count": int(stream["nb_frames"]) >= 8,
        "continuous_fps": fps > 0,
    }
    if not all(checks.values()):
        raise RuntimeError(checks)
    event["observations"]["video"] = {
        "ref": str(video.relative_to(root)),
        "start_s": 20.0,
        "duration_s": duration,
        "fps": fps,
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
    }
    events_path.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
    report = root / "reports" / "production_batches" / f"{args.batch}_video_audit.json"
    report.write_text(
        json.dumps(
            {
                "event_id": event["event_id"],
                "checks": checks,
                "metadata": metadata,
                "published_v_track_qa": 0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"event_id": event["event_id"], "checks": checks}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
