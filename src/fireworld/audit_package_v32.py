"""Audit v3.2 using only files inside the release package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, cast

from fireworld.mini_pilot import write_json

TEST_SPLITS = {
    "test_iid",
    "test_ood_geometry",
    "test_ood_condition",
    "test_ood_view_sensor",
}
TASKS = {"L1-1", "L1-2", "L1-3", "L2-1", "L2-2", "L2-3", "L3-1", "L3-2", "L3-3"}
VERSION = "fds-core-v3.2.0"


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refs(row: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    observation = row["observation"]
    if observation["structured"]:
        result.add(observation["structured"]["ref"])
    result.update(observation["images"] or [])
    if observation["video"]:
        result.add(observation["video"])
    result.update(
        option["content_ref"]
        for option in row["options"] or []
        if option["content_ref"]
    )
    return result


def event_class(event: dict[str, Any]) -> str | None:
    return next(
        (
            str(label["value"])
            for label in event["ground_truth"]["labels"]
            if label["name"] == "event_class"
        ),
        None,
    )


def update_manifest(release: Path, status: str) -> None:
    manifest_path = release / "release_manifest.json"
    manifest: dict[str, Any] = load(manifest_path)
    manifest["status"] = status
    manifest["files"] = {
        path.relative_to(release).as_posix(): sha256(path)
        for path in release.rglob("*")
        if path.is_file() and path != manifest_path
    }
    write_json(manifest_path, manifest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    release = root / "release/fireworldbench_fds_core_v3_2"
    public, private = release / "public", release / "private"
    manifest: dict[str, Any] = load(release / "release_manifest.json")
    train_dev: list[dict[str, Any]] = load(public / "qa_train_dev.json")
    test_questions: list[dict[str, Any]] = load(public / "qa_test_questions.json")
    test_gold: list[dict[str, Any]] = load(private / "qa_test_gold.json")
    gold_by_id = {row["qa_id"]: row for row in test_gold}
    full_rows = train_dev + test_gold
    events: list[dict[str, Any]] = [
        load(path)
        for path in sorted((public / "fire_events/fds_core_v3_2").glob("FWE-*.json"))
    ]
    matrix: dict[str, Any] = load(public / "configs/production_matrix.v3.2.json")
    missing_qa_refs = sorted(
        ref for row in full_rows for ref in refs(row) if not (public / ref).is_file()
    )
    missing_event_refs: list[str] = []
    for event in events:
        observation = event["observations"]
        event_refs = set()
        if observation["structured"]:
            event_refs.add(observation["structured"]["ref"])
        event_refs.update(item["ref"] for item in observation["images"] or [])
        if observation["video"]:
            event_refs.add(observation["video"]["ref"])
        event_refs.add(event["license"]["evidence_ref"])
        missing_event_refs.extend(ref for ref in event_refs if not (public / ref).is_file())

    public_answers = sum(
        bool(row["answer"]["choice"] or row["answer"]["fields"])
        for row in test_questions
    )
    question_ids = {row["qa_id"] for row in test_questions}
    gold_ids = set(gold_by_id)
    validation_payload = public / "reports/package_validation_payload.json"
    write_json(validation_payload, {"events": events, "qa": full_rows})
    validation_code = """
import json,sys
sys.path.insert(0, sys.argv[1])
from fireworld.validation import validate_event_groups,validate_event_semantics,validate_qa_semantics,validate_schema
d=json.load(open(sys.argv[2]))
errors=[]
for x in d['events']: errors += validate_schema(x,'fire_event.schema.json') + validate_event_semantics(x)
for x in d['qa']: errors += validate_schema(x,'qa.schema.json') + validate_qa_semantics(x)
errors += validate_event_groups(d['qa'])
print(json.dumps(errors))
raise SystemExit(bool(errors))
"""
    environment = os.environ.copy()
    environment["FIREWORLD_SCHEMA_ROOT"] = str(public / "schemas")
    validation = subprocess.run(
        [
            "/root/miniconda3/envs/fireworldbench-v1/bin/python",
            "-c",
            validation_code,
            str(public / "scorer"),
            str(validation_payload),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
        cwd=public,
    )
    validation_payload.unlink()

    scoring_code = """
