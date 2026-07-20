"""Invalidate the disproven v3.1 acceptance without deleting its audit trail."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from fireworld.mini_pilot import write_json


def load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    reasons = [
        "L1-2 candidate payloads exposed exact future time metadata",
        "I/V filenames exposed timestamp and reverse labels",
        "L3-1 smoke trend reused visibility instead of independent soot",
        "L3-2 threshold audit repeated one threshold",
        "nine-task baseline Overall was null",
        "engineering acceptance values were hard-coded",
    ]
    for relative in (
        "reports/fds_core_v3_1_final_acceptance.json",
        "release/fireworldbench_fds_core_v3_1/release_manifest.json",
    ):
        path = root / relative
        if not path.is_file():
            continue
        record = load(path)
        record["release_status"] = "superseded_by_v3_2_repair"
        record["status"] = "superseded_by_v3_2_repair"
        record["supersession_reasons"] = reasons
        write_json(path, record)
    write_json(
        root / "reports" / "fds_core_v3_1_supersession.json",
        {
            "schema_version": "fds-core-v3.2.0",
            "superseded_release": "fireworldbench_fds_core_v3_1",
            "status": "superseded_by_v3_2_repair",
            "strict_qualified_events_after_recheck": 0,
            "reasons": reasons,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
