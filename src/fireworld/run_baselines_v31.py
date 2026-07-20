"""Evaluate non-oracle chance, train-majority, and fixed-rule baselines."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from fireworld.mini_pilot import write_json
from fireworld.scoring import aggregate_scores

TEST_SPLITS = {"test_iid", "test_ood_geometry", "test_ood_condition", "test_ood_view_sensor"}


def answer_key(item: dict[str, Any]) -> tuple[str | None, tuple[tuple[str, Any], ...]]:
    answer = item["answer"]
    return answer["choice"], tuple(sorted(answer["fields"].items()))


def prediction(qa_id: str, choice: str | None, fields: dict[str, Any]) -> dict[str, Any]:
    return {"qa_id": qa_id, "answer": {"choice": choice, "fields": fields}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    rows: list[dict[str, Any]] = json.loads((root / "qa" / "fds_core_v3_1" / "qa.json").read_text())
    rows = [row for row in rows if row["quality"]["status"] == "eligible"]
    train = [row for row in rows if row["split"] == "train"]
    test = [row for row in rows if row["split"] in TEST_SPLITS]
    majority: dict[str, tuple[str | None, dict[str, Any]]] = {}
    for task in {row["task_id"] for row in train}:
        candidates = [row for row in train if row["task_id"] == task]
        key, _ = Counter(answer_key(row) for row in candidates).most_common(1)[0]
        majority[task] = (key[0], dict(key[1]))
    majority_predictions = {
        row["qa_id"]: prediction(row["qa_id"], *majority[row["task_id"]]) for row in test
    }
    rule_defaults: dict[str, tuple[str | None, dict[str, Any]]] = {
        "L1-1": (None, {"class": "fire"}),
        "L1-2": ("A", {"choice": "A"}),
        "L1-3": (None, {"consistency": "consistent", "violation_type": None}),
        "L2-1": (None, {"source_region": "R1", "stage": "incipient"}),
        "L2-2": (None, {"risk_region": "R1", "risk_level": "low"}),
        "L3-1": (
            None,
            {"temperature_trend": "stable", "smoke_trend": "stable", "visibility_trend": "stable"},
        ),
        "L3-2": (None, {"first_high_risk_region": "none"}),
        "L3-3": (None, {"comparison": "same"}),
    }
    rule_predictions = {
        row["qa_id"]: prediction(row["qa_id"], *rule_defaults[row["task_id"]]) for row in test
    }
    chance = {
        "L1-1": 0.25,
        "L1-2": 0.25,
        "L1-3": 0.5,
        "L2-1": 1 / 32,
        "L2-2": 1 / 32,
        "L3-1": 1 / 27,
        "L3-2": 1 / 9,
        "L3-3": 1 / 3,
    }
    report = {
        "schema_version": "fds-core-v3.1.0",
        "scope": "strict eligible QA only; L2-3 excluded because expert review is deferred",
        "oracle_included": False,
        "test_rows": len(test),
        "chance_primary": chance,
        "majority_train_to_test": aggregate_scores(test, majority_predictions),
        "fixed_rule_to_test": aggregate_scores(test, rule_predictions),
    }
    write_json(root / "reports" / "fds_core_v3_1_baselines.json", report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
