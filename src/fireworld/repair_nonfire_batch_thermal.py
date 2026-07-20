"""Repair all weak non-combustion thermal disturbances in a failed batch."""

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
    args = parser.parse_args()
    root = args.root.resolve()
    batch_dir = root / "fds_runs" / args.batch
    audit = json.loads(
        (root / "reports" / "production_batches" / f"{args.batch}_physical_audit.json").read_text()
    )
    failed = set(audit["failed"])
    manifest = json.loads((batch_dir / "input_manifest.json").read_text())
    targets = [item for item in manifest["runs"] if item["run_key"] in failed]
    if not targets or any(
        item["matrix_row"]["event_class"] != "non_fire_disturbance" for item in targets
    ):
        raise ValueError("expected only non-fire disturbance failures")
    matrix_path = root / "splits" / "production_matrix.v2.1.json"
    matrix = json.loads(matrix_path.read_text())
    ids = {item["event_id"] for item in targets}
    for row in matrix["rows"]:
        if row["event_id"] in ids:
            row["heater_temperature_c"] = 600.0
    quarantine = root / "quarantine" / f"{args.batch}_weak_nonfire_thermal"
    quarantine.mkdir(parents=True, exist_ok=True)
    for item in targets:
        source = batch_dir / item["run_key"]
        if source.exists():
            shutil.move(str(source), quarantine / item["run_key"])
    matrix_path.write_text(json.dumps(matrix, indent=2) + "\n")
    report = root / "reports" / "production_batches" / f"{args.batch}_nonfire_thermal_repair.json"
    report.write_text(
        json.dumps(
            {
                "created_at": datetime.now(UTC).isoformat(),
                "reason": "batch-wide non-combustion thermal signal below frozen threshold",
                "repaired_runs": sorted(failed),
                "new_heater_temperature_c": 600.0,
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
