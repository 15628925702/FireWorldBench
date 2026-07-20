"""Build a self-contained internal v3.1 release with hidden test answers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, cast

from fireworld.mini_pilot import write_json

TEST_SPLITS = {"test_iid", "test_ood_geometry", "test_ood_condition", "test_ood_view_sensor"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def link(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    os.link(source, destination)


def public_row(row: dict[str, Any]) -> dict[str, Any]:
    copy = json.loads(json.dumps(row))
    copy["answer"] = {"choice": None, "fields": {}}
    return cast(dict[str, Any], copy)


def refs_for(row: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    observation = row["observation"]
    if observation["structured"]:
        refs.add(observation["structured"]["ref"])
    refs.update(observation["images"] or [])
    if observation["video"]:
        refs.add(observation["video"])
    refs.update(option["content_ref"] for option in row["options"] or [] if option["content_ref"])
    return refs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    project = Path(__file__).resolve().parents[2]
    audit = json.loads((root / "reports" / "fds_core_v3_1_final_audit.json").read_text())
    if audit["release_status"] != "provisionally_accepted_expert_review_deferred":
        raise ValueError("final audit has not accepted the v3.1 candidate")
    release = root / "release" / "fireworldbench_fds_core_v3_1"
    if release.exists():
        raise ValueError(f"refusing to overwrite release: {release}")
    public, private = release / "public", release / "private"
    public.mkdir(parents=True)
    private.mkdir(parents=True)
    qa: list[dict[str, Any]] = json.loads((root / "qa" / "fds_core_v3_1" / "qa.json").read_text())
    train_dev = [row for row in qa if row["split"] not in TEST_SPLITS]
    tests = [row for row in qa if row["split"] in TEST_SPLITS]
    write_json(public / "qa_train_dev.json", train_dev)
    write_json(public / "qa_test_questions.json", [public_row(row) for row in tests])
    write_json(private / "qa_test_gold.json", tests)
    for event in sorted((root / "fire_events" / "fds_core_v3_1").glob("FWE-*.json")):
        link(event, public / "fire_events" / "fds_core_v3_1" / event.name)
    refs = {"governance/licenses/fds_internal_release_v3_1.md"}
    for row in qa:
        refs.update(refs_for(row))
    events = [
        json.loads(path.read_text())
        for path in (root / "fire_events" / "fds_core_v3_1").glob("FWE-*.json")
    ]
    for event in events:
        obs = event["observations"]
        if obs["structured"]:
            refs.add(obs["structured"]["ref"])
        refs.update(image["ref"] for image in obs["images"] or [])
        if obs["video"]:
            refs.add(obs["video"]["ref"])
        refs.add(event["license"]["evidence_ref"] or "")
    refs.discard("")
    missing = sorted(ref for ref in refs if not (root / ref).is_file())
    if missing:
        raise ValueError("unresolved release refs: " + "; ".join(missing[:20]))
    for ref in sorted(refs):
        link(root / ref, public / ref)
    for name in ("fire_event.schema.json", "qa.schema.json", "prediction.v2.schema.json"):
        link(project / "schemas" / name, public / "schemas" / name)
    for name in (
        "__init__.py",
        "contracts.py",
        "scoring.py",
        "score.py",
        "validation.py",
        "cli_utils.py",
    ):
        link(project / "src" / "fireworld" / name, public / "src" / "fireworld" / name)
    for source in (
        root / "splits" / "production_matrix.v2.1.json",
        root / "reports" / "fds_core_v3_1_event_snapshot.json",
        root / "reports" / "fds_core_v3_1_qa_snapshot.json",
        root / "reports" / "fds_core_v3_1_final_audit.json",
        root / "reports" / "fds_core_v3_1_stability_shortcut_audit.json",
        root / "reports" / "fds_core_v3_1_baselines.json",
    ):
        link(source, public / "reports" / source.name)
    manifest = {
        "schema_version": "fds-core-v3.1.0",
        "status": "provisionally_accepted_expert_review_deferred",
        "expert_review_deferred_task": "L2-3",
        "events": len(events),
        "qa_total": len(qa),
        "qa_train_dev": len(train_dev),
        "qa_test_hidden_answer": len(tests),
        "task_counts": dict(sorted(Counter(row["task_id"] for row in qa).items())),
        "track_counts": dict(sorted(Counter(row["track"] for row in qa).items())),
        "test_answers": "private/qa_test_gold.json only",
        "scoring": "deterministic fireworld.score; no LLM judge",
        "license_policy": "internal_research_only; redistribution restricted",
        "reference_file_count": len(refs),
        "snapshot_sha256": sha256(root / "reports" / "fds_core_v3_1_qa_snapshot.json"),
    }
    write_json(release / "release_manifest.json", manifest)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
