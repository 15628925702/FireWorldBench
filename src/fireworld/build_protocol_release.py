"""Build a self-contained provisional v3 release from audited protocol evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from collections import Counter
from itertools import pairwise
from pathlib import Path
from typing import Any, cast

from PIL import Image, ImageChops, ImageStat

from fireworld.build_global_release import digest, load_events, qa
from fireworld.mini_pilot import write_json
from fireworld.validation import validate_event_groups, validate_qa_semantics, validate_schema

VERSION = "protocol-release-v3.0.0"
TEST_SPLITS = {"test_iid", "test_ood_geometry", "test_ood_condition", "test_ood_view_sensor"}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hardlink(source: str | Path, destination: str | Path) -> None:
    source = Path(source)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    os.link(source, destination)


def image_delta(paths: list[Path]) -> float:
    values: list[float] = []
    for first, second in pairwise(paths):
        with Image.open(first).convert("RGB") as a, Image.open(second).convert("RGB") as b:
            values.append(sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3.0)
    return max(values, default=0.0)


def video_ok(path: Path) -> tuple[bool, float]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        return False, 0.0
    try:
        duration = float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False, 0.0
    return 4.0 <= duration <= 12.0, duration


def public_question(item: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(item))
    clone["answer"] = {"choice": None, "fields": {}}
    return cast(dict[str, Any], clone)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    audit = json.loads((root / "reports" / "protocol_rebuild_v3_audit.json").read_text())
    if audit["release_status"] != "provisionally_accepted_expert_review_deferred":
        raise ValueError("protocol candidate is not provisionally accepted")
    release = root / "release" / "fireworldbench_v3_provisional"
    if release.exists():
        raise ValueError(f"release already exists: {release}")
    public, private = release / "public", release / "private"
    public.mkdir(parents=True)
    private.mkdir(parents=True)
    event_pairs, _ = load_events(root)
    qa_rows: list[dict[str, Any]] = json.loads(
        (root / "qa" / "protocol_rebuild_v3" / "qa.json").read_text()
    )
    # I examples are a deterministic release derivation. Remove the previous
    # derivation before rebuilding so reruns cannot duplicate QA records.
    qa_rows = [
        item
        for item in qa_rows
        if not (
            item["track"] == "I"
            and item["task_id"] == "L1-3"
            and item["provenance"]["builder_version"] == "protocol-rebuild-v3.0.0"
        )
    ]
    event_by_id = {event["event_id"]: event for event, _ in event_pairs}
    split_by_id = {event["event_id"]: split for event, split in event_pairs}
    visual_report: list[dict[str, Any]] = []
    rebuilt: dict[str, dict[str, Any]] = {}
    for event_id, original in sorted(event_by_id.items()):
        event = json.loads(json.dumps(original))
        images = original["observations"].get("images") or []
        image_paths = [root / item["ref"] for item in images]
        image_valid = bool(images) and all(path.is_file() for path in image_paths)
        delta = image_delta(image_paths) if image_valid and len(image_paths) > 1 else 0.0
        image_valid = (
            image_valid and len({file_hash(path) for path in image_paths}) > 1 and delta > 0.25
        )
        copied_images: list[dict[str, Any]] | None = None
        if image_valid:
            copied_images = []
            for item, source in zip(images, image_paths, strict=True):
                destination = (
                    root / "derived" / "protocol_rebuild_v3" / "I" / event_id / source.name
                )
                hardlink(source, destination)
                copied_images.append(
                    {
                        "ref": str(destination.relative_to(root)),
                        "time_s": item["time_s"],
                        "sha256": file_hash(destination),
                    }
                )
        video = original["observations"].get("video")
        video_valid, duration = (False, 0.0)
        copied_video: dict[str, Any] | None = None
        if video and (source := root / video["ref"]).is_file():
            video_valid, duration = video_ok(source)
            if video_valid:
                destination = (
                    root / "derived" / "protocol_rebuild_v3" / "V" / event_id / source.name
                )
                hardlink(source, destination)
                copied_video = {
                    **video,
                    "ref": str(destination.relative_to(root)),
                    "duration_s": duration,
                    "sha256": file_hash(destination),
                }
        event["observations"]["images"] = copied_images
        event["observations"]["video"] = copied_video
        canonical_s = (
            root / "derived" / "protocol_rebuild_v3" / "S" / event_id / "state" / "t20.json"
        )
        if not canonical_s.is_file():
            raise ValueError(f"missing canonical bounded observation: {canonical_s}")
        event["observations"]["structured"] = {
            "ref": str(canonical_s.relative_to(root)),
            "format": "json",
            "variables": ["temperature", "visibility", "u_velocity"],
            "units_normalized": True,
        }
        event["provenance"]["transform_version"] = VERSION
        path = root / "fire_events" / "protocol_rebuild_v3" / f"{event_id}.json"
        write_json(path, event)
        rebuilt[event_id] = event
        visual_report.append(
            {
                "event_id": event_id,
                "images_published": len(copied_images or []),
                "image_delta": delta,
                "video_published": bool(copied_video),
                "video_duration_s": duration,
            }
        )
    # Rebind every QA to the versioned Event manifest.
    for item in qa_rows:
        item["provenance"]["event_manifest_sha256"] = digest(rebuilt[item["event_id"]])
    # Add genuine I temporal-coherence examples only where dynamic keyframes passed audit.
    for event_id, event in rebuilt.items():
        refs = [item["ref"] for item in event["observations"]["images"] or []]
        if len(refs) < 2:
            continue
        split = split_by_id[event_id]
        ordered = refs[:4]
        for ordinal, inconsistent in enumerate((False, True), 1):
            shown = ordered if not inconsistent else ordered[:1] + list(reversed(ordered[1:]))
            obs = {
                "structured": None,
                "images": shown,
                "video": None,
                "context": "Audited ordered dynamic Smokeview keyframes.",
                "time_window_s": [20.0, 110.0],
            }
            fields = {
                "consistency": "inconsistent" if inconsistent else "consistent",
                "violation_type": "reverse" if inconsistent else None,
            }
            image_qa = qa(
                event,
                split,
                "L1-3",
                200 + ordinal,
                obs,
                fields,
                "Are these keyframes temporally consistent?",
            )
            image_qa["track"] = "I"
            qa_rows.append(image_qa)
    errors = [
        error
        for item in qa_rows
        for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)
    ]
    errors += validate_event_groups(qa_rows)
    if errors:
        raise ValueError("release QA validation failed: " + "; ".join(errors[:10]))
    qa_root = root / "qa" / "protocol_rebuild_v3"
    write_json(qa_root / "qa.json", qa_rows)
    # A hardlinked copy makes all QA refs resolvable from public/ without duplicating large assets.
    shutil.copytree(
        root / "derived" / "protocol_rebuild_v3",
        public / "derived" / "protocol_rebuild_v3",
        copy_function=hardlink,
    )
    shutil.copytree(
        root / "fire_events" / "protocol_rebuild_v3",
        public / "fire_events" / "protocol_rebuild_v3",
        copy_function=hardlink,
    )
    train_dev = [item for item in qa_rows if item["split"] not in TEST_SPLITS]
    tests = [item for item in qa_rows if item["split"] in TEST_SPLITS]
    write_json(public / "qa_train_dev.json", train_dev)
    write_json(public / "qa_test_questions.json", [public_question(item) for item in tests])
    write_json(private / "qa_test_gold.json", tests)
    shutil.copy2(
        root / "splits" / "production_matrix.v2.1.json", public / "production_matrix.v2.1.json"
    )
    write_json(
        root / "reports" / "protocol_rebuild_v3_visual_audit.json",
        {
            "events": len(visual_report),
            "images_published_events": sum(item["images_published"] > 0 for item in visual_report),
            "videos_published_events": sum(item["video_published"] for item in visual_report),
            "items": visual_report,
        },
    )
    report = {
        "schema_version": "3.0.0",
        "status": "provisionally_accepted_expert_review_deferred",
        "events": len(rebuilt),
        "qa": len(qa_rows),
        "tracks": dict(Counter(item["track"] for item in qa_rows)),
        "visual_assets": {
            "image_events": sum(item["images_published"] > 0 for item in visual_report),
            "video_events": sum(item["video_published"] for item in visual_report),
        },
        "test_answers_private": len(tests),
        "engineering_review": "deferred_by_user; not formal PDF acceptance",
    }
    write_json(release / "release_manifest.json", report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
