from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build unified Fire Events from ingested source records"
    )
    parser.add_argument("--all-sources", action="store_true")
    parser.parse_args()
    print("Fire Event builders are frozen but source adapters are pending; no events were written.")
    return 0


raise SystemExit(main())
