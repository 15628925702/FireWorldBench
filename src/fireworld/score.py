from __future__ import annotations

import argparse
from pathlib import Path

from fireworld.cli_utils import write_json
from fireworld.scoring import aggregate_scores
from fireworld.validation import read_records


def main() -> int:
    parser = argparse.ArgumentParser(description="Score v2 predictions with deterministic metrics")
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    gold = read_records(args.gold)
    prediction_rows = read_records(args.predictions)
    predictions = {row["qa_id"]: row for row in prediction_rows}
    write_json(aggregate_scores(gold, predictions), args.report)
    return 0


raise SystemExit(main())
