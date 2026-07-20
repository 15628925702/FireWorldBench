"""Threshold, ambiguity, and shortcut audits for the self-contained v3 release."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image

from fireworld.mini_pilot import write_json


def risk_level(row: dict[str, Any], temperature: float, visibility: float) -> str:
    values = []
    for number in range(1, 9):
        region = f"R{number}"
        score = max(
            (float(row.get(f"T_{region}", 20.0)) - 20.0) / 40.0,
            (30.0 - float(row.get(f"V_{region}", 30.0))) / 6.0,
        )
        values.append((score, region))
    _, region = max(values)
    temp = float(row.get(f"T_{region}", 20.0))
    vis = float(row.get(f"V_{region}", 30.0))
    if temp >= 200.0 or vis <= 3.0:
        return "critical"
    if temp >= temperature or vis <= visibility:
        return "high"
    if temp >= 35.0 or vis <= 20.0:
        return "moderate"
    return "low"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    release = root / "release" / "fireworldbench_v3_provisional" / "public"
    train_dev = json.loads((release / "qa_train_dev.json").read_text())
    tests = json.loads((release / "qa_test_questions.json").read_text())
    private = json.loads((release.parent / "private" / "qa_test_gold.json").read_text())
    qa = train_dev + private
    perturbations = ((55.0, 9.0), (60.0, 10.0), (65.0, 11.0))
    l2 = [item for item in qa if item["task_id"] == "L2-2" and item["track"] == "S"]
    flips = 0
    for item in l2:
        ref = item["observation"]["structured"]["ref"]
        rows = json.loads((release / ref).read_text())["rows"]
        labels = [risk_level(rows[-1], temp, vis) for temp, vis in perturbations]
        if len(set(labels)) > 1:
            flips += 1
    refs: list[str] = []
    for item in qa:
        obs = item["observation"]
        if obs["structured"]:
            refs.append(obs["structured"]["ref"])
        refs.extend(obs["images"] or [])
        if obs["video"]:
            refs.append(obs["video"])
        refs.extend(
            option["content_ref"] for option in item["options"] or [] if option["content_ref"]
        )
    forbidden = ("fire", "hrr", "vent", "risk", "train", "dev", "test", "answer")
    path_hits = [ref for ref in refs if any(token in Path(ref).name.lower() for token in forbidden)]
    image_refs = sorted({ref for ref in refs if ref.lower().endswith(".png")})
    exif_hits = []
    for ref in image_refs:
        with Image.open(release / ref) as image:
            if image.getexif():
                exif_hits.append(ref)
    window_label_counts: dict[str, Counter[float]] = {}
    for item in qa:
        if item["task_id"] != "L1-1":
            continue
        label = item["answer"]["fields"]["class"]
        window_label_counts.setdefault(label, Counter())[
            item["observation"]["time_window_s"][1]
        ] += 1
    ambiguous = [item for item in qa if item["quality"]["status"] != "eligible"]
    report = {
        "schema_version": "3.0.0",
        "release": "fireworldbench_v3_provisional",
        "threshold_stability": {
            "task": "L2-2",
            "samples": len(l2),
            "perturbations": [
                {"high_temperature_c": temp, "high_visibility_m": vis}
                for temp, vis in perturbations
            ],
            "flip_count": flips,
            "flip_rate": flips / len(l2) if l2 else None,
        },
        "ambiguity": {
            "all_qa_noneligible": len(ambiguous),
            "test_noneligible": sum(item["quality"]["status"] != "eligible" for item in private),
            "deferred_reason": "mechanism independent review deferred by user",
        },
        "shortcut": {
            "path_forbidden_token_hits": path_hits,
            "image_exif_hits": exif_hits,
            "l1_1_window_end_by_class": {
                key: dict(value) for key, value in window_label_counts.items()
            },
            "test_public_answers_nonempty": sum(
                bool(item["answer"]["choice"] or item["answer"]["fields"]) for item in tests
            ),
        },
    }
    write_json(root / "reports" / "protocol_rebuild_v3_quality_audit.json", report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
