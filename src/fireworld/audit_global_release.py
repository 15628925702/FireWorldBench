"""Fail-closed global release audit for accepted production evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from fireworld.mini_pilot import write_json
from fireworld.validation import validate_event_groups, validate_qa_semantics, validate_schema

REQUIRED_TASKS = {
    f"L{layer}-{task}"
    for layer, task in ((1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3))
}
REQUIRED_MECHANISMS = {
    "buoyant_plume",
    "ceiling_jet",
    "smoke_layer",
    "longitudinal_ventilation",
    "backlayering",
    "extraction_dominated",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    matrix = json.loads((root / "splits" / "production_matrix.v2.1.json").read_text())
    questions: list[dict[str, Any]] = json.loads(
        (root / "qa" / "global_release" / "qa.json").read_text()
    )
    event_paths = sorted((root / "fire_events").glob("production_batch_*/fire_events.json"))
    events = [event for path in event_paths for event in json.loads(path.read_text())]
    existing_rows = [row for row in matrix["rows"] if row["status"] == "qualified_existing"]
    existing_events = [json.loads((root / row["source_ref"]).read_text()) for row in existing_rows]
    task_counts = Counter(item["task_id"] for item in questions)
    mechanism_counts = Counter(
        item["answer"]["fields"]["mechanism"] for item in questions if item["task_id"] == "L2-3"
    )
    mechanism_questions = [item for item in questions if item["task_id"] == "L2-3"]
    calibration = json.loads((root / "reports" / "mechanism_rule_calibration.v1.json").read_text())
    replacements = json.loads((root / "splits" / "mechanism_replacements.v1.json").read_text())[
        "replacements"
    ]
    replacement_by_event = {item["target_event_id"]: item for item in replacements}
    mechanism_rule_valid = (
        calibration.get("status") == "calibrated_not_yet_integrated"
        and len(replacements) == len(REQUIRED_MECHANISMS)
        and all(item.get("status") == "integrated" for item in replacements)
        and {item["event_id"] for item in mechanism_questions} == set(replacement_by_event)
        and all(
            item["answer"]["fields"]["mechanism"]
            == replacement_by_event[item["event_id"]]["mechanism"]
            and item["observation"]["structured"]["ref"].startswith(
                "derived/mechanism_replacements/S/"
            )
            for item in mechanism_questions
        )
    )
    track_counts = Counter(item["track"] for item in questions)
    answer_positions = Counter(
        item["answer"]["choice"] for item in questions if item["task_id"] == "L1-2"
    )
    refs: list[str] = []
    for item in questions:
        observation = item["observation"]
        if observation["structured"]:
            refs.append(observation["structured"]["ref"])
        refs.extend(observation["images"] or [])
        if observation["video"]:
            refs.append(observation["video"])
        refs.extend(
            option["content_ref"] for option in item["options"] or [] if option["content_ref"]
        )
    errors = [
        error
        for item in questions
        for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)
    ]
    errors.extend(validate_event_groups(questions))
    groups = defaultdict(set)
    for item in questions:
        groups[item["event_group"]].add(item["split"])
    checks: dict[str, Any] = {
        "qa_schema_semantic": not errors,
        "qa_count_4000_6000": 4000 <= len(questions) <= 6000,
        "all_nine_tasks": set(task_counts) == REQUIRED_TASKS,
        "event_group_leakage_zero": not any(len(value) > 1 for value in groups.values()),
        "all_referenced_paths_resolve": not [ref for ref in refs if not (root / ref).is_file()],
        "l1_2_answer_position_spread_le_2": max(answer_positions.values())
        - min(answer_positions.values())
        <= 2,
        "l1_3_has_both_classes": {
            item["answer"]["fields"]["consistency"]
            for item in questions
            if item["task_id"] == "L1-3"
        }
        == {"consistent", "inconsistent"},
        "all_six_mechanisms": set(mechanism_counts) == REQUIRED_MECHANISMS,
        "mechanism_labels_have_frozen_engineering_rule": mechanism_rule_valid,
        "matrix_all_180_integrated": len(events) + len(existing_events) == matrix["target_events"],
        # Set by the full protocol audit, not by schema validation alone.
        "task_observations_are_temporally_materialized": False,
        "release_package_is_self_contained": False,
        "all_matrix_events_have_qa": len({item["event_id"] for item in questions})
        == matrix["target_events"],
    }
    report = {
        "schema_version": "2.1.0",
        "release_status": "accepted" if all(checks.values()) else "blocked_by_audit",
        "matrix_target_events": matrix["target_events"],
        "production_events_integrated": len(events),
        "preexisting_matrix_rows_integrated": len(existing_events),
        "preexisting_matrix_rows_not_yet_integrated": matrix["target_events"]
        - len(events)
        - len(existing_events),
        "qa": len(questions),
        "task_counts": dict(sorted(task_counts.items())),
        "track_counts": dict(sorted(track_counts.items())),
        "mechanism_counts": dict(sorted(mechanism_counts.items())),
        "l1_2_answer_positions": dict(sorted(answer_positions.items())),
        "checks": checks,
        "validation_error_count": len(errors),
        "unresolved_ref_count": sum(not (root / ref).is_file() for ref in refs),
    }
    write_json(root / "reports" / "global_release_audit.v2.1.json", report)
    print(json.dumps(report))
    return 0 if report["release_status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
