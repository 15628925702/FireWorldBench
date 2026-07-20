"""Regenerate and rerun only repair trajectories that fail physical audit."""

from __future__ import annotations

import argparse
import json
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fireworld.generate_production_batch import input_text
from fireworld.mini_pilot import write_json
from fireworld.run_trajectory_repairs_v32 import run_one

BATCH = "trajectory_repair_v3_2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    root = args.root.resolve()
    batch = root / "fds_runs" / BATCH
    audit = json.loads((root / "reports/fds_core_v3_2_trajectory_repair_physical_audit.json").read_text())
    failed = set(audit["failed"])
    if not failed:
        raise ValueError("physical audit has no failed repair runs")
    manifest_path = batch / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    selected: list[dict[str, Any]] = []
    quarantine = root / "quarantine" / f"trajectory_repair_v3_2_physical_failures_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    quarantine.mkdir(parents=True)
    for item in manifest["runs"]:
        key = item["run_key"]
        if key not in failed:
            continue
        row = item["matrix_row"]
        shutil.move(str(batch / key), quarantine / key)
        run = batch / key
        run.mkdir()
        if row["event_class"] == "non_fire_disturbance":
            row["heater_temperature_c"] = 350.0 + float(row["repair_environment_slot"])
            row["supply_velocity"] = min(float(row["supply_velocity"]), 0.25)
        elif row["event_class"] == "fire":
            row["hrrpua"] = max(1800.0, float(row["hrrpua"]) * 1.6)
        text = input_text(row, key).replace(
            "FireWorldBench v2.1 production", "FireWorldBench v3.2 physical repair"
        )
        (run / f"{key}.fds").write_text(text)
        selected.append(item)
    write_json(manifest_path, manifest)
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_one, batch, item) for item in selected]
        for future in as_completed(futures):
            results.append(future.result())
            print(json.dumps(results[-1]), flush=True)
    report = {
        "schema_version": "fds-core-v3.2.0",
        "status": "completed" if all(item["passed"] for item in results) else "failed",
        "quarantine": str(quarantine.relative_to(root)),
        "runs": sorted(results, key=lambda item: item["run_key"]),
    }
    write_json(root / "reports/fds_core_v3_2_targeted_physical_repairs.json", report)
    return 0 if report["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
