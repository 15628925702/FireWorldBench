"""Run the frozen v3.2 trajectory repairs with bounded local concurrency."""

from __future__ import annotations

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fireworld.mini_pilot import write_json

BATCH = "trajectory_repair_v3_2"
FAILURE_MARKERS = ("error", "fatal", "numerical instability", "nan", "diverg")


def run_one(batch: Path, item: dict[str, Any]) -> dict[str, Any]:
    key = item["run_key"]
    run = batch / key
    log = run / f"{key}_fds.log"
    started = datetime.now(UTC)
    with log.open("w") as handle:
        result = subprocess.run(
            [
                "bash",
                "-lc",
                ". /root/FDS/FDS6/bin/FDS6VARS.sh && "
                f"OMP_NUM_THREADS=1 /root/FDS/FDS6/bin/fds {key}.fds",
            ],
            cwd=run,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=False,
        )
    text = log.read_text(errors="replace").lower()
    passed = (
        result.returncode == 0
        and "completed successfully" in text
        and not any(marker in text for marker in FAILURE_MARKERS)
    )
    return {
        "run_key": key,
        "event_id": item["event_id"],
        "returncode": result.returncode,
        "passed": passed,
        "elapsed_s": round((datetime.now(UTC) - started).total_seconds(), 3),
        "log_ref": str(log),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    root = args.root.resolve()
    batch = root / "fds_runs" / BATCH
    manifest = json.loads((batch / "input_manifest.json").read_text())
    runs = manifest["runs"]
    results: list[dict[str, Any]] = []
    report_path = root / "reports/fds_core_v3_2_trajectory_repair_runs.json"
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_one, batch, item): item for item in runs}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            results.sort(key=lambda item: item["run_key"])
            report = {
                "schema_version": "fds-core-v3.2.0",
                "status": "running",
                "total": len(runs),
                "completed": len(results),
                "passed": sum(item["passed"] for item in results),
                "failed": [item["run_key"] for item in results if not item["passed"]],
                "runs": results,
            }
            write_json(report_path, report)
            print(json.dumps({key: report[key] for key in ("completed", "passed", "failed")}), flush=True)
    report["status"] = "completed" if not report["failed"] else "failed"
    write_json(report_path, report)
    return 0 if report["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
