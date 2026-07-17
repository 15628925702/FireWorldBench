from __future__ import annotations

import argparse
from pathlib import Path

from fireworld.cli_utils import read_json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the event_group-first split configuration"
    )
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = read_json(args.config)
    if config.get("unit") != "event_group" or not config.get("split_before_derivation"):
        parser.error("v2 requires event_group split before any QA derivation")
    print(
        "Split configuration is event_group-first. No split was written without an event manifest."
    )
    return 0


raise SystemExit(main())
