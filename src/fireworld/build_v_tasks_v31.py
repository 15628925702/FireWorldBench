"""Derive audited V temporal-coherence examples for the v3.1 candidate."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from fireworld.build_global_release import load_events, qa
from fireworld.mini_pilot import write_json
from fireworld.validation import validate_event_groups, validate_qa_semantics, validate_schema

VERSION = "fds-core-v3.1.0"


def probe(path: Path) -> tuple[bool, float, int]:
    duration = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if duration.returncode:
        return False, 0.0, 0
    try:
        seconds = float(json.loads(duration.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False, 0.0, 0
    hashes = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "12", "-f", "framemd5", "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    frame_hashes = [
        line.split(",")[-1] for line in hashes.stdout.splitlines() if line.startswith("0,")
    ]
    return 4.0 <= seconds <= 12.0 and len(set(frame_hashes)) > 1, seconds, len(set(frame_hashes))


def observation(ref: str, start: float, end: float) -> dict[str, Any]:
    return {
        "structured": None,
        "images": None,
        "video": ref,
        "context": "Audited continuous Smokeview video.",
        "time_window_s": [start, end],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    qa_path = root / "qa" / "fds_core_v3_1" / "qa.json"
    questions: list[dict[str, Any]] = [
        item for item in json.loads(qa_path.read_text()) if item["track"] != "V"
    ]
    event_pairs, _ = load_events(root)
    records: list[dict[str, Any]] = []
    for ordinal, (event, split) in enumerate(event_pairs, 1):
        video = event["observations"].get("video")
        if not video:
            continue
        source = root / video["ref"]
        passed, duration, unique_hashes = probe(source)
        if not passed:
            records.append(
                {"event_id": event["event_id"], "pass": False, "reason": "decode_or_motion"}
            )
            continue
        out = root / "derived" / "fds_core_v3_1" / "V" / event["event_id"]
        out.mkdir(parents=True, exist_ok=True)
        transformed = out / "sequence_reverse.mp4"
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-i",
                str(source),
                "-vf",
                "reverse",
                "-an",
                str(transformed),
            ],
            check=False,
        )
        transformed_passed, transformed_duration, transformed_hashes = probe(transformed)
        if result.returncode or not transformed_passed:
            records.append(
                {"event_id": event["event_id"], "pass": False, "reason": "reverse_render"}
            )
            continue
        start = float(video["start_s"])
        end = start + duration
        for item_ordinal, (ref, consistency, violation) in enumerate(
            (
                (video["ref"], "consistent", None),
                (str(transformed.relative_to(root)), "inconsistent", "reverse"),
            ),
            1,
        ):
            row = qa(
                event,
                split,
                "L1-3",
                3000 + ordinal * 10 + item_ordinal,
                observation(ref, start, end),
                {"consistency": consistency, "violation_type": violation},
                "Is this video temporally consistent?",
            )
            row["track"] = "V"
            row["provenance"]["builder_version"] = VERSION
            questions.append(row)
        records.append(
            {
                "event_id": event["event_id"],
                "pass": True,
                "duration_s": duration,
                "source_unique_frame_hashes": unique_hashes,
                "reverse_duration_s": transformed_duration,
                "reverse_unique_frame_hashes": transformed_hashes,
            }
        )
    errors = [
        error
        for item in questions
        for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)
    ]
    errors += validate_event_groups(questions)
    if errors:
        raise ValueError("V task validation failed: " + "; ".join(errors[:10]))
    write_json(qa_path, questions)
    report = {
        "version": VERSION,
        "eligible_video_events": sum(item["pass"] for item in records),
        "published_v_qa": sum(item["track"] == "V" for item in questions),
        "records": records,
        "validation_errors": len(errors),
    }
    write_json(root / "reports" / "fds_core_v3_1_v_task_audit.json", report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
