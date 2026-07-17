from __future__ import annotations

import argparse
from pathlib import Path

from fireworld.cli_utils import read_json, write_json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an FDS generation plan; execution is pilot-gated"
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    config = read_json(args.config)
    unresolved = [
        key for key, value in config.get("versions", {}).items() if str(value).startswith("TBD")
    ]
    if str(config.get("mesh", "")).startswith("TBD"):
        unresolved.append("mesh")
    if str(config.get("boundary_conditions", "")).startswith("TBD"):
        unresolved.append("boundary_conditions")
    if args.execute:
        if unresolved:
            parser.error(f"FDS execution blocked by unresolved fields: {', '.join(unresolved)}")
        parser.error("FDS execution adapter is not implemented; no simulation was started")
    report = {
        "status": "planned_not_generated",
        "target": config.get("independent_event_target"),
        "unresolved": unresolved,
    }
    write_json(report, None)
    return 0


raise SystemExit(main())
