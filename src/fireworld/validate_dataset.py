from __future__ import annotations

import argparse
from pathlib import Path

from fireworld.validation import (
    read_records,
    validate_event_groups,
    validate_event_semantics,
    validate_qa_semantics,
    validate_schema,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Fire Event and QA files")
    parser.add_argument("--events", type=Path)
    parser.add_argument("--qa", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    if not args.events and not args.qa:
        parser.error("provide --events and/or --qa")
    errors: list[str] = []
    if args.events:
        for index, event in enumerate(read_records(args.events)):
            errors.extend(
                f"event[{index}] {item}"
                for item in validate_schema(event, "fire_event.schema.json")
            )
            errors.extend(f"event[{index}] {item}" for item in validate_event_semantics(event))
    if args.qa:
        rows = read_records(args.qa)
        for index, qa in enumerate(rows):
            errors.extend(f"qa[{index}] {item}" for item in validate_schema(qa, "qa.schema.json"))
            errors.extend(f"qa[{index}] {item}" for item in validate_qa_semantics(qa))
        errors.extend(validate_event_groups(rows))
    if errors:
        for error in errors:
            print(error)
        return 1
    print("FireWorldBench v2 validation passed")
    return 0


raise SystemExit(main())
