from __future__ import annotations

import argparse
from pathlib import Path

from fireworld.cli_utils import write_json
from fireworld.scoring import aggregate_scores
from fireworld.validation import read_records, validate_prediction_semantics, validate_schema


def main() -> int:
    parser = argparse.ArgumentParser(description="Score v2 predictions with deterministic metrics")
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--partition", default="test_iid")
    args = parser.parse_args()
    gold = read_records(args.gold)
    if not any("split" in row and row.get("split") == args.partition for row in gold):
        parser.error(f"gold file has no rows for partition: {args.partition}")
    prediction_rows = read_records(args.predictions)
    gold_by_qa_id = {row["qa_id"]: row for row in gold if "qa_id" in row}
    schema_errors = [
        f"prediction[{index}] {error}"
        for index, row in enumerate(prediction_rows)
        for error in validate_schema(row, "prediction.v2.schema.json")
    ]
    schema_errors.extend(
        f"prediction[{index}] {error}"
        for index, row in enumerate(prediction_rows)
        for error in validate_prediction_semantics(
            row, gold_by_qa_id.get(row.get("qa_id"))
        )
    )
    unknown_ids = sorted({str(row["qa_id"]) for row in prediction_rows} - set(gold_by_qa_id))
    schema_errors.extend(f"prediction qa_id is absent from gold: {qa_id}" for qa_id in unknown_ids)
    if schema_errors:
        for error in schema_errors:
            print(error)
        return 1
    if len({row["qa_id"] for row in prediction_rows}) != len(prediction_rows):
        parser.error("duplicate prediction qa_id")
    predictions = {row["qa_id"]: row for row in prediction_rows}
    write_json(aggregate_scores(gold, predictions, partition=args.partition), args.report)
    return 0


raise SystemExit(main())
