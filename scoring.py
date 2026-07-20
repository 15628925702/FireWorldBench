"""Deterministic primary scoring for the frozen nine tasks."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from fireworld.contracts import MAIN_SPLITS, TASKS


def _field_accuracy(
    gold: dict[str, Any], prediction: dict[str, Any], fields: tuple[str, ...]
) -> float:
    correct = sum(1 for name in fields if gold.get(name) == prediction.get(name))
    return correct / len(fields)


def score_one(gold: dict[str, Any], prediction: dict[str, Any]) -> float:
    task_id = gold["task_id"]
    contract = TASKS[task_id]
    if task_id == "L1-2":
        return float(gold["answer"]["choice"] == prediction.get("choice"))
    return _field_accuracy(
        gold["answer"]["fields"], prediction.get("fields", {}), contract.answer_fields
    )


def _aggregate_task_scores(
    gold_rows: Iterable[dict[str, Any]], predictions: dict[str, dict[str, Any]]
) -> tuple[dict[str, float], int]:
    per_task: dict[str, list[float]] = defaultdict(list)
    missing = 0
    for gold in gold_rows:
        prediction = predictions.get(gold["qa_id"])
        if prediction is None:
            missing += 1
            score = 0.0
        else:
            score = score_one(gold, prediction)
        per_task[gold["task_id"]].append(score * 100.0)
    task_scores = {task: sum(values) / len(values) for task, values in sorted(per_task.items())}
    return task_scores, missing


def _layer_scores(task_scores: dict[str, float]) -> dict[str, float]:
    layer_scores: dict[str, float] = {}
    for layer in ("L1", "L2", "L3"):
        values = [
            task_scores[task] for task in TASKS if task.startswith(layer) and task in task_scores
        ]
        if values:
            layer_scores[layer] = sum(values) / len(values)
    return layer_scores


def aggregate_scores(
    gold_rows: Iterable[dict[str, Any]],
    predictions: dict[str, dict[str, Any]],
    partition: str | None = None,
) -> dict[str, Any]:
    rows = list(gold_rows)
    if partition in {"train", "dev"}:
        raise ValueError("train/dev are not valid leaderboard partitions")
    rows_have_split = any("split" in row for row in rows)
    main_rows = (
        [row for row in rows if row.get("split") == partition]
        if partition is not None
        else [row for row in rows if row.get("split") in MAIN_SPLITS]
        if rows_have_split
        else rows
    )
    external_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        split = str(row.get("split"))
        if split not in MAIN_SPLITS and split != partition:
            external_rows[split].append(row)

    task_scores, missing = _aggregate_task_scores(main_rows, predictions) if main_rows else ({}, 0)
    overall = sum(task_scores.values()) / 9 if len(task_scores) == 9 else None
    external_reports: dict[str, dict[str, Any]] = {}
    for split, split_rows in sorted(external_rows.items()):
        split_scores, split_missing = _aggregate_task_scores(split_rows, predictions)
        external_reports[split] = {
            "task_scores": split_scores,
            "missing_predictions": split_missing,
        }
    return {
        "task_scores": task_scores,
        "layer_scores": _layer_scores(task_scores),
        "overall": overall,
        "partition": partition or "main",
        "missing_predictions": missing,
        "external": external_reports,
    }
