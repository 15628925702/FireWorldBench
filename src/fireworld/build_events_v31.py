"""Freeze a schema-valid v3.1 Fire Event snapshot for the final audit.

Split placement and snapshot hashes deliberately live in a separate manifest:
the Fire Event schema has closed provenance fields and must not be extended by
release bookkeeping.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from fireworld.build_global_release import load_events
from fireworld.mini_pilot import write_json
from fireworld.validation import validate_event_semantics, validate_schema

VERSION = "fds-core-v3.1.0"
LICENSE = {
    "license_id": "NIST-FDS-INTERNAL-RESEARCH",
    "evidence_ref": "governance/licenses/fds_internal_release_v3_1.md",
    "citation": "NIST Fire Dynamics Simulator (FDS) 6.11.1; internal research release terms.",
    "allowed_uses": ["research", "training", "evaluation", "derivation"],
    "redistribution": "restricted",
}


def digest(value: Any) -> str:
    content = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(content).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    destination = root / "fire_events" / "fds_core_v3_1"
    if destination.exists() and any(destination.iterdir()):
        raise ValueError(f"refusing to overwrite frozen snapshot: {destination}")

    rows: list[dict[str, str]] = []
    errors: list[str] = []
    event_pairs, _ = load_events(root)
    for original, split in sorted(event_pairs, key=lambda pair: pair[0]["event_id"]):
        event = json.loads(json.dumps(original))
        event["provenance"]["transform_version"] = VERSION
        event["license"] = LICENSE
        event_errors = validate_schema(event, "fire_event.schema.json") + validate_event_semantics(
            event
        )
        if event_errors:
            errors.extend(f"{event['event_id']}: {error}" for error in event_errors)
            continue
        path = destination / f"{event['event_id']}.json"
        write_json(path, event)
        rows.append({"event_id": event["event_id"], "split": split, "sha256": digest(event)})
    if errors:
        raise ValueError("event snapshot validation failed: " + "; ".join(errors[:20]))
    if len(rows) != 180:
        raise ValueError(f"expected 180 events, got {len(rows)}")
    manifest = {
        "schema_version": VERSION,
        "event_count": len(rows),
        "events": rows,
        "snapshot_sha256": digest(rows),
        "license_policy": "internal_research_only",
    }
    write_json(root / "reports" / "fds_core_v3_1_event_snapshot.json", manifest)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
