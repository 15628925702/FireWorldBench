"""Render replacement I/V evidence from the new v3.2 physical trajectories."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from fireworld.mini_pilot import write_json
from fireworld.render_explicit_observation_images import render

BATCH = "trajectory_repair_v3_2"


def is_fire(item: dict[str, Any]) -> bool:
    return bool(item["matrix_row"]["event_class"] == "fire")


def video(root: Path, event_id: str, reverse: bool = False) -> str:
    source = root / "derived" / BATCH / "I" / event_id
    times = (110, 80, 50, 20) if reverse else (20, 50, 80, 110)
    images = [source / f"{event_id.lower()}_t{time_s:03d}.png" for time_s in times]
    role = "b" if reverse else "a"
    output = root / "derived" / BATCH / "V" / event_id / f"{role}.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-y", "-v", "error"]
    for image in images:
        command.extend(("-loop", "1", "-t", "1.5", "-i", str(image)))
    command.extend(("-filter_complex", "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0,fps=10,scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2:black,format=yuv420p[v]", "-map", "[v]", "-map_metadata", "-1", "-c:v", "libx264", "-movflags", "+faststart", str(output)))
    subprocess.run(command, check=True)
    return str(output.relative_to(root))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = json.loads((root / "fds_runs" / BATCH / "input_manifest.json").read_text())
    previous_qa = json.loads((root / "qa/fds_core_v3_1/qa.json").read_text())
    video_events = {item["event_id"] for item in previous_qa if item["track"] == "V"}
    image_report: dict[str, Any] = {}
    video_report: dict[str, Any] = {}
    for item in manifest["runs"]:
        if not is_fire(item):
            continue
        event_id = item["event_id"]
        run = root / "fds_runs" / BATCH / item["run_key"]
        images, checks = render(root, run, event_id, BATCH)
        image_report[event_id] = {"images": images, **checks}
        if event_id in video_events:
            consistent = video(root, event_id)
            inconsistent = video(root, event_id, reverse=True)
            probes = {}
            for role, ref in (("consistent", consistent), ("inconsistent", inconsistent)):
                result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=nb_frames,avg_frame_rate", "-of", "json", str(root / ref)], check=True, capture_output=True, text=True)
                metadata = json.loads(result.stdout)
                probes[role] = {"ref": ref, "sha256": hashlib.sha256((root / ref).read_bytes()).hexdigest(), "metadata": metadata}
            video_report[event_id] = probes
    report = {"schema_version": "fds-core-v3.2.0", "status": "passed", "image_events": len(image_report), "video_events": len(video_report), "images": image_report, "videos": video_report}
    write_json(root / "reports/fds_core_v3_2_trajectory_repair_visual_audit.json", report)
    print(json.dumps({key: report[key] for key in ("status", "image_events", "video_events")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