import json,sys
sys.path.insert(0,sys.argv[1])
from fireworld.scoring import aggregate_scores
gold=json.load(open(sys.argv[2])); predictions={x['qa_id']:x for x in json.load(open(sys.argv[3]))}
print(json.dumps(aggregate_scores(gold,predictions),sort_keys=True))
"""

    def replay(prediction_path: Path) -> dict[str, Any]:
        result = subprocess.run(
            [
                "/root/miniconda3/envs/fireworldbench-v1/bin/python",
                "-c",
                scoring_code,
                str(public / "scorer"),
                str(private / "qa_test_gold.json"),
                str(prediction_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=release,
        )
        if result.returncode:
            return {"error": result.stderr, "returncode": result.returncode}
        return cast(dict[str, Any], json.loads(result.stdout))

    majority_replay = replay(public / "baselines/fds_core_v3_2_majority_predictions.json")
    rule_replay = replay(public / "baselines/fds_core_v3_2_physical_rule_predictions.json")
    baseline_report: dict[str, Any] = load(public / "reports/fds_core_v3_2_baselines.json")
    data_audit: dict[str, Any] = load(public / "reports/fds_core_v3_2_data_audit.json")
    stability_audit: dict[str, Any] = load(
        public / "reports/fds_core_v3_2_stability_shortcut_audit.json"
    )
    engineering_audit: dict[str, Any] = load(
        public / "reports/fds_core_v3_2_engineering_audit.json"
    )
    report_snapshots = {
        report_path.name: load(report_path).get("snapshot_id")
        for report_path in (public / "reports").glob("*.json")
    }
    class_counts = Counter(event_class(event) for event in events)
    split_counts = Counter(row["split"] for row in matrix["rows"])
    event_groups: dict[str, set[str]] = defaultdict(set)
    for row in full_rows:
        event_groups[row["event_group"]].add(row["split"])
    file_hash_errors = [
        name
        for name, expected in manifest["files"].items()
        if not (release / name).is_file() or sha256(release / name) != expected
    ]
    checks = {
        "package_files_match_manifest": not file_hash_errors,
        "package_local_schema_semantic_validation": validation.returncode == 0,
        "exactly_180_events": len(events) == 180,
        "qa_4000_6000": 4000 <= len(full_rows) <= 6000,
        "event_class_matrix_126_18_18_18": class_counts
        == Counter(
            {
                "fire": 126,
                "no_fire": 18,
                "ventilation_disturbance": 18,
                "non_fire_disturbance": 18,
            }
        ),
        "event_split_matrix_96_20_20_16_14_14": split_counts
        == Counter(
            {
                "train": 96,
                "dev": 20,
                "test_iid": 20,
                "test_ood_geometry": 16,
                "test_ood_condition": 14,
                "test_ood_view_sensor": 14,
            }
        ),
        "all_nine_tasks_and_three_tracks": {row["task_id"] for row in full_rows}
        == TASKS
        and {row["track"] for row in full_rows} == {"S", "I", "V"},
        "all_package_references_resolve": not missing_qa_refs and not missing_event_refs,
        "test_answers_hidden": public_answers == 0,
        "private_gold_matches_public_questions": question_ids == gold_ids,
        "event_group_leakage_zero": not any(len(splits) > 1 for splits in event_groups.values()),
        "data_audit_passed": data_audit["status"]
        == "passed_data_gates_pending_release_experiments",
        "stability_shortcut_audit_passed": stability_audit["status"]
        == "passed_pending_package_audit",
        "engineering_gates_passed": engineering_audit["status"] == "passed",
        "majority_scorer_replay": majority_replay == baseline_report["train_majority"],
        "rule_scorer_replay": rule_replay == baseline_report["physical_rule"],
        "oracle_self_check_100_excluded": baseline_report[
            "oracle_self_check_excluded_from_results"
        ]["overall"]
        == 100.0,
        "no_llm_judge": baseline_report["llm_judge_used"] is False,
        "all_reports_same_snapshot": set(report_snapshots.values())
        == {manifest["snapshot_id"]},
        "license_internal_restricted_explicit": all(
            event["license"]["redistribution"] == "restricted" for event in events
        ),
        "fd_gen_provenance_not_fabricated": load(
            public / "reports/environment_provenance.json"
        )["fd_gen"]["status"]
        == "not_used",
        "expert_review_only_deferred_gate": sum(
            row["quality"]["status"] == "eligible_expert_review_deferred"
            for row in full_rows
        )
        == 6
        and all(
            row["task_id"] == "L2-3"
            for row in full_rows
            if row["quality"]["status"] == "eligible_expert_review_deferred"
        ),
    }
    report = {
        "schema_version": VERSION,
        "snapshot_id": manifest["snapshot_id"],
        "release_status": (
            "provisionally_accepted_expert_review_deferred"
            if all(checks.values())
            else "blocked_by_package_audit"
        ),
        "strict_qualified_events": 180 if all(checks.values()) else 0,
        "events": len(events),
        "qa": len(full_rows),
        "task_counts": dict(sorted(Counter(row["task_id"] for row in full_rows).items())),
        "track_counts": dict(sorted(Counter(row["track"] for row in full_rows).items())),
        "class_counts": dict(sorted(class_counts.items(), key=lambda item: str(item[0]))),
        "split_counts": dict(sorted(split_counts.items())),
        "checks": checks,
        "errors": {
            "manifest_hash": file_hash_errors,
            "schema_semantic": validation.stdout[-4000:] + validation.stderr[-4000:],
            "missing_qa_refs": missing_qa_refs,
            "missing_event_refs": missing_event_refs,
        },
        "baseline_replay": {"majority": majority_replay, "physical_rule": rule_replay},
    }
    package_report = public / "reports/fds_core_v3_2_package_audit.json"
    write_json(package_report, report)
    write_json(root / "reports/fds_core_v3_2_package_audit.json", report)
    update_manifest(release, report["release_status"])
    print(json.dumps({"release_status": report["release_status"], "checks": checks}, indent=2))
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
