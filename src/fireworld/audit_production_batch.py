"""Fail-closed physical and observability audit for a production FDS batch."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def device_ranges(path: Path) -> dict[str, tuple[float, float]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    names = rows[1]
    values = [[float(value) for value in row] for row in rows[2:] if len(row) == len(names)]
    if not values:
        raise ValueError(f"no device data: {path}")
    return {
        name: (min(row[index] for row in values), max(row[index] for row in values))
        for index, name in enumerate(names)
    }


def audit_run(batch: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    key = manifest["run_key"]
    row = manifest["matrix_row"]
    run = batch / key
    log = (run / f"{key}_fds.log").read_text(encoding="utf-8", errors="replace").lower()
    data = device_ranges(run / f"{key}_devc.csv")
    temps = [value for name, value in data.items() if name.startswith("T_R")]
    visibility = [value for name, value in data.items() if name.startswith("V_R")]
    velocity = [value for name, value in data.items() if name.startswith("U_R")]
    event_class = row["event_class"]
    no_error = not any(token in log for token in ("error", "fatal", "nan", "diverg"))
    checks = {
        "completed": "completed successfully" in log,
        "no_numerical_error": no_error,
        "sensor_csv": bool(data),
        "explicit_slcf": len(list(run.glob("*.sf"))) >= 4,
        "explicit_smoke3d": len(list(run.glob("*.s3d"))) >= 2,
        "thermal_signal": max(high for _, high in temps) - min(low for low, _ in temps) >= 10.0
        if event_class in {"fire", "non_fire_disturbance"}
        else True,
        "smoke_or_visibility_signal": min(low for low, _ in visibility) <= 10.0
        if event_class == "fire"
        else True,
        "ventilation_signal": max(high - low for low, high in velocity) >= 0.2
        if event_class == "ventilation_disturbance"
        else True,
    }
    return {
        "run_key": key,
        "event_id": row["event_id"],
        "event_class": event_class,
        "checks": checks,
        "pass": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    batch = args.root.resolve() / "fds_runs" / args.batch
    manifest = json.loads((batch / "input_manifest.json").read_text(encoding="utf-8"))
    audited = [audit_run(batch, item) for item in manifest["runs"]]
    report = {
        "batch": args.batch,
        "runs_audited": len(audited),
        "passed": sum(item["pass"] for item in audited),
        "failed": [item["run_key"] for item in audited if not item["pass"]],
        "runs": audited,
    }
    path = (
        args.root.resolve() / "reports" / "production_batches" / f"{args.batch}_physical_audit.json"
    )
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("batch", "runs_audited", "passed", "failed")}))
    return 0 if not report["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
