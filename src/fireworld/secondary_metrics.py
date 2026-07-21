"""Protocol-permitted secondary metrics for deterministic scores."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from fireworld.contracts import MAIN_SPLITS, TASKS
from fireworld.scoring import score_one


def _rows(gold: list[dict[str, Any]], partition: str | None, track: str | None) -> list[dict[str, Any]]:
    return [
        row for row in gold
        if (partition is None and row.get("split") in MAIN_SPLITS or partition is not None and row.get("split") == partition)
        and (track is None or row.get("track") == track)
    ]


def _macro_f1(gold: list[str], pred: list[str]) -> float:
    labels = sorted(set(gold) | set(pred))
    values = []
    for label in labels:
        tp = sum(a == label and b == label for a, b in zip(gold, pred))
        fp = sum(a != label and b == label for a, b in zip(gold, pred))
        fn = sum(a == label and b != label for a, b in zip(gold, pred))
        values.append(0.0 if 2 * tp + fp + fn == 0 else 2 * tp / (2 * tp + fp + fn))
    return sum(values) / len(values) * 100 if values else 0.0


def compute_secondary(
    gold: list[dict[str, Any]], predictions: dict[str, dict[str, Any]],
    partition: str | None = None, track: str | None = None,
) -> dict[str, Any]:
    component: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    joint: dict[str, list[float]] = defaultdict(list)
    f1: dict[str, tuple[list[str], list[str]]] = {"L1-1": ([], []), "L2-3": ([], [])}
    confidence: list[tuple[float, float]] = []
    horizons: dict[str, int] = defaultdict(int)
    for row in _rows(gold, partition, track):
        task = row["task_id"]; pred = predictions.get(row["qa_id"]); answer = pred.get("answer", {}) if pred else {}
        fields = TASKS[task].answer_fields
        pairs = [("choice", row["answer"]["choice"], answer.get("choice"))] if task == "L1-2" else [
            (field, row["answer"]["fields"].get(field), answer.get("fields", {}).get(field)) for field in fields
        ]
        for field, truth, value in pairs:
            component[task][field].append(float(truth == value))
        if len(pairs) > 1:
            joint[task].append(float(all(truth == value for _, truth, value in pairs)))
        if task in f1:
            field = "class" if task == "L1-1" else "mechanism"
            f1[task][0].append(str(row["answer"]["fields"][field]))
            f1[task][1].append(str(answer.get("fields", {}).get(field, "__missing__")))
        if pred and isinstance(pred.get("confidence"), (int, float)):
            confidence.append((float(pred["confidence"]), score_one(row, pred)))
        context = " ".join(filter(None, [row.get("question"), row.get("observation", {}).get("context")]))
        match = re.search(r"(?:\+|next |within )(\d+(?:\.\d+)?) seconds", context, re.I)
        horizons[f"{match.group(1)}s" if match else "not_declared"] += 1
    result: dict[str, Any] = {
        "component_accuracy": {task: {field: sum(v) / len(v) * 100 for field, v in parts.items()} for task, parts in component.items()},
        "joint_exact_match": {task: sum(v) / len(v) * 100 for task, v in joint.items()},
        "macro_f1": {task: _macro_f1(a, b) for task, (a, b) in f1.items() if a},
        "horizon_counts": dict(sorted(horizons.items())),
        "difficulty": {"status": "unavailable_frozen_release_has_no_difficulty_field"},
    }
    if not confidence:
        result["calibration"] = {"status": "not_reported_no_non_null_confidence", "n": 0}
    else:
        brier = sum((c - correct) ** 2 for c, correct in confidence) / len(confidence)
        bins: dict[int, list[tuple[float, float]]] = defaultdict(list)
        for c, correct in confidence: bins[min(9, int(c * 10))].append((c, correct))
        ece = sum(len(v) / len(confidence) * abs(sum(x for x, _ in v) / len(v) - sum(y for _, y in v) / len(v)) for v in bins.values())
        result["calibration"] = {"status": "reported", "n": len(confidence), "ece": ece, "brier": brier}
    return result