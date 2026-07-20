"""Require one unique measured device trajectory for each active Event."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from fireworld.build_global_release import load_events, raw_for_event
from fireworld.mini_pilot import write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    event_pairs, index = load_events(root)
    owners: dict[str, list[str]] = defaultdict(list)
    for event, _ in event_pairs:
        rows = raw_for_event(root, event, index)
        digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        owners[digest].append(event["event_id"])
    duplicates = {digest: ids for digest, ids in owners.items() if len(ids) > 1}
    report = {"schema_version": "fds-core-v3.2.0", "status": "passed" if len(owners) == 180 and not duplicates else "failed", "events": len(event_pairs), "unique_trajectories": len(owners), "duplicate_groups": duplicates}
    write_json(root / "reports/fds_core_v3_2_global_trajectory_uniqueness.json", report)
    print(json.dumps({key: report[key] for key in ("status", "events", "unique_trajectories")}, indent=2))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
