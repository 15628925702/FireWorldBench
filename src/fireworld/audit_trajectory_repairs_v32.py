"""Audit completed replacement runs before they can enter the v3.2 snapshot."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from fireworld.build_global_release import load_csv
from fireworld.mini_pilot import write_json

BATCH = "trajectory_repair_v3_2"


def ranges(path: Path) -> dict[str, tuple[float, float]]:
    with path.open(newline="") as handle:
        raw = list(csv.reader(handle))
    names = raw[1]
    values = [[float(value) for value in row] for row in raw[2:] if len(row) == len(names)]
    return {name: (min(row[index] for row in values), max(row[index] for row in values)) for index, name in enumerate(names)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    batch = root / "fds_runs" / BATCH
    manifest = json.loads((batch / "input_manifest.json").read_text())
    results: list[dict[str, Any]] = []
    trajectory_hashes: list[str] = []
    old_active_hashes: set[str] = set()
    old_events = {
        path.stem: json.loads(path.read_text())
        for path in (root / "fire_events/fds_core_v3_1").glob("FWE-*.json")
    }
    replacement_ids = {item["event_id"] for item in manifest["runs"]}
    for event_id, event in old_events.items():
        if event_id in replacement_ids:
            continue
        run = (root / event["provenance"]["fds"]["log_ref"]).parent
        devc = next(run.glob("*_devc.csv"))
        rows = load_csv(devc)
        old_active_hashes.add(
            hashlib.sha256(
                json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        )
    for item in manifest["runs"]:
        key = item["run_key"]
        run = batch / key
        row = item["matrix_row"]
        log = (run / f"{key}_fds.log").read_text(errors="replace").lower()
        devc = run / f"{key}_devc.csv"
        data = ranges(devc)
        temps = [value for name, value in data.items() if name.startswith("T_R")]
        visibility = [value for name, value in data.items() if name.startswith("V_R")]
        velocity = [value for name, value in data.items() if name.startswith("U_R")]
        event_class = row["event_class"]
        checks = {
            "completed": "completed successfully" in log,
            "no_numerical_error": not any(marker in log for marker in ("error", "fatal", "nan", "diverg")),
            "sensor_csv": devc.is_file() and devc.stat().st_size > 1000,
            "explicit_slcf": len(list(run.glob("*.sf"))) >= 4,
            "explicit_smoke3d": len(list(run.glob("*.s3d"))) >= 2,
            "thermal_signal": max(high for _, high in temps) - min(low for low, _ in temps) >= 10 if event_class in {"fire", "non_fire_disturbance"} else True,
            "visibility_signal": min(low for low, _ in visibility) <= 12 if event_class == "fire" else True,
            "ventilation_signal": max(high - low for low, high in velocity) >= 0.15 if event_class == "ventilation_disturbance" else True,
        }
        rows = load_csv(devc)
        trajectory_hash = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        trajectory_hashes.append(trajectory_hash)
        results.append({"run_key": key, "event_id": item["event_id"], "event_class": event_class, "checks": checks, "trajectory_sha256": trajectory_hash, "pass": all(checks.values())})
    duplicates = [digest for digest, count in Counter(trajectory_hashes).items() if count > 1]
    retained_collisions = sorted(set(trajectory_hashes) & old_active_hashes)
    failed = [item["run_key"] for item in results if not item["pass"]]
    report = {"schema_version": "fds-core-v3.2.0", "status": "passed" if not failed and not duplicates and not retained_collisions else "failed", "runs": len(results), "passed": sum(item["pass"] for item in results), "failed": failed, "repair_trajectory_duplicates": duplicates, "retained_trajectory_collisions": retained_collisions, "runs_detail": results}
    write_json(root / "reports/fds_core_v3_2_trajectory_repair_physical_audit.json", report)
    print(json.dumps({key: report[key] for key in ("status", "runs", "passed", "failed", "repair_trajectory_duplicates", "retained_trajectory_collisions")}, indent=2))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
