"""Run all remaining frozen batches continuously through fail-closed acceptance."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

# ruff: noqa: SIM105


PYTHON = "/root/miniconda3/envs/fireworldbench-v1/bin/python"


def command(module: str, root: Path, batch: str) -> None:
    subprocess.run([PYTHON, "-m", module, "--root", str(root), "--batch", batch], check=True)


def accepted(root: Path, batch: str) -> bool:
    path = root / "reports" / "production_batches" / f"{batch}_acceptance.json"
    return path.is_file() and json.loads(path.read_text()).get("status") == "accepted"


def run_batch(root: Path, batch: str) -> None:
    subprocess.run(
        [
            "bash",
            "-lc",
            f"source /root/FDS/FDS6/bin/FDS6VARS.sh; cd {root}/5.项目实现/v1; "
            f"{PYTHON} -m fireworld.run_production_batch --root {root} --batch {batch}",
        ],
        check=True,
    )


def repair_known_physics_failures(root: Path, batch: str) -> bool:
    report = root / "reports" / "production_batches" / f"{batch}_physical_audit.json"
    if not report.is_file():
        return False
    failed = json.loads(report.read_text()).get("failed", [])
    manifest = json.loads((root / "fds_runs" / batch / "input_manifest.json").read_text())["runs"]
    rows = [item for item in manifest if item["run_key"] in failed]
    if not rows:
        return False

    families: set[str] = set()
    standalone_fires: list[str] = []
    nonfire_runs: list[str] = []
    for item in rows:
        matrix_row = item["matrix_row"]
        event_class = matrix_row["event_class"]
        family = matrix_row.get("counterfactual_family")
        if event_class == "non_fire_disturbance":
            nonfire_runs.append(item["run_key"])
        elif event_class == "fire" and family:
            families.add(str(family))
        elif event_class == "fire":
            standalone_fires.append(item["run_key"])
        else:
            return False

    for family in sorted(families):
        subprocess.run(
            [
                PYTHON,
                "-m",
                "fireworld.repair_failed_counterfactual",
                "--root",
                str(root),
                "--batch",
                batch,
                "--family",
                str(family),
                "--source-region",
                "R3",
            ],
            check=True,
        )
    for run_key in standalone_fires:
        subprocess.run(
            [
                PYTHON,
                "-m",
                "fireworld.repair_failed_fire_visibility",
                "--root",
                str(root),
                "--batch",
                batch,
                "--run-key",
                run_key,
                "--source-region",
                "R3",
            ],
            check=True,
        )
    for run_key in nonfire_runs:
        subprocess.run(
            [
                PYTHON,
                "-m",
                "fireworld.repair_failed_nonfire_thermal",
                "--root",
                str(root),
                "--batch",
                batch,
                "--run-key",
                run_key,
                "--temperature-c",
                "1000",
            ],
            check=True,
        )
    command("fireworld.generate_production_batch", root, batch)
    run_batch(root, batch)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--start", type=int, default=3)
    parser.add_argument("--end", type=int, default=17)
    args = parser.parse_args()
    root = args.root.resolve()
    status: list[dict[str, str]] = []
    for index in range(args.start, args.end + 1):
        batch = f"production_batch_{index:02d}"
        if accepted(root, batch):
            status.append({"batch": batch, "status": "already_accepted"})
            continue
        command("fireworld.generate_production_batch", root, batch)
        run_batch(root, batch)
        try:
            command("fireworld.finalize_production_batch", root, batch)
        except subprocess.CalledProcessError:
            pass
        if not accepted(root, batch):
            if not repair_known_physics_failures(root, batch):
                status.append({"batch": batch, "status": "rejected_unresolved"})
                break
            try:
                command("fireworld.finalize_production_batch", root, batch)
            except subprocess.CalledProcessError:
                pass
        if not accepted(root, batch):
            status.append({"batch": batch, "status": "rejected_after_repair"})
            break
        status.append({"batch": batch, "status": "accepted"})
    output = root / "reports" / "production_batches" / "continuous_production_status.json"
    output.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status))
    return 0 if all(item["status"] in {"accepted", "already_accepted"} for item in status) else 1


if __name__ == "__main__":
    raise SystemExit(main())
