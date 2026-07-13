"""Validate project bootstrap invariants from a source checkout."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fireworldbench.project_checks import REQUIRED_PATHS, validate_project  # noqa: E402


def main() -> int:
    errors = validate_project(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Project check failed with {len(errors)} error(s).")
        return 1
    print(f"Project check passed: {len(REQUIRED_PATHS)} required files and core policies verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
