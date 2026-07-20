"""Repair a known fire observability failure without changing frozen identity."""

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
    parser.add_argument("--run-key", required=True)
    parser.add_argument("--source-region", default="R3")
    args = parser.parse_args()
    root = args.root.resolve()
    batch_dir = root / "fds_runs" / args.batch
    manifest_path = batch_dir / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    target = next(item for item in manifest["runs"] if item["run_key"] == args.run_key)
    if target["matrix_row"]["event_class"] != "fire" or target["matrix_row"].get(
        "counterfactual_family"
    ):
        raise ValueError("only a standalone fire event can use this repair")
    event_id = target["event_id"]
    matrix_path = root / "splits" / "production_matrix.v2.1.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    row = next(item for item in matrix["rows"] if item["event_id"] == event_id)
    previous = row["source_region"]
    row["source_region"] = args.source_region
    quarantine = root / "quarantine" / f"{args.batch}_{args.run_key}_visibility_failure"
    quarantine.mkdir(parents=True, exist_ok=True)
    run_dir = batch_dir / args.run_key
    if run_dir.exists():
        shutil.move(str(run_dir), quarantine / args.run_key)
    matrix_path.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    report = root / "reports" / "production_batches" / f"{args.batch}_{args.run_key}_repair.json"
    report.write_text(
        json.dumps(
            {
                "created_at": datetime.now(UTC).isoformat(),
                "reason": "physical audit failed thermal and visibility observability",
                "event_id": event_id,
                "previous_source_region": previous,
                "new_source_region": args.source_region,
                "quarantine": str(quarantine.relative_to(root)),
                "frozen_invariants": [
                    "event_id",
                    "event_group",
                    "split",
                    "geometry",
                    "ventilation",
                    "hrrpua",
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
