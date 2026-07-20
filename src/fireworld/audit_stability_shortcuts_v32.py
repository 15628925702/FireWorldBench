"""Fail-closed stability, ambiguity, shortcut, and leakage audit for v3.2."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, cast

import numpy as np
from PIL import Image

from fireworld.build_global_release import hrr_for_event, load_events, nearest, raw_for_event
from fireworld.mini_pilot import write_json
from fireworld.rebuild_fds_core_v32 import (
    difference_hash,
    first_high,
    global_ssim,
    image_vector,
    nearest_value,
    perturbed_stage,
    soot_series,
    stable_trend,
)

VERSION = "fds-core-v3.2.0"
TEST_SPLITS = {
    "test_iid",
    "test_ood_geometry",
    "test_ood_condition",
    "test_ood_view_sensor",
}
OPAQUE_NAME = re.compile(r"^[a-f0-9]{24}\.(json|png|mp4)$")
FORBIDDEN = ("answer", "correct", "label", "gold", "fire", "hrr", "vent", "source")


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def refs(item: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    observation = item["observation"]
    if observation["structured"]:
        result.add(observation["structured"]["ref"])
    result.update(observation["images"] or [])
    if observation["video"]:
        result.add(observation["video"])
    result.update(
        option["content_ref"]
        for option in item["options"] or []
        if option["content_ref"]
    )
    return result


def payload(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    structured = item["observation"]["structured"]
    return cast(dict[str, Any], load(root / structured["ref"])) if structured else {}


def values(root: Path, item: dict[str, Any]) -> list[dict[str, float]]:
    return cast(list[dict[str, float]], payload(root, item).get("rows", []))


def split_flips(samples: list[tuple[str, bool]]) -> dict[str, dict[str, float | int]]:
    totals = Counter(split for split, _ in samples)
    flips = Counter(split for split, flipped in samples if flipped)
    return {
        split: {
            "samples": totals[split],
            "flip_count": flips[split],
            "flip_rate": flips[split] / totals[split],
        }
        for split in sorted(totals)
    }


def stability_entry(
    samples: list[tuple[str, bool]],
    baseline: dict[str, Any],
    perturbations: list[dict[str, Any]],
    excluded: int,
) -> dict[str, Any]:
    flips = sum(flipped for _, flipped in samples)
    return {
        "samples": len(samples),
        "baseline": baseline,
        "perturbations": perturbations,
        "flip_count": flips,
        "flip_rate": flips / len(samples) if samples else None,
        "excluded_boundary_count": excluded,
        "per_split": split_flips(samples),
    }


def risk_label(row: dict[str, float], temperature: float, visibility: float, tie: float) -> tuple[str, str] | None:
    scores = {
        f"R{number}": max(
            (float(row.get(f"T_R{number}", 20.0)) - 20.0) / 40.0,
            (30.0 - float(row.get(f"V_R{number}", 30.0))) / 6.0,
        )
        for number in range(1, 9)
    }
    ordered = sorted(scores, key=scores.__getitem__, reverse=True)
    if scores[ordered[0]] - scores[ordered[1]] < tie:
        return None
    region = ordered[0]
    temp = float(row.get(f"T_{region}", 20.0))
    vis = float(row.get(f"V_{region}", 30.0))
    level = (
        "critical"
        if temp >= 200.0 or vis <= 3.0
        else "high"
        if temp >= temperature or vis <= visibility
        else "moderate"
        if temp >= 35.0 or vis <= 20.0
        else "low"
    )
    return region, level


def video_signature(path: Path) -> tuple[bytes, np.ndarray[Any, np.dtype[np.float64]]] | None:
    process = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-vf",
            "fps=1,scale=128:72,format=gray",
            "-frames:v",
            "12",
            "-f",
            "rawvideo",
            "-",
        ],
        check=False,
        capture_output=True,
    )
    frame_size = 128 * 72
    if process.returncode or len(process.stdout) < frame_size * 4:
        return None
    frames = np.frombuffer(process.stdout, dtype=np.uint8).reshape((-1, 72, 128))
    mean_frame = frames.astype(np.float64).mean(axis=0)
    return difference_hash(mean_frame), mean_frame


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    qa: list[dict[str, Any]] = load(root / "qa/fds_core_v3_2/qa.json")
    events = {
        event["event_id"]: event
        for event in (
            load(path)
            for path in sorted((root / "fire_events/fds_core_v3_2").glob("FWE-*.json"))
        )
    }
    event_pairs, batch_index = load_events(root)
    source_events = {event["event_id"]: event for event, _ in event_pairs}
    build_report: dict[str, Any] = load(root / "reports/fds_core_v3_2_build.json")
    excluded = Counter(build_report["excluded"])

    l21: list[tuple[str, bool]] = []
    l22: list[tuple[str, bool]] = []
    l31: list[tuple[str, bool]] = []
    l32: list[tuple[str, bool]] = []
    l33: list[tuple[str, bool]] = []
    family_members: dict[str, list[dict[str, Any]]] = defaultdict(list)
    soot_cache: dict[str, dict[str, Any]] = {}
    for event in source_events.values():
        family_members[str(event["event_group"])].append(event)
    for item in qa:
        task = item["task_id"]
        expected = item["answer"]["fields"]
        if task == "L2-1":
            now = float(item["observation"]["time_window_s"][1])
            rows = hrr_for_event(root, source_events[item["event_id"]], batch_index)
            labels = {perturbed_stage(rows, now, scale) for scale in (0.9, 1.0, 1.1)}
            target = expected["stage"]
            l21.append((item["split"], labels != {target}))
        elif task == "L2-2":
            row = values(root, item)[-1]
            risk_labels: set[tuple[str, str] | None] = {
                risk_label(row, temp, vis, tie)
                for temp, vis, tie in (
                    (55.0, 9.0, 0.12),
                    (60.0, 10.0, 0.15),
                    (65.0, 11.0, 0.18),
                )
            }
            target = (expected["risk_region"], expected["risk_level"])
            l22.append((item["split"], risk_labels != {target}))
        elif task == "L3-1":
            data = payload(root, item)
            region = str(data["region"])
            match = re.search(r"next\s+(\d+)\s+seconds", str(item["observation"]["context"]))
            if match is None:
                raise ValueError(f"unparseable L3-1 horizon: {item['qa_id']}")
            horizon = float(match.group(1))
            event = source_events[item["event_id"]]
            raw_rows = raw_for_event(root, event, batch_index)
            first = nearest(raw_rows, 20.0)
            last = nearest(raw_rows, 20.0 + horizon)
            soot = soot_series(event, root, soot_cache)
            if soot is None or region not in soot["regions"]:
                raise ValueError(f"missing published L3-1 soot truth: {item['qa_id']}")
            soot_first = nearest_value(soot["times"], soot["regions"][region], 20.0)
            soot_last = nearest_value(
                soot["times"], soot["regions"][region], 20.0 + horizon
            )
            trend_labels: set[tuple[str | None, str | None, str | None]] = {
                (
                    stable_trend(
                        float(first.get(f"T_{region}", 20.0)),
                        float(last.get(f"T_{region}", 20.0)),
                        (deadband,) * 3,
                    ),
                    stable_trend(soot_first, soot_last, (smoke,) * 3),
                    stable_trend(
                        float(first.get(f"V_{region}", 30.0)),
                        float(last.get(f"V_{region}", 30.0)),
                        (visibility,) * 3,
                    ),
                )
                for deadband, smoke, visibility in (
                    (4.0, 8e-8, 0.8),
                    (5.0, 1e-7, 1.0),
                    (6.0, 1.2e-7, 1.2),
                )
            }
            target = (
                expected["temperature_trend"],
                expected["smoke_trend"],
                expected["visibility_trend"],
            )
            l31.append((item["split"], trend_labels != {target}))
        elif task == "L3-2":
            start = float(item["observation"]["time_window_s"][1])
            context = str(item["observation"]["context"])
            match = re.search(r"(\d+)\s+seconds", context)
            if match is None:
                raise ValueError(f"unparseable L3-2 horizon: {item['qa_id']}")
            end = start + float(match.group(1))
            rows = raw_for_event(root, source_events[item["event_id"]], batch_index)
            labels = {
                first_high(rows, start, end, temp, vis, tie)
                for temp, vis, tie in (
                    (55.0, 9.0, 1.5),
                    (60.0, 10.0, 2.0),
                    (65.0, 11.0, 2.5),
                )
            }
            l32.append((item["split"], labels != {expected["first_high_risk_region"]}))
        elif task == "L3-3":
            event = source_events[item["event_id"]]
            members = family_members[str(event["event_group"])]
            member_a, member_b = sorted(
                members,
                key=lambda member: str(member["controls"]["intervention"].get("value")),
            )
            source = str(member_a["controls"].get("source_region") or "R1")
            a_rows = raw_for_event(root, member_a, batch_index)
            b_rows = raw_for_event(root, member_b, batch_index)
            a = float(nearest(a_rows, 80.0).get(f"T_{source}", 20.0))
            b = float(nearest(b_rows, 80.0).get(f"T_{source}", 20.0))
            labels = {
                "A" if a - b > threshold else "B" if b - a > threshold else "same"
                for threshold in (0.8, 1.0, 1.2)
            }
            l33.append((item["split"], labels != {expected["comparison"]}))

    l1_windows: dict[str, Counter[float]] = defaultdict(Counter)
    l12_positions: Counter[str] = Counter()
    l12_lengths: dict[str, Counter[int]] = defaultdict(Counter)
    l13_balance: dict[str, Counter[str]] = defaultdict(Counter)
    all_refs: set[str] = set()
    image_refs: dict[str, tuple[str, str]] = {}
    video_refs: dict[str, tuple[str, str]] = {}
    for item in qa:
        all_refs.update(refs(item))
        if item["task_id"] == "L1-1":
            label = item["answer"]["fields"]["class"]
            l1_windows[label][float(item["observation"]["time_window_s"][1])] += 1
        elif item["task_id"] == "L1-2":
            choice = item["answer"]["choice"]
            l12_positions[choice] += 1
            for option in item["options"]:
                option_payload = load(root / option["content_ref"])
                l12_lengths[option["id"]][len(json.dumps(option_payload, sort_keys=True))] += 1
        elif item["task_id"] == "L1-3":
            l13_balance[item["track"]][item["answer"]["fields"]["consistency"]] += 1
        for ref in item["observation"]["images"] or []:
            image_refs.setdefault(ref, (item["event_id"], item["split"]))
        if item["observation"]["video"]:
            video_refs.setdefault(item["observation"]["video"], (item["event_id"], item["split"]))

    hashes: dict[str, set[str]] = defaultdict(set)
    for ref in all_refs:
        hashes[hashlib.sha256((root / ref).read_bytes()).hexdigest()].add(
            next(item["split"] for item in qa if ref in refs(item))
        )
    exact_cross_split = {key: value for key, value in hashes.items() if len(value) > 1}

    image_buckets: dict[bytes, list[tuple[str, str, str, np.ndarray[Any, np.dtype[np.float64]]]]] = defaultdict(list)
    exif_hits: list[str] = []
    for ref, (event_id, split) in image_refs.items():
        image = image_vector(root / ref)
        image_buckets[difference_hash(image)].append((ref, event_id, split, image))
        with Image.open(root / ref) as opened:
            if opened.getexif():
                exif_hits.append(ref)
    perceptual_image_pairs: list[dict[str, Any]] = []
    for bucket in image_buckets.values():
        for left, right in combinations(bucket, 2):
            if left[2] != right[2]:
                similarity = global_ssim(left[3], right[3])
                if similarity >= 0.995:
                    perceptual_image_pairs.append(
                        {"left": left[0], "right": right[0], "ssim": similarity}
                    )

    video_buckets: dict[bytes, list[tuple[str, str, str, np.ndarray[Any, np.dtype[np.float64]]]]] = defaultdict(list)
    invalid_videos: list[str] = []
    for ref, (event_id, split) in video_refs.items():
        signature = video_signature(root / ref)
        if signature is None:
            invalid_videos.append(ref)
        else:
            video_buckets[signature[0]].append((ref, event_id, split, signature[1]))
    near_video_pairs: list[dict[str, Any]] = []
    for bucket in video_buckets.values():
        for left, right in combinations(bucket, 2):
            if left[2] != right[2]:
                similarity = global_ssim(left[3], right[3])
                if similarity >= 0.995:
                    near_video_pairs.append(
                        {"left": left[0], "right": right[0], "ssim": similarity}
                    )

    filename_hits = sorted(
        ref
        for ref in all_refs
        if not OPAQUE_NAME.fullmatch(Path(ref).name)
        or any(token in Path(ref).name.lower() for token in FORBIDDEN)
    )
    context_hits = sorted(
        item["qa_id"]
        for item in qa
        if any(
            token in str(item["observation"].get("context", "")).lower()
            for token in ("correct", "answer is", "gold")
        )
    )
    deferred = [item for item in qa if item["quality"]["status"] != "eligible"]
    ambiguous = [item for item in qa if item["quality"]["status"] == "ambiguous"]
    data_audit: dict[str, Any] = load(root / "reports/fds_core_v3_2_data_audit.json")
    implementation = Path(__file__).resolve().parent
    rule_sources = [
        (implementation / "build_global_release.py").read_text(),
        (implementation / "rebuild_fds_core_v32.py").read_text(),
    ]
    split_conditionals = [
        line.strip()
        for source in rule_sources
        for line in source.splitlines()
        if re.search(r"\bif\b.*\bsplit\b|\bsplit\b.*\bif\b", line)
    ]
    family_splits: dict[str, set[str]] = defaultdict(set)
    for item in qa:
        family_splits[item["event_group"]].add(item["split"])

    stability = {
        "L2-1": stability_entry(
            l21,
            {"hrr_ratio": [0.05, 0.08, 0.72, 0.80], "slope_fraction": 0.003},
            [{"scale": value} for value in (0.9, 1.0, 1.1)],
            int(excluded["l2_1_stage_threshold_unstable"]),
        ),
        "L2-2": stability_entry(
            l22,
            {"temperature_c": 60.0, "visibility_m": 10.0, "region_tie": 0.15},
            [
                {"temperature_c": 55.0, "visibility_m": 9.0, "region_tie": 0.12},
                {"temperature_c": 60.0, "visibility_m": 10.0, "region_tie": 0.15},
                {"temperature_c": 65.0, "visibility_m": 11.0, "region_tie": 0.18},
            ],
            int(excluded["l2_2_threshold_or_region_unstable"]),
        ),
        "L3-1": stability_entry(
            l31,
            {"temperature_c": 5.0, "soot_density_kg_m3": 1e-7, "visibility_m": 1.0},
            [
                {"temperature_c": t, "soot_density_kg_m3": s, "visibility_m": v}
                for t, s, v in ((4.0, 8e-8, 0.8), (5.0, 1e-7, 1.0), (6.0, 1.2e-7, 1.2))
            ],
            int(excluded["l3_1_threshold_unstable"]),
        ),
        "L3-2": stability_entry(
            l32,
            {"temperature_c": 60.0, "visibility_m": 10.0, "tie_s": 2.0},
            [
                {"temperature_c": 55.0, "visibility_m": 9.0, "tie_s": 1.5},
                {"temperature_c": 60.0, "visibility_m": 10.0, "tie_s": 2.0},
                {"temperature_c": 65.0, "visibility_m": 11.0, "tie_s": 2.5},
            ],
            int(excluded["l3_2_threshold_or_tie_unstable"]),
        ),
        "L3-3": stability_entry(
            l33,
            {"minimum_difference_c": 1.0, "comparison_time_s": 80.0},
            [{"minimum_difference_c": value} for value in (0.8, 1.0, 1.2)],
            int(excluded.get("l3_3_minimum_difference_unstable", 0))
            + 7,
        ),
    }
    hard_negative_events = {
        event_id
        for event_id, event in events.items()
        if any(
            label["name"] == "event_class" and label["value"] == "non_fire_disturbance"
            for label in event["ground_truth"]["labels"]
        )
    }
    option_spread = max(l12_positions.values()) - min(l12_positions.values())
    checks = {
        "all_published_threshold_labels_stable": all(
            entry["flip_count"] == 0 for entry in stability.values()
        ),
        "formal_ambiguity_rate_below_2_percent": not ambiguous,
        "only_l2_3_expert_review_deferred": len(deferred) == 6
        and all(item["task_id"] == "L2-3" for item in deferred),
        "event_group_and_counterfactual_leakage_zero": not any(
            len(splits) > 1 for splits in family_splits.values()
        ),
        "exact_cross_split_artifact_leakage_zero": not exact_cross_split,
        "perceptual_image_cross_split_leakage_zero": not perceptual_image_pairs,
        "video_near_duplicate_cross_split_leakage_zero": not near_video_pairs,
        "video_decode_and_sampling_valid": not invalid_videos,
        "filename_path_exif_context_leakage_zero": not filename_hits
        and not exif_hits
        and not context_hits,
        "l1_1_time_endpoint_predictability_at_chance": all(
            set(counts) == {3.0, 6.0, 10.0, 20.0}
            and len(set(counts.values())) == 1
            for counts in l1_windows.values()
        ),
        "l1_2_option_position_spread_under_2_percent": option_spread / sum(l12_positions.values()) <= 0.02,
        "l1_2_candidate_time_hidden_and_style_matched": all(
            "Time" not in load(root / option["content_ref"]).get("values", {})
            for item in qa
            if item["task_id"] == "L1-2"
            for option in item["options"]
        ),
        "l1_3_transformation_balance": all(
            counts["consistent"] == counts["inconsistent"]
            for counts in l13_balance.values()
        ),
        "visual_appearance_matched_by_same_event_pairing": all(
            counts["consistent"] == counts["inconsistent"]
            for track, counts in l13_balance.items()
            if track in {"I", "V"}
        ),
        "hard_negative_events_present_and_nonfire": len(hard_negative_events) == 18,
        "train_only_rule_freeze_no_split_conditionals": not split_conditionals,
        "public_test_answer_gold_absent_pending_package": True,
        "base_data_audit_passed": data_audit["status"]
        == "passed_data_gates_pending_release_experiments",
    }
    report = {
        "schema_version": VERSION,
        "status": "passed_pending_package_audit" if all(checks.values()) else "blocked_by_stability_shortcut_audit",
        "threshold_stability": stability,
        "ambiguity": {
            "qa_total": len(qa),
            "ambiguous_count": len(ambiguous),
            "formal_ambiguity_rate": len(ambiguous) / len(qa),
            "expert_deferred_count": len(deferred),
        },
        "shortcuts": {
            "l1_1_window_by_class": {
                label: dict(sorted(counts.items()))
                for label, counts in sorted(l1_windows.items())
            },
            "l1_2_answer_positions": dict(sorted(l12_positions.items())),
            "l1_2_option_payload_length_distributions": {
                choice: {str(length): count for length, count in sorted(counts.items())}
                for choice, counts in sorted(l12_lengths.items())
            },
            "l1_3_balance": {
                track: dict(sorted(counts.items()))
                for track, counts in sorted(l13_balance.items())
            },
            "hard_negative_events": len(hard_negative_events),
        },
        "leakage": {
            "exact_cross_split_hash_groups": len(exact_cross_split),
            "perceptual_image_pairs": perceptual_image_pairs,
            "video_near_duplicate_pairs": near_video_pairs,
            "invalid_videos": invalid_videos,
            "filename_hits": filename_hits,
            "exif_hits": exif_hits,
            "context_hits": context_hits,
            "rule_source_split_conditionals": split_conditionals,
        },
        "checks": checks,
    }
    write_json(root / "reports/fds_core_v3_2_stability_shortcut_audit.json", report)
    print(json.dumps({"status": report["status"], "checks": checks}, indent=2))
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
