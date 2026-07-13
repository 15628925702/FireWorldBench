"""Minimal CLI for project bootstrap checks."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from fireworldbench import __version__
from fireworldbench.project_checks import discover_project_root, validate_project


def doctor(root: Path) -> int:
    errors = validate_project(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"FireWorldBench {__version__}: project bootstrap invariants verified at {root}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fwb")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor_parser = subparsers.add_parser("doctor", help="validate project bootstrap invariants")
    doctor_parser.add_argument(
        "--root",
        type=Path,
        help="project root; otherwise discover from cwd",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        try:
            root = args.root.resolve() if args.root else discover_project_root()
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}")
            return 2
        return doctor(root)
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
