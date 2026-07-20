"""Content-level audit for the protocol-rebuild-v3 candidate release."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, cast

from fireworld.mini_pilot import write_json
from fireworld.validation import validate_event_groups, validate_qa_semantics, validate_schema

TASKS = {"L1-1", "L1-2", "L1-3", "L2-1", "L2-2", "L2-3", "L3-1", "L3-2", "L3-3"}


def read(root: Path, ref: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((root / ref).read_text()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    qa = json.loads((root / "qa" / "protocol_rebuild_v3" / "qa.json").read_text())
    eligible = [item for item in qa if item["quality"]["status"] == "eligible"]
    # User-authorized engineering acceptance defers, but never fabricates, the
    # independent mechanism review. These records remain explicitly ambiguous
    # in their QA quality field and excluded from any final PDF-compliant claim.
    provisional = [
        item for item in qa if item["quality"]["status"] == "eligible" or item["task_id"] == "L2-3"
    ]
    errors = [
        error
        for item in qa
        for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)
    ]
    errors += validate_event_groups(qa)
    refs: list[str] = []
    temporal_errors: list[str] = []
    option_errors: list[str] = []
    transform_errors: list[str] = []
    for item in qa:
        obs = item["observation"]
        if obs["structured"]:
            ref = obs["structured"]["ref"]
            refs.append(ref)
            path = root / ref
            if not path.is_file():
                temporal_errors.append(f"missing:{item['qa_id']}:{ref}")
                continue
            content = read(root, ref)
            rows = content.get("rows", [])
            end = obs["time_window_s"][1]
            times = [
                row.get("Time")
                for row in rows
                if isinstance(row, dict) and isinstance(row.get("Time"), (int, float))
            ]
            numeric_times = [float(time) for time in times if isinstance(time, (int, float))]
            if numeric_times and max(numeric_times) > end + 1e-6:
                temporal_errors.append(f"future_observation:{item['qa_id']}")
            if item["task_id"] == "L1-3":
                expected = item["answer"]["fields"]["violation_type"] or "identity"
                if content.get("transform") != expected:
                    transform_errors.append(f"transform_mismatch:{item['qa_id']}")
        for option in item["options"] or []:
            ref = option["content_ref"]
            if ref:
                refs.append(ref)
                if not (root / ref).is_file():
                    option_errors.append(f"missing_option:{item['qa_id']}:{ref}")
        if item["task_id"] == "L1-2":
            options = item["options"] or []
            if len(options) != 4 or {option["id"] for option in options} != set("ABCD"):
                option_errors.append(f"not_four_way:{item['qa_id']}")
                continue
            target = item["observation"]["time_window_s"][1]
            delta_text = item["observation"]["context"] or ""
            if "+" not in delta_text:
                option_errors.append(f"missing_delta:{item['qa_id']}")
            target_time = None
            try:
                target_time = target + float(delta_text.split("+")[1].split()[0])
            except (IndexError, ValueError):
                option_errors.append(f"bad_delta:{item['qa_id']}")
            actuals = []
            for option in options:
                candidate = read(root, option["content_ref"])
                actuals.append(candidate.get("time_s"))
                if (
                    option["id"] == item["answer"]["choice"]
                    and target_time is not None
                    and candidate.get("time_s") != target_time
                ):
                    option_errors.append(f"wrong_positive_time:{item['qa_id']}")
            if len(set(actuals)) != 4:
                option_errors.append(f"non_distinct_options:{item['qa_id']}")
    groups: dict[str, set[str]] = defaultdict(set)
    for item in qa:
        groups[item["event_group"]].add(item["split"])
    l1 = Counter(
        item["answer"]["fields"]["class"] for item in eligible if item["task_id"] == "L1-1"
    )
    l13 = Counter(
        item["answer"]["fields"]["consistency"] for item in eligible if item["task_id"] == "L1-3"
    )
    answer_positions = Counter(
        item["answer"]["choice"] for item in eligible if item["task_id"] == "L1-2"
    )
    task_counts = Counter(item["task_id"] for item in eligible)
    provisional_task_counts = Counter(item["task_id"] for item in provisional)
    report = {
        "schema_version": "3.0.0",
        "release_status": "blocked_by_protocol_audit",
        "formal_release_status": "blocked_pending_expert_mechanism_review",
        "engineering_acceptance_policy": "expert_review_deferred_by_user",
        "events": len({item["event_id"] for item in eligible}),
        "qa_all": len(qa),
        "qa_eligible": len(eligible),
        "qa_provisional": len(provisional),
        "task_counts_eligible": dict(sorted(task_counts.items())),
        "task_counts_provisional": dict(sorted(provisional_task_counts.items())),
        "l1_1_class_counts": dict(sorted(l1.items())),
        "l1_3_consistency_counts": dict(sorted(l13.items())),
        "l1_2_answer_positions": dict(sorted(answer_positions.items())),
        "checks": {
            "schema_and_semantic": not errors,
            "all_180_events_have_eligible_qa": len({item["event_id"] for item in eligible}) == 180,
            "eligible_qa_4000_6000": 4000 <= len(eligible) <= 6000,
            "all_nine_tasks_present": set(task_counts) == TASKS,
            "all_nine_tasks_present_with_deferred_mechanism_review": set(provisional_task_counts)
            == TASKS,
            "event_group_leakage_zero": not any(len(splits) > 1 for splits in groups.values()),
            "all_referenced_payloads_resolve": not [
                ref for ref in refs if not (root / ref).is_file()
            ],
            "no_future_rows_in_observation": not temporal_errors,
            "l1_1_four_class_balanced": len(set(l1.values())) == 1
            and set(l1) == {"fire", "no_fire", "ventilation_disturbance", "sensor_fault"},
            "l1_2_real_four_way_same_event_candidates": not option_errors,
            "l1_2_answer_position_spread_le_2": max(answer_positions.values())
            - min(answer_positions.values())
            <= 2,
            "l1_3_exact_50_50_real_transform": l13.get("consistent") == l13.get("inconsistent")
            and not transform_errors,
            "l3_1_has_10_30_60": {"10", "30", "60"}.issubset(
                {
                    (item["observation"]["context"] or "").split()[3]
                    for item in eligible
                    if item["task_id"] == "L3-1"
                }
            ),
            "mechanism_independent_review_complete": False,
        },
        "schema_errors": errors[:50],
        "temporal_errors": temporal_errors[:50],
        "option_errors": option_errors[:50],
        "transform_errors": transform_errors[:50],
        "pending": {
            "mechanism_review_items": sum(
                item["task_id"] == "L2-3" and item["quality"]["status"] != "eligible" for item in qa
            ),
            "reason": "TASK_PROTOCOL requires at least 10% independent fire-engineering review; no such review evidence exists.",
        },
    }
    checks = cast(dict[str, Any], report["checks"])
    auto_checks = {
        key: value
        for key, value in checks.items()
        if key not in {"mechanism_independent_review_complete", "all_nine_tasks_present"}
    }
    report["release_status"] = (
        "provisionally_accepted_expert_review_deferred"
        if all(bool(value) for value in auto_checks.values())
        else "blocked_by_protocol_audit"
    )
    write_json(root / "reports" / "protocol_rebuild_v3_audit.json", report)
    print(json.dumps(report, sort_keys=True))
    return 0 if str(report["release_status"]).startswith("provisionally_accepted") else 1


if __name__ == "__main__":
    raise SystemExit(main())
