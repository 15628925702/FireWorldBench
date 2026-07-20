"""Wait for a raw batch then execute every fail-closed acceptance stage."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


def completed(log: Path) -> bool:
    return log.is_file() and "completed successfully" in log.read_text(errors="replace").lower()


def failed(log: Path) -> bool:
    if not log.is_file():
        return False
    text = log.read_text(errors="replace").lower()
    return any(
        marker in text for marker in ("error", "fatal", "numerical instability", "nan")
    ) and not completed(log)


def run(root: Path, batch: str) -> None:
    manifest = json.loads((root / "fds_runs" / batch / "input_manifest.json").read_text())["runs"]
    logs = [
        root / "fds_runs" / batch / item["run_key"] / f"{item['run_key']}_fds.log"
        for item in manifest
    ]
    while not all(completed(log) for log in logs):
        failures = [str(log) for log in logs if failed(log)]
        if failures:
            raise RuntimeError(f"raw FDS failure: {failures}")
        time.sleep(20)
    base = ["/root/miniconda3/envs/fireworldbench-v1/bin/python", "-m"]
    modules = (
        [*base, "fireworld.audit_production_batch", "--root", str(root), "--batch", batch],
        [*base, "fireworld.build_production_batch", "--root", str(root), "--batch", batch],
        [*base, "fireworld.render_production_images", "--root", str(root), "--batch", batch],
        [*base, "fireworld.render_production_video", "--root", str(root), "--batch", batch],
        [*base, "fireworld.attach_production_video", "--root", str(root), "--batch", batch],
        [
            *base,
            "fireworld.validate_dataset",
            "--events",
            str(root / "fire_events" / batch / "fire_events.json"),
            "--qa",
            str(root / "qa" / batch / "qa.json"),
        ],
        [*base, "fireworld.accept_production_batch", "--root", str(root), "--batch", batch],
    )
    for command in modules:
        subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    report = root / "reports" / "production_batches" / f"{args.batch}_finalizer.json"
    try:
        run(root, args.batch)
        result = {"batch": args.batch, "status": "accepted"}
    except Exception as error:
        result = {"batch": args.batch, "status": "rejected", "error": str(error)}
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0 if result["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
