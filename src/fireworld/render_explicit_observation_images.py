"""Render and attach dynamic I evidence for accepted explicit FDS fire runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT_BATCH = "explicit_observation_batch_01"
CF_BATCH = "explicit_counterfactual_01"
TIMES = (20, 50, 80, 110)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smoke_fields(run: Path) -> tuple[str, str]:
    smv = next(run.glob("*.smv")).read_text(encoding="utf-8", errors="replace").splitlines()
    pairs = [
        (smv[index + 1].strip(), smv[index + 2].strip())
        for index, line in enumerate(smv[:-2])
        if line.startswith("SMOKF3D")
    ]
    soot = next(filename for filename, label in pairs if label == "SOOT DENSITY")
    temperature = next(filename for filename, label in pairs if label == "TEMPERATURE")
    return soot, temperature


def render(
    root: Path, run: Path, event_id: str, group: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    output = root / "derived" / group / "I" / event_id
    output.mkdir(parents=True, exist_ok=True)
    soot, temperature = smoke_fields(run)
    ssf = output / "render.ssf"
    lines = [
        "RENDERDIR",
        f" {output}",
        "RENDERTYPE",
        " PNG",
        "UNLOADALL",
        "LOADFILE",
        f" {soot}",
        "LOADFILE",
        f" {temperature}",
    ]
    for time_s in TIMES:
        lines.extend(
            ["SETTIMEVAL", f" {time_s}.0", "RENDERONCE", f"{event_id.lower()}_t{time_s:03d}"]
        )
    ssf.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for image in output.glob("*.png"):
        image.unlink()
    stem = next(run.glob("*.smv")).with_suffix("")
    result = subprocess.run(
        [
            "/usr/bin/timeout",
            "180",
            "/root/FDS/FDS6/smvbin/smokeview",
            str(stem),
            "-script",
            str(ssf),
            "-render_overwrite",
        ],
        cwd=run,
        env={**os.environ, "DISPLAY": ":99", "LIBGL_ALWAYS_SOFTWARE": "1"},
        capture_output=True,
        text=True,
        check=False,
    )
    log = output / "render.log"
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    lower = log.read_text(encoding="utf-8", errors="replace").lower()
    images = []
    for time_s in TIMES:
        image = output / f"{event_id.lower()}_t{time_s:03d}.png"
        if not image.is_file():
            raise RuntimeError(f"missing image {image}")
        images.append(
            {"ref": str(image.relative_to(root)), "time_s": time_s, "sha256": digest(image)}
        )
    checks: dict[str, Any] = {
        "returncode": result.returncode,
        "global_times_error": "global_times" in lower,
        "load_error": "error" in lower and "loading file" not in lower,
        "unique_hashes": len({row["sha256"] for row in images}),
        "log": str(log.relative_to(root)),
    }
    checks["pass"] = (
        checks["returncode"] == 0
        and not checks["global_times_error"]
        and not checks["load_error"]
        and checks["unique_hashes"] > 1
    )
    if not checks["pass"]:
        raise RuntimeError(f"visual gate failed: {checks}")
    return images, checks


def attach(
    root: Path, events_path: Path, batch: str, group: str, keys: tuple[str, ...]
) -> dict[str, Any]:
    events = json.loads(events_path.read_text(encoding="utf-8"))
    fire_events = [
        event
        for event in events
        if any(
            label["name"] == "event_class" and label["value"] == "fire"
            for label in event["ground_truth"]["labels"]
        )
    ]
    if len(fire_events) != len(keys):
        raise ValueError(f"fire event/key mismatch: {len(fire_events)} vs {len(keys)}")
    report: dict[str, Any] = {}
    for event, key in zip(fire_events, keys, strict=True):
        images, checks = render(root, root / "fds_runs" / batch / key, event["event_id"], group)
        event["observations"]["images"] = images
        report[event["event_id"]] = checks
    events_path.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    primary = root / "fire_events" / "explicit_observation_pilot_10" / "fire_events.json"
    cf = root / "fire_events" / "explicit_counterfactual_01" / "fire_events.json"
    report = {
        "primary": attach(
            root,
            primary,
            ROOT_BATCH,
            "explicit_observation_pilot_10",
            ("obs_001", "obs_002", "obs_003", "obs_004", "obs_005", "obs_006", "obs_010"),
        ),
        "counterfactual": attach(
            root, cf, CF_BATCH, "explicit_counterfactual_01", ("cf_hrr_a", "cf_hrr_b")
        ),
    }
    out = root / "reports" / "explicit_observation_batch_01" / "batch_dynamic_image_audit.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "events": sum(len(value) for value in report.values()),
                "passed": all(
                    check["pass"] for group in report.values() for check in group.values()
                ),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
