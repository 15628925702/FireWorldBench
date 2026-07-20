"""Execute the v3.2 post-FDS pipeline in fail-closed order."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from fireworld.mini_pilot import write_json

PYTHON = "/root/miniconda3/envs/fireworldbench-v1/bin/python"


def command(module: str, root: Path) -> None:
    subprocess.run([PYTHON, "-m", module, "--root", str(root)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    runs = json.loads((root / "reports/fds_core_v3_2_trajectory_repair_runs.json").read_text())
    if runs["status"] != "completed" or runs["passed"] != runs["total"]:
        raise ValueError("repair FDS runs are not all complete")
    command("fireworld.audit_trajectory_repairs_v32", root)
    command("fireworld.integrate_trajectory_repairs_v32", root)
    command("fireworld.audit_global_trajectory_uniqueness_v32", root)
    command("fireworld.render_trajectory_repairs_v32", root)
    subprocess.run([PYTHON, "-m", "fireworld.build_global_release", "--root", str(root)], check=True)
    for path in (
        root / "fire_events/fds_core_v3_2",
        root / "derived/fds_core_v3_2",
        root / "qa/fds_core_v3_2",
    ):
        if path.exists():
            shutil.rmtree(path)
    for report in (
        root / "reports/fds_core_v3_2_build.json",
        root / "reports/fds_core_v3_2_data_audit.json",
    ):
        report.unlink(missing_ok=True)
    command("fireworld.rebuild_fds_core_v32", root)
    command("fireworld.audit_fds_core_v32", root)
    command("fireworld.run_baselines_v32", root)
    report = {"schema_version": "fds-core-v3.2.0", "status": "data_and_baseline_gates_passed_pending_final_audits", "stages": ["repair_physical", "repair_events", "global_trajectory_unique", "dynamic_visual", "fresh_raw_qa", "v3_2_rebuild", "data_audit", "baselines"]}
    write_json(root / "reports/fds_core_v3_2_post_fds_pipeline.json", report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
