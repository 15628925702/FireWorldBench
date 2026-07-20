"""Create one audited continuous-time video from dynamic production images."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    events = json.loads((root / "fire_events" / args.batch / "fire_events.json").read_text())
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
        print("no fire event; no video published")
        return 0
    event_id = event["event_id"]
    image_dir = root / "derived" / args.batch / "I" / event_id
    images = [image_dir / f"{event_id.lower()}_t{time_s:03d}.png" for time_s in (20, 50, 80, 110)]
    if not all(image.is_file() for image in images):
        raise RuntimeError("video source frames are incomplete")
    output_dir = root / "derived" / args.batch / "V"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{event_id}_dynamic.mp4"
    command = ["ffmpeg", "-y"]
    for image in images:
        command.extend(("-loop", "1", "-t", "1.5", "-i", str(image)))
    command.extend(
        (
            "-filter_complex",
            "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0,fps=2,format=yuv420p[v]",
            "-map",
            "[v]",
            "-c:v",
            "libx264",
            "-movflags",
            "+faststart",
            str(output),
        )
    )
    subprocess.run(command, check=True, capture_output=True, text=True)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
