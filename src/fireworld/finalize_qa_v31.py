"""Bind the reconstructed QA set to the frozen v3.1 Event snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from fireworld.mini_pilot import write_json
from fireworld.validation import validate_event_groups, validate_qa_semantics, validate_schema

VERSION = "fds-core-v3.1.0"
LICENSE_REF = "governance/licenses/fds_internal_release_v3_1.md"


def digest(value: Any) -> str:
    content = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(content).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    events = {
        path.stem: json.loads(path.read_text())
        for path in (root / "fire_events" / "fds_core_v3_1").glob("FWE-*.json")
    }
    if len(events) != 180:
        raise ValueError(f"expected frozen 180 events, got {len(events)}")
    path = root / "qa" / "fds_core_v3_1" / "qa.json"
    rows: list[dict[str, Any]] = json.loads(path.read_text())
    for item in rows:
        event = events.get(item["event_id"])
        if event is None:
            raise ValueError(f"QA references an event outside snapshot: {item['qa_id']}")
        item["provenance"]["event_manifest_sha256"] = digest(event)
        item["provenance"]["builder_version"] = VERSION
        item["provenance"]["source_license_ref"] = LICENSE_REF
        if item["task_id"] == "L2-3":
            item["quality"]["status"] = "ambiguous"
            item["quality"]["ambiguity_reason"] = "expert_review_deferred_by_user"
    errors = [
        error
        for item in rows
        for error in validate_schema(item, "qa.schema.json") + validate_qa_semantics(item)
    ]
    errors.extend(validate_event_groups(rows))
    if errors:
        raise ValueError("final QA validation failed: " + "; ".join(errors[:20]))
    write_json(path, rows)
    manifest = {
        "schema_version": VERSION,
        "qa_count": len(rows),
        "qa_sha256": digest(rows),
        "strict_eligible_count": sum(item["quality"]["status"] == "eligible" for item in rows),
        "expert_review_deferred_count": sum(item["task_id"] == "L2-3" for item in rows),
    }
    write_json(root / "reports" / "fds_core_v3_1_qa_snapshot.json", manifest)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
