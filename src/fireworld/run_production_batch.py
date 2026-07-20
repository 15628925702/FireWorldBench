"""Run one frozen FDS batch sequentially and stop at the first numerical failure."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

FAILURE_MARKERS = ("error", "numerical instability", "nan")


def run_batch(root: Path, batch: str) -> int:
    batch_dir = root / "fds_runs" / batch
    runs = sorted(path for path in batch_dir.iterdir() if path.is_dir())
    for run in runs:
        fds_input = run / f"{run.name}.fds"
        log = run / f"{run.name}_fds.log"
        if log.exists() and "completed successfully" in log.read_text(errors="replace").lower():
            continue
        with log.open("w", encoding="utf-8") as handle:
            # Load the bundled Intel runtime for deterministic batch execution.
            result = subprocess.run(
                [
                    "bash",
                    "-lc",
                    ". /root/FDS/FDS6/bin/FDS6VARS.sh && /root/FDS/FDS6/bin/fds " + fds_input.name,
                ],
                cwd=run,
                stdout=handle,
                stderr=subprocess.STDOUT,
                check=False,
            )
        text = log.read_text(errors="replace").lower()
        if (
            result.returncode != 0
            or "completed successfully" not in text
            or any(marker in text for marker in FAILURE_MARKERS)
        ):
            print(f"FAILED {run.name}")
            return 1
        print(f"PASSED {run.name}")
    print(f"PASSED_BATCH {batch}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    return run_batch(args.root.resolve(), args.batch)


if __name__ == "__main__":
    raise SystemExit(main())
