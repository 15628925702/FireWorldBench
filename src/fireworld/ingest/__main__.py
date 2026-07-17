from __future__ import annotations

import argparse
from pathlib import Path

from fireworld.cli_utils import write_json
from fireworld.contracts import SOURCE_TASKS


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a source for Fire Event ingestion")
    parser.add_argument("--source", choices=sorted(SOURCE_TASKS), required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.input.exists():
        parser.error(f"input does not exist: {args.input}")
    files = (
        sorted(path for path in args.input.rglob("*") if path.is_file())
        if args.input.is_dir()
        else [args.input]
    )
    report = {
        "status": "inventory_only",
        "source": args.source,
        "file_count": len(files),
        "event_count": 0,
    }
    write_json(report, args.output)
    return 0


raise SystemExit(main())
