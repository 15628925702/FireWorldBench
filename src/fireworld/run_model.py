from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a model on a frozen v2 QA manifest")
    parser.add_argument("--model", required=True)
    parser.add_argument("--track", choices=["S", "I", "V"], required=True)
    parser.parse_args()
    parser.error(
        "model adapters are not configured during architecture freeze; no inference was run"
    )
    return 2


raise SystemExit(main())
