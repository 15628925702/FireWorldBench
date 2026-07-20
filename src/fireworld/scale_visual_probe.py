"""Render and audit a scale probe from audited raw FDS Smoke3D outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()
    root = args.root.resolve()
    runs = sorted((root / "fds_runs" / "pilot").glob("pilot_*"))[: args.count]
    output_root = root / "derived" / f"scale_visual_probe_{args.count}" / "I"
    report_root = root / "reports" / f"scale_visual_probe_{args.count}"
    output_root.mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, int | float | bool | str]] = []
    for run in runs:
        run_id = run.name
        output = output_root / run_id
        output.mkdir(parents=True, exist_ok=True)
        soot = next(run.glob("*_1_1.s3d"), None)
        temperature = next(run.glob("*_1_3.s3d"), None)
        smv = next(run.glob("*.smv"), None)
        if soot is None or temperature is None or smv is None:
            records.append({"run_id": run_id, "pass": False, "reason": "missing Smoke3D or SMV"})
            continue
        ssf = output / "render.ssf"
        lines = [
            "RENDERDIR",
            f" {output}",
            "RENDERTYPE",
            " PNG",
            "UNLOADALL",
            "LOADFILE",
            f" {soot.name}",
            "LOADFILE",
            f" {temperature.name}",
        ]
        for point in (10, 30, 60, 90):
            lines.extend(
                ["SETTIMEVAL", f" {float(point):.1f}", "RENDERONCE", f"{run_id}_t{point:03d}"]
            )
        ssf.write_text("\n".join(lines) + "\n", encoding="utf-8")
        for image in output.glob("*.png"):
            image.unlink()
        began = time.perf_counter()
        completed = subprocess.run(
            [
                "/usr/bin/timeout",
                "180",
                "/root/FDS/FDS6/smvbin/smokeview",
                str(smv.with_suffix("")),
                "-script",
                str(ssf),
                "-render_overwrite",
            ],
            cwd=run,
            env={**os.environ, "DISPLAY": ":99", "LIBGL_ALWAYS_SOFTWARE": "1"},
            text=True,
            capture_output=True,
            check=False,
        )
        elapsed = round(time.perf_counter() - began, 3)
        log = output / "render.log"
        log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
        text = log.read_text(encoding="utf-8", errors="replace").lower()
        images = [output / f"{run_id}_t{point:03d}.png" for point in (10, 30, 60, 90)]
        hashes = [sha256(image) for image in images if image.is_file()]
        passed = (
            completed.returncode == 0
            and len(hashes) == 4
            and len(set(hashes)) > 1
            and "global_times" not in text
            and "error" not in text
        )
        records.append(
            {
                "run_id": run_id,
                "pass": passed,
                "returncode": completed.returncode,
                "elapsed_s": elapsed,
                "frame_count": len(hashes),
                "unique_hash_count": len(set(hashes)),
                "global_times_error": "global_times" in text,
                "error_text": "error" in text,
                "image_bytes": sum(image.stat().st_size for image in images if image.is_file()),
                "log": str(log.relative_to(root)),
            }
        )
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "status": "pass" if records and all(row["pass"] for row in records) else "fail",
        "requested_runs": args.count,
        "rendered_runs": len(records),
        "pass_count": sum(bool(row["pass"]) for row in records),
        "mean_elapsed_s": round(
            sum(float(row.get("elapsed_s", 0.0)) for row in records) / len(records), 3
        )
        if records
        else None,
        "total_image_bytes": sum(int(row.get("image_bytes", 0)) for row in records),
        "records": records,
        "protocol": "UNLOADALL -> LOADFILE soot -> LOADFILE temperature -> SETTIMEVAL -> RENDERONCE",
    }
    (report_root / "scale_visual_probe_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
