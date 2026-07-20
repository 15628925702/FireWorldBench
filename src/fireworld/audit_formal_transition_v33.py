"""Verify that v3.3 changes only the completed expert-review fields."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, cast

from fireworld.mini_pilot import write_json
from fireworld.validation import (
    validate_event_groups,
    validate_qa_semantics,
    validate_schema,
)

VERSION = "fds-core-v3.3.0"


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def normalize_review_fields(item: dict[str, Any]) -> dict[str, Any]:
    result = cast(dict[str, Any], json.loads(json.dumps(item)))
    if result["task_id"] == "L2-3":
        result["quality"]["status"] = "eligible_expert_review_deferred"
        result["quality"]["ambiguity_reason"] = (
            "independent_fire_engineering_review_deferred_by_user"
        )
        result["observation"]["context"] = (
            "Engineering-rule evidence; independent review pending."
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    prior: list[dict[str, Any]] = load(root / "qa/fds_core_v3_2/qa.json")
    formal: list[dict[str, Any]] = load(root / "qa/fds_core_v3_3/qa.json")
    prior_by_id = {item["qa_id"]: item for item in prior}
    formal_by_id = {item["qa_id"]: item for item in formal}
    changed = [
        qa_id
        for qa_id in sorted(prior_by_id)
        if prior_by_id[qa_id] != formal_by_id.get(qa_id)
    ]
    nonreview_changes = [
        qa_id
        for qa_id in changed
        if normalize_review_fields(formal_by_id[qa_id]) != prior_by_id[qa_id]
    ]
    errors = [
        error
        for item in formal
        for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)
    ]
    errors.extend(validate_event_groups(formal))
    group_splits: dict[str, set[str]] = defaultdict(set)
    for item in formal:
        group_splits[item["event_group"]].add(item["split"])
    base_reports = {
        "physical": load(root / "reports/fds_core_v3_2_trajectory_repair_physical_audit.json"),
        "unique": load(root / "reports/fds_core_v3_2_global_trajectory_uniqueness.json"),
        "visual": load(root / "reports/fds_core_v3_2_trajectory_repair_visual_audit.json"),
        "data": load(root / "reports/fds_core_v3_2_data_audit.json"),
        "stability": load(root / "reports/fds_core_v3_2_stability_shortcut_audit.json"),
        "engineering": load(root / "reports/fds_core_v3_2_engineering_audit.json"),
    }
    expert = load(root / "reports/private/fds_core_v3_3_expert_review_record.json")
    checks = {
        "same_qa_ids": set(prior_by_id) == set(formal_by_id),
        "exactly_six_l2_3_review_changes": len(changed) == 6
        and all(formal_by_id[qa_id]["task_id"] == "L2-3" for qa_id in changed),
        "no_nonreview_data_changes": not nonreview_changes,
        "all_4039_quality_eligible": len(formal) == 4039
        and all(item["quality"]["status"] == "eligible" for item in formal),
        "schema_semantic_validation": not errors,
        "task_track_counts_unchanged": Counter(item["task_id"] for item in prior)
        == Counter(item["task_id"] for item in formal)
        and Counter(item["track"] for item in prior)
        == Counter(item["track"] for item in formal),
        "event_group_leakage_zero": not any(
            len(splits) > 1 for splits in group_splits.values()
        ),
        "expert_review_record_complete": expert["status"] == "completed"
        and expert["reviewed_qa_count"] == 6
        and {item["qa_id"] for item in expert["reviewed_items"]} == set(changed),
        "physical_reaudit_passed": base_reports["physical"]["status"] == "passed",
        "trajectory_uniqueness_reaudit_passed": base_reports["unique"]["status"]
        == "passed",
        "visual_reaudit_passed": base_reports["visual"]["status"] == "passed",
        "data_reaudit_passed": base_reports["data"]["status"]
        == "passed_data_gates_pending_release_experiments",
        "stability_shortcut_reaudit_passed": base_reports["stability"]["status"]
        == "passed_pending_package_audit",
        "engineering_reaudit_passed": base_reports["engineering"]["status"] == "passed",
    }
    report = {
        "schema_version": VERSION,
        "status": "passed_pending_formal_package" if all(checks.values()) else "blocked",
        "events": 180,
        "qa": len(formal),
        "changed_qa_ids": changed,
        "checks": checks,
        "errors": {"schema_semantic": errors, "nonreview_changes": nonreview_changes},
    }
    write_json(root / "reports/fds_core_v3_3_formal_transition_audit.json", report)
    print(json.dumps({"status": report["status"], "checks": checks}, indent=2))
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
