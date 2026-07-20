"""Repair a physically weak non-combustion thermal disturbance."""

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
    parser.add_argument("--temperature-c", type=float, default=600.0)
    args = parser.parse_args()
    root = args.root.resolve()
    batch_dir = root / "fds_runs" / args.batch
    manifest = json.loads((batch_dir / "input_manifest.json").read_text())
    target = next(item for item in manifest["runs"] if item["run_key"] == args.run_key)
    if target["matrix_row"]["event_class"] != "non_fire_disturbance":
        raise ValueError("expected non-fire disturbance")
    matrix_path = root / "splits" / "production_matrix.v2.1.json"
    matrix = json.loads(matrix_path.read_text())
    row = next(item for item in matrix["rows"] if item["event_id"] == target["event_id"])
    previous = row.get("heater_temperature_c", 120.0)
    row["heater_temperature_c"] = args.temperature_c
    quarantine = root / "quarantine" / f"{args.batch}_{args.run_key}_weak_thermal"
    quarantine.mkdir(parents=True, exist_ok=True)
    source = batch_dir / args.run_key
    if source.exists():
        shutil.move(str(source), quarantine / args.run_key)
    matrix_path.write_text(json.dumps(matrix, indent=2) + "\n")
    report = root / "reports" / "production_batches" / f"{args.batch}_{args.run_key}_repair.json"
    report.write_text(
        json.dumps(
            {
                "created_at": datetime.now(UTC).isoformat(),
                "reason": "non-combustion thermal signal below frozen 10C threshold",
                "event_id": target["event_id"],
                "previous_heater_temperature_c": previous,
                "new_heater_temperature_c": args.temperature_c,
                "no_combustion": True,
                "quarantine": str(quarantine.relative_to(root)),
            },
            indent=2,
        )
        + "\n"
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
