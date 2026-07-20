"""Create a reproducible release package with test answers kept private."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, cast

from fireworld.mini_pilot import write_json

TEST_SPLITS = {"test_iid", "test_ood_geometry", "test_ood_condition", "test_ood_view_sensor"}


def public_row(row: dict[str, Any]) -> dict[str, Any]:
    copy = json.loads(json.dumps(row))
    copy["answer"] = {"choice": None, "fields": {}}
    return cast(dict[str, Any], copy)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    audit = json.loads((root / "reports" / "global_release_audit.v2.1.json").read_text())
    if audit["release_status"] != "accepted":
        raise ValueError("cannot package a release blocked by global audit")
    qa = json.loads((root / "qa" / "global_release" / "qa.json").read_text())
    release = root / "release" / "fireworldbench_v2_1_final"
    if release.exists():
        raise ValueError(f"release directory already exists: {release}")
    public = release / "public"
    private = release / "private"
    public.mkdir(parents=True)
    private.mkdir(parents=True)
    train_dev = [row for row in qa if row["split"] not in TEST_SPLITS]
    tests = [row for row in qa if row["split"] in TEST_SPLITS]
    write_json(public / "qa_train_dev.json", train_dev)
    write_json(public / "qa_test_questions.json", [public_row(row) for row in tests])
    write_json(private / "qa_test_gold.json", tests)
    shutil.copy2(
        root / "splits" / "production_matrix.v2.1.json", public / "production_matrix.v2.1.json"
    )
    shutil.copy2(
        root / "reports" / "global_release_audit.v2.1.json",
        public / "global_release_audit.v2.1.json",
    )
    manifest: dict[str, Any] = {
        "schema_version": "2.1.0",
        "status": "accepted",
        "events": 180,
        "qa_total": len(qa),
        "qa_train_dev": len(train_dev),
        "qa_test_hidden_answer": len(tests),
        "task_counts": dict(sorted(Counter(row["task_id"] for row in qa).items())),
        "tracks": dict(sorted(Counter(row["track"] for row in qa).items())),
        "scoring": "deterministic fireworld.score; no LLM judge",
        "baselines": {
            "chance": {"L1-2": 0.25, "L1-1": 0.25, "L3-3": 1 / 3},
            "majority_and_rule": "reported separately; oracle excluded",
        },
    }
    write_json(release / "release_manifest.json", manifest)
    print(json.dumps(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
