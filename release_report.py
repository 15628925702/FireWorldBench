"""Build deterministic public-package size reports from derived manifests."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from fireworld.cli_utils import read_json, write_json


def build_report(rows: list[dict[str, Any]], asset_root: Path) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    bytes_by_track: Counter[str] = Counter()
    bytes_by_split: Counter[str] = Counter()
    bytes_by_task: Counter[str] = Counter()
    missing_assets: list[str] = []
    for row in rows:
        track = str(row.get("track", "unknown"))
        split = str(row.get("split", "unknown"))
        task = str(row.get("task_id", "unknown"))
        counts[track] += 1
        bytes_seen = 0
        observation = row.get("observation", {})
        refs: list[str] = []
        if track == "S" and isinstance(observation.get("structured"), dict):
            ref = observation["structured"].get("ref")
            if isinstance(ref, str):
                refs.append(ref)
        elif track == "I" and isinstance(observation.get("images"), list):
            refs.extend(ref for ref in observation["images"] if isinstance(ref, str))
        elif track == "V" and isinstance(observation.get("video"), str):
            refs.append(observation["video"])
        for ref in refs:
            path = asset_root / ref
            if path.is_file():
                bytes_seen += path.stat().st_size
            else:
                missing_assets.append(ref)
        bytes_by_track[track] += bytes_seen
        bytes_by_split[split] += bytes_seen
        bytes_by_task[task] += bytes_seen
    return {
        "status": "measured_manifest_only",
        "qa_count": len(rows),
        "qa_count_by_track": dict(sorted(counts.items())),
        "bytes_by_track": dict(sorted(bytes_by_track.items())),
        "bytes_by_split": dict(sorted(bytes_by_split.items())),
        "bytes_by_task": dict(sorted(bytes_by_task.items())),
        "missing_assets": sorted(set(missing_assets)),
        "headroom_factor": 1.25,
        "note": "Does not include raw FDS archive; pilot-derived values replace release targets.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Report public v2 package sizes")
    parser.add_argument("--qa", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    value = read_json(args.qa)
    rows = value if isinstance(value, list) else [value]
    write_json(build_report(rows, args.asset_root), args.report)
    return 0


raise SystemExit(main())
