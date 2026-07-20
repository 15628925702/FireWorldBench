"""Build the immutable self-contained FDS Core v3.2 package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, cast

from fireworld.mini_pilot import write_json

TEST_SPLITS = {
    "test_iid",
    "test_ood_geometry",
    "test_ood_condition",
    "test_ood_view_sensor",
}
VERSION = "fds-core-v3.2.0"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def link(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.link(source, destination)


def public_question(row: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(row))
    result["answer"] = {"choice": None, "fields": {}}
    result["provenance"].pop("event_manifest_sha256", None)
    return cast(dict[str, Any], result)


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


def canonical_hash(paths: list[Path], base: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(base).as_posix().encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256(path)))
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    project = Path(__file__).resolve().parents[2]
    required = {
        "data": (root / "reports/fds_core_v3_2_data_audit.json", "status", "passed_data_gates_pending_release_experiments"),
        "stability": (root / "reports/fds_core_v3_2_stability_shortcut_audit.json", "status", "passed_pending_package_audit"),
        "engineering": (root / "reports/fds_core_v3_2_engineering_audit.json", "status", "passed"),
    }
    for name, (path, key, expected) in required.items():
        if json.loads(path.read_text())[key] != expected:
            raise ValueError(f"{name} gate has not passed")
    baselines: dict[str, Any] = json.loads(
        (root / "reports/fds_core_v3_2_baselines.json").read_text()
    )
    if baselines["oracle_self_check_excluded_from_results"]["overall"] != 100.0:
        raise ValueError("oracle scorer self-check did not pass")

    release = root / "release/fireworldbench_fds_core_v3_2"
    if release.exists():
        raise ValueError(f"refusing to overwrite immutable release: {release}")
    public, private = release / "public", release / "private"
    public.mkdir(parents=True)
    private.mkdir(parents=True)
    qa: list[dict[str, Any]] = json.loads((root / "qa/fds_core_v3_2/qa.json").read_text())
    train_dev = [row for row in qa if row["split"] not in TEST_SPLITS]
    tests = [row for row in qa if row["split"] in TEST_SPLITS]
    write_json(public / "qa_train_dev.json", train_dev)
    write_json(public / "qa_test_questions.json", [public_question(row) for row in tests])
    write_json(private / "qa_test_gold.json", tests)
    write_json(
        private / "scoring_config.json",
        {
            "schema_version": VERSION,
            "primary": "deterministic_nine_task_macro",
            "test_splits": sorted(TEST_SPLITS),
            "llm_judge": False,
            "expert_deferred_policy": "score L2-3 with deterministic frozen label; independent review deferred",
        },
    )

    event_paths = sorted((root / "fire_events/fds_core_v3_2").glob("FWE-*.json"))
    events = [json.loads(path.read_text()) for path in event_paths]
    for path in event_paths:
        link(path, public / "fire_events/fds_core_v3_2" / path.name)
    release_refs = {ref for row in qa for ref in refs(row)}
    for event in events:
        observations = event["observations"]
        if observations["structured"]:
            release_refs.add(observations["structured"]["ref"])
        release_refs.update(item["ref"] for item in observations["images"] or [])
        if observations["video"]:
            release_refs.add(observations["video"]["ref"])
        release_refs.add(event["license"]["evidence_ref"])
    missing = sorted(ref for ref in release_refs if not (root / ref).is_file())
    if missing:
        raise ValueError(f"unresolved package references: {missing[:20]}")
    for ref in sorted(release_refs):
        link(root / ref, public / ref)

    for name in ("fire_event.schema.json", "qa.schema.json", "prediction.v2.schema.json"):
        link(project / "schemas" / name, public / "schemas" / name)
    for name in ("tasks.v2.json", "evaluation.v2.json"):
        link(project / "configs" / name, public / "configs" / name)
    link(root / "splits/production_matrix.v3.2.json", public / "configs/production_matrix.v3.2.json")
    for name in (
        "__init__.py",
        "contracts.py",
        "scoring.py",
        "score.py",
        "validation.py",
        "cli_utils.py",
    ):
        link(project / "src/fireworld" / name, public / "scorer/fireworld" / name)
    for name in (
        "fds_core_v3_2_data_audit.json",
        "fds_core_v3_2_stability_shortcut_audit.json",
        "fds_core_v3_2_baselines.json",
        "fds_core_v3_2_engineering_audit.json",
        "fds_core_v3_2_global_trajectory_uniqueness.json",
        "fds_core_v3_2_trajectory_repair_physical_audit.json",
        "fds_core_v3_2_trajectory_repair_visual_audit.json",
    ):
        destination = public / "reports" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / "reports" / name, destination)
    for name in (
        "fds_core_v3_2_majority_predictions.json",
        "fds_core_v3_2_physical_rule_predictions.json",
    ):
        destination = public / "baselines" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / "reports" / name, destination)
    (public / "configs").mkdir(parents=True, exist_ok=True)
    shutil.copy2(project / "docs/TASK_PROTOCOL.md", public / "configs/TASK_PROTOCOL.md")
    shutil.copy2(
        project / "docs/FINAL_REPAIR_AND_ACCEPTANCE_PLAN_V3.md",
        public / "configs/FINAL_REPAIR_AND_ACCEPTANCE_PLAN_V3.md",
    )
    environment = {
        "schema_version": VERSION,
        "design_pdf_sha256": "ba63ab8428d1f759629a89864af7f623589d023dd6d5a29e4940fc6d629a19a6",
        "fds": "6.11.1",
        "smokeview": "6.11.2",
        "python": "3.11.15",
        "fdsreader": "1.11.7",
        "fd_gen": {"status": "not_used", "installed_package": False},
        "license_scope": "internal_research_only_redistribution_restricted",
    }
    write_json(public / "reports/environment_provenance.json", environment)

    authoritative = [
        path
        for path in release.rglob("*")
        if path.is_file() and "reports" not in path.parts and path.name != "release_manifest.json"
    ]
    snapshot = canonical_hash(authoritative, release)
    for report_path in (public / "reports").glob("*.json"):
        report = json.loads(report_path.read_text())
        report["snapshot_id"] = snapshot
        write_json(report_path, report)
    files = {
        path.relative_to(release).as_posix(): sha256(path)
        for path in release.rglob("*")
        if path.is_file()
    }
    manifest = {
        "schema_version": VERSION,
        "status": "candidate_pending_package_audit",
        "snapshot_id": snapshot,
        "events": len(events),
        "qa_total": len(qa),
        "qa_train_dev": len(train_dev),
        "qa_test_hidden_answer": len(tests),
        "task_counts": dict(sorted(Counter(row["task_id"] for row in qa).items())),
        "track_counts": dict(sorted(Counter(row["track"] for row in qa).items())),
        "expert_review_status": "deferred_by_user_L2-3_only",
        "test_answers": "private/qa_test_gold.json only",
        "license_policy": "internal_research_only; redistribution restricted",
        "files": files,
    }
    write_json(release / "release_manifest.json", manifest)
    print(json.dumps({key: value for key, value in manifest.items() if key != "files"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
