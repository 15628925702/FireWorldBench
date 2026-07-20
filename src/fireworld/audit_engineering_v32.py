"""Run and record the real v3.2 engineering gates."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from fireworld.mini_pilot import write_json

PYTHON = "/root/miniconda3/envs/fireworldbench-v1/bin/python"


def run(project: Path, arguments: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        arguments,
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "command": arguments,
        "exit_code": result.returncode,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    project = Path(__file__).resolve().parents[2]
    gates = {
        "ruff": run(project, [PYTHON, "-m", "ruff", "check", "src/fireworld", "tests"]),
        "mypy_strict": run(project, [PYTHON, "-m", "mypy", "--strict", "src/fireworld"]),
        "pytest": run(project, [PYTHON, "-m", "pytest", "-q"]),
    }
    checks = {
        "ruff_exit_zero": gates["ruff"]["exit_code"] == 0,
        "mypy_strict_exit_zero": gates["mypy_strict"]["exit_code"] == 0,
        "pytest_exit_zero": gates["pytest"]["exit_code"] == 0,
        "pytest_no_skips": "skipped" not in gates["pytest"]["stdout_tail"].lower(),
        "active_authority_only": (project / "src/fireworld").is_dir(),
    }
    report = {
        "schema_version": "fds-core-v3.2.0",
        "status": "passed" if all(checks.values()) else "blocked_by_engineering_gates",
        "gates": gates,
        "checks": checks,
    }
    write_json(root / "reports/fds_core_v3_2_engineering_audit.json", report)
    print(json.dumps({"status": report["status"], "checks": checks}, indent=2))
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
