"""Amend a physically invisible A/B pair while preserving its frozen identity."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--family", required=True)
    parser.add_argument("--source-region", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    matrix_path = root / "splits" / "production_matrix.v2.1.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    changed = []
    for row in matrix["rows"]:
        if row.get("counterfactual_family") == args.family:
            changed.append(
                {"event_id": row["event_id"], "previous_source_region": row["source_region"]}
            )
            row["source_region"] = args.source_region
    if len(changed) != 2:
        raise ValueError(f"expected exactly two rows, got {len(changed)}")
    batch_dir = root / "fds_runs" / args.batch
    manifest = json.loads((batch_dir / "input_manifest.json").read_text(encoding="utf-8"))
    quarantine = root / "quarantine" / f"{args.batch}_{args.family}_visibility_failure"
    quarantine.mkdir(parents=True, exist_ok=True)
    for item in manifest["runs"]:
        row = item["matrix_row"]
        if row.get("counterfactual_family") == args.family:
            source = batch_dir / item["run_key"]
            if source.exists():
                shutil.move(str(source), quarantine / item["run_key"])
    matrix_path.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    report = root / "reports" / "production_batches" / f"{args.batch}_{args.family}_repair.json"
    report.write_text(
        json.dumps(
            {
                "created_at": datetime.now(UTC).isoformat(),
                "reason": "physical audit failed thermal and visibility observability",
                "family": args.family,
                "changed": changed,
                "new_source_region": args.source_region,
                "quarantine": str(quarantine.relative_to(root)),
                "frozen_invariants": [
                    "event_id",
                    "event_group",
                    "split",
                    "geometry",
                    "ventilation",
                    "hrrpua A/B only",
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
