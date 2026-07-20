"""Verify the self-contained public package and private answer boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fireworld.mini_pilot import write_json


def refs(row: dict[str, Any]) -> set[str]:
    output: set[str] = set()
    obs = row["observation"]
    if obs["structured"]:
        output.add(obs["structured"]["ref"])
    output.update(obs["images"] or [])
    if obs["video"]:
        output.add(obs["video"])
    output.update(option["content_ref"] for option in row["options"] or [] if option["content_ref"])
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    release = root / "release" / "fireworldbench_fds_core_v3_1"
    public, private = release / "public", release / "private"
    train_dev: list[dict[str, Any]] = json.loads((public / "qa_train_dev.json").read_text())
    test_questions: list[dict[str, Any]] = json.loads(
        (public / "qa_test_questions.json").read_text()
    )
    test_gold: list[dict[str, Any]] = json.loads((private / "qa_test_gold.json").read_text())
    public_rows = train_dev + test_questions
    public_refs = {ref for row in public_rows for ref in refs(row)}
    missing = sorted(ref for ref in public_refs if not (public / ref).is_file())
    public_answers = sum(
        bool(row["answer"]["choice"] or row["answer"]["fields"]) for row in test_questions
    )
    gold_ids = {row["qa_id"] for row in test_gold}
    question_ids = {row["qa_id"] for row in test_questions}
    report = {
        "schema_version": "fds-core-v3.1.0",
        "release": release.name,
        "checks": {
            "public_references_resolve": not missing,
            "test_answers_hidden": public_answers == 0,
            "test_gold_matches_questions": gold_ids == question_ids,
            "events_present": len(
                list((public / "fire_events" / "fds_core_v3_1").glob("FWE-*.json"))
            )
            == 180,
            "scorer_present": (public / "src" / "fireworld" / "score.py").is_file(),
            "schemas_present": all(
                (public / "schemas" / name).is_file()
                for name in (
                    "fire_event.schema.json",
                    "qa.schema.json",
                    "prediction.v2.schema.json",
                )
            ),
        },
        "public_ref_count": len(public_refs),
        "missing_refs": missing,
        "public_test_answer_count": public_answers,
    }
    report["release_status"] = (
        "provisionally_accepted_expert_review_deferred"
        if all(report["checks"].values())
        else "blocked_by_package_audit"
    )
    write_json(root / "reports" / "fds_core_v3_1_package_audit.json", report)
    print(json.dumps(report, indent=2))
    return 0 if report["release_status"] != "blocked_by_package_audit" else 2


if __name__ == "__main__":
    raise SystemExit(main())
