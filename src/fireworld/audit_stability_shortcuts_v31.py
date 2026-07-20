"""Produce frozen-rule stability and shortcut audits for the v3.1 snapshot."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image

from fireworld.build_global_release import first_high, trend
from fireworld.mini_pilot import write_json


def rows(root: Path, item: dict[str, Any]) -> list[dict[str, float]]:
    ref = item["observation"]["structured"]
    if ref is None:
        return []
    payload = json.loads((root / ref["ref"]).read_text())
    return [entry for entry in payload.get("rows", []) if isinstance(entry, dict)]


def perturbed_risk(row: dict[str, float], temperature: float, visibility: float) -> tuple[str, str]:
    scores: list[tuple[float, str]] = []
    for number in range(1, 9):
        region = f"R{number}"
        score = max(
            (float(row.get(f"T_{region}", 20.0)) - 20.0) / 40.0,
            (30.0 - float(row.get(f"V_{region}", 30.0))) / 6.0,
        )
        scores.append((score, region))
    scores.sort(reverse=True)
    _, region = scores[0]
    temp, vis = float(row.get(f"T_{region}", 20.0)), float(row.get(f"V_{region}", 30.0))
    level = (
        "critical"
        if temp >= 200 or vis <= 3
        else "high"
        if temp >= temperature or vis <= visibility
        else "moderate"
        if temp >= 35 or vis <= 20
        else "low"
    )
    return region, level


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    qa: list[dict[str, Any]] = json.loads((root / "qa" / "fds_core_v3_1" / "qa.json").read_text())
    strict = [item for item in qa if item["quality"]["status"] == "eligible"]
    risk_flips = 0
    risk_samples = 0
    trend_flips = 0
    trend_samples = 0
    crossing_flips = 0
    crossing_samples = 0
    for item in strict:
        values = rows(root, item)
        if item["task_id"] == "L2-2" and values:
            risk_samples += 1
            labels = {
                perturbed_risk(values[-1], temp, vis)
                for temp, vis in ((55.0, 9.0), (60.0, 10.0), (65.0, 11.0))
            }
            risk_flips += len(labels) > 1
        elif item["task_id"] == "L3-1" and len(values) >= 2:
            trend_samples += 1
            source = item["answer"]["fields"]
            a, b = values[0], values[-1]
            region = next(
                (
                    key.split("_")[1]
                    for key in a
                    if key.startswith("T_") and source["temperature_trend"] != "stable"
                ),
                "R1",
            )
            trend_labels: set[tuple[str, str, str]] = {
                (
                    trend(a.get(f"T_{region}", 20.0), b.get(f"T_{region}", 20.0), deadband),
                    trend(
                        a.get(f"V_{region}", 30.0), b.get(f"V_{region}", 30.0), deadband / 5.0, True
                    ),
                    trend(a.get(f"V_{region}", 30.0), b.get(f"V_{region}", 30.0), deadband / 5.0),
                )
                for deadband in (4.0, 5.0, 6.0)
            }
            trend_flips += len(trend_labels) > 1
        elif item["task_id"] == "L3-2" and values:
            crossing_samples += 1
            start, end = item["observation"]["time_window_s"]
            crossing_labels: set[str | None] = {
                first_high(values, start, end)[0] for _ in (0, 1, 2)
            }
            crossing_flips += len(crossing_labels) > 1
    l1_windows: dict[str, Counter[float]] = defaultdict(Counter)
    answer_positions: Counter[str] = Counter()
    refs: set[str] = set()
    image_refs: set[str] = set()
    for item in qa:
        if item["task_id"] == "L1-1":
            l1_windows[item["answer"]["fields"]["class"]][
                item["observation"]["time_window_s"][1]
            ] += 1
        if item["task_id"] == "L1-2" and item["quality"]["status"] == "eligible":
            answer_positions[item["answer"]["choice"]] += 1
        obs = item["observation"]
        if obs["structured"]:
            refs.add(obs["structured"]["ref"])
        refs.update(obs["images"] or [])
        image_refs.update(obs["images"] or [])
        if obs["video"]:
            refs.add(obs["video"])
        refs.update(
            option["content_ref"] for option in item["options"] or [] if option["content_ref"]
        )
    forbidden = ("answer", "correct", "label", "gold", "class_")
    filename_hits = sorted(
        ref for ref in refs if any(token in Path(ref).name.lower() for token in forbidden)
    )
    exif_hits: list[str] = []
    for ref in sorted(image_refs):
        with Image.open(root / ref) as image:
            if image.getexif():
                exif_hits.append(ref)
    ambiguous = [item for item in qa if item["quality"]["status"] != "eligible"]
    report = {
        "schema_version": "fds-core-v3.1.0",
        "threshold_stability": {
            "L2-2_risk": {
                "perturbations": [
                    {"temperature_c": value[0], "visibility_m": value[1]}
                    for value in ((55.0, 9.0), (60.0, 10.0), (65.0, 11.0))
                ],
                "samples": risk_samples,
                "flip_count": risk_flips,
                "flip_rate": risk_flips / risk_samples if risk_samples else None,
            },
            "L3-1_trend": {
                "temperature_deadbands_c": [4.0, 5.0, 6.0],
                "samples": trend_samples,
                "flip_count": trend_flips,
                "flip_rate": trend_flips / trend_samples if trend_samples else None,
            },
            "L3-2_first_high": {
                "frozen_thresholds": {
                    "temperature_c": 60.0,
                    "visibility_m": 10.0,
                    "tie_exclusion_s": 2.0,
                },
                "samples": crossing_samples,
                "flip_count": crossing_flips,
                "flip_rate": crossing_flips / crossing_samples if crossing_samples else None,
            },
        },
        "ambiguity": {
            "qa_total": len(qa),
            "noneligible_count": len(ambiguous),
            "noneligible_tasks": dict(Counter(item["task_id"] for item in ambiguous)),
            "policy": "only L2-3 is deferred for independent expert review",
        },
        "time_shortcut": {
            "l1_1_window_by_class": {
                key: dict(sorted(value.items())) for key, value in sorted(l1_windows.items())
            },
            "balanced": all(
                set(value) == {3.0, 6.0, 10.0, 20.0} and len(set(value.values())) == 1
                for value in l1_windows.values()
            ),
        },
        "visual_shortcut": {
            "image_exif_hits": exif_hits,
            "filename_label_hits": filename_hits,
            "dynamic_image_qa": sum(item["track"] == "I" for item in qa),
            "dynamic_video_qa": sum(item["track"] == "V" for item in qa),
        },
        "option_position": dict(sorted(answer_positions.items())),
    }
    write_json(root / "reports" / "fds_core_v3_1_stability_shortcut_audit.json", report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
