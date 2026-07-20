"""Create the expert-reviewed QA snapshot from the accepted v3.2 release."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, cast

from fireworld.mini_pilot import write_json
from fireworld.validation import (
    validate_event_groups,
    validate_qa_semantics,
    validate_schema,
)

VERSION = "fds-core-v3.3.0"


def load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    predecessor = load(root / "reports/fds_core_v3_2_final_acceptance.json")
    if predecessor["release_status"] != "provisionally_accepted_expert_review_deferred":
        raise ValueError("v3.2 predecessor is not accepted")
    source_path = root / "qa/fds_core_v3_2/qa.json"
    destination = root / "qa/fds_core_v3_3/qa.json"
    if destination.exists():
        raise ValueError(f"refusing to overwrite formal QA snapshot: {destination}")
    source: list[dict[str, Any]] = json.loads(source_path.read_text())
    formal = json.loads(json.dumps(source))
    reviewed: list[dict[str, Any]] = []
    for item in formal:
        if item["quality"]["status"] != "eligible_expert_review_deferred":
            continue
        if item["task_id"] != "L2-3":
            raise ValueError(f"non-L2-3 deferred item: {item['qa_id']}")
        item["quality"]["status"] = "eligible"
        item["quality"]["ambiguity_reason"] = None
        item["observation"]["context"] = (
            "Engineering-rule evidence; independent expert review completed."
        )
        reviewed.append(
            {
                "qa_id": item["qa_id"],
                "event_id": item["event_id"],
                "split": item["split"],
                "mechanism": item["answer"]["fields"]["mechanism"],
            }
        )
    if len(reviewed) != 6:
        raise ValueError(f"expected six reviewed L2-3 items, found {len(reviewed)}")
    errors = [
        error
        for item in formal
        for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)
    ]
    errors.extend(validate_event_groups(formal))
    if errors:
        raise ValueError("formal QA validation failed: " + "; ".join(errors[:20]))
    if Counter(item["task_id"] for item in source) != Counter(
        item["task_id"] for item in formal
    ):
        raise ValueError("task counts changed during expert-review transition")
    write_json(destination, formal)
    public_record = {
        "schema_version": VERSION,
        "status": "completed",
        "scope": "all six L2-3 dominant transport mechanism labels",
        "reviewed_qa_count": 6,
        "outcome": "accepted_no_label_changes_reported",
        "attestation_source": "user_confirmation_in_current_task",
        "reviewer_identity_public": False,
        "credential_verification_by_codex": "not_performed",
        "completed_date": "2026-07-20",
    }
    private_record = {
        **public_record,
        "reviewed_items": reviewed,
        "attestation_note": (
            "The user stated that an expert reviewed the data and instructed Codex to mark "
            "the review complete. No reviewer identity or signed review artifact was provided."
        ),
    }
    write_json(root / "reports/fds_core_v3_3_expert_review_public.json", public_record)
    write_json(root / "reports/private/fds_core_v3_3_expert_review_record.json", private_record)
    report = {
        "schema_version": VERSION,
        "status": "formal_candidate_built_pending_full_reaudit",
        "predecessor_snapshot_id": predecessor["snapshot_id"],
        "events": 180,
        "qa": len(formal),
        "reviewed_l2_3": len(reviewed),
        "all_quality_eligible": all(
            item["quality"]["status"] == "eligible" for item in formal
        ),
        "task_counts": dict(sorted(Counter(item["task_id"] for item in formal).items())),
        "track_counts": dict(sorted(Counter(item["track"] for item in formal).items())),
    }
    write_json(root / "reports/fds_core_v3_3_formalization.json", report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
