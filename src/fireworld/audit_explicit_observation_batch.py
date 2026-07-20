"""Fail-closed numerical and observability audit for explicit FDS runs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def ranges(path: Path) -> dict[str, dict[str, float]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    names = rows[1]
    data: list[list[float]] = []
    for row in rows[2:]:
        try:
            data.append([float(value) for value in row])
        except ValueError:
            continue
    if not data:
        raise ValueError(f"no numeric device rows: {path}")
    return {
        name: {"min": min(row[index] for row in data), "max": max(row[index] for row in data)}
        for index, name in enumerate(names)
        if name != "Time"
    }


def audit_run(run: Path) -> dict[str, Any]:
    key = run.name
    log = (run / f"{key}.stderr.log").read_text(encoding="utf-8", errors="replace").lower()
    stats = ranges(run / f"{key}_devc.csv")
    temperature = stats["T_SOURCE_NEAR"]
    visibility = stats["V_SOURCE_CEILING"]
    velocities = [value for name, value in stats.items() if name.startswith("U_")]
    speed_span = max(item["max"] - item["min"] for item in velocities)
    checks = {
        "completed": f"stop: fds completed successfully (chid: {key})" in log,
        "no_error": not any(token in log for token in ("error", "fatal", "nan", "diverg")),
        "temperature_signal": temperature["max"] >= 60.0
        and temperature["max"] - temperature["min"] >= 20.0,
        "visibility_signal": visibility["min"] <= 10.0
        and visibility["max"] - visibility["min"] >= 5.0,
        "ventilation_signal": speed_span >= 0.25,
        "slice_files": len(list(run.glob("*.sf"))) >= 4,
        "smoke3d_files": len(list(run.glob("*.s3d"))) >= 2,
    }
    return {
        "run": key,
        "checks": checks,
        "pass": all(checks.values()),
        "signals": {
            "source_temperature_c": temperature,
            "source_ceiling_visibility_m": visibility,
            "max_velocity_span_m_s": speed_span,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    runs = [
        audit_run(path)
        for path in sorted(args.batch.glob("obs_*"))
        if (path / f"{path.name}_devc.csv").is_file()
    ]
    report = {
        "batch": args.batch.name,
        "runs_audited": len(runs),
        "runs": runs,
        "passed": sum(item["pass"] for item in runs),
        "failed": [item["run"] for item in runs if not item["pass"]],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "runs_audited": report["runs_audited"],
                "passed": report["passed"],
                "failed": report["failed"],
            }
        )
    )
    return 0 if not report["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
