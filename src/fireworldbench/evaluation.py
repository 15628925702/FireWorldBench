"""Small, deterministic evaluation primitives for P2-EVAL-001."""

from __future__ import annotations

import random
from collections import Counter
from typing import Sequence


def macro_f1(gold: Sequence[str], pred: Sequence[str], labels: Sequence[str]) -> float:
    if len(gold) != len(pred) or not gold:
        return 0.0
    scores: list[float] = []
    for label in labels:
        tp = sum(g == label and p == label for g, p in zip(gold, pred))
        fp = sum(g != label and p == label for g, p in zip(gold, pred))
        fn = sum(g == label and p != label for g, p in zip(gold, pred))
        denominator = 2 * tp + fp + fn
        scores.append((2 * tp / denominator) if denominator else 0.0)
    return sum(scores) / len(scores)


def evidence_f1(gold: set[str], pred: set[str]) -> float:
    if not gold and not pred:
        return 1.0
    if not gold or not pred:
        return 0.0
    precision = len(gold & pred) / len(pred)
    recall = len(gold & pred) / len(gold)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def pair_ranking_accuracy(gold: Sequence[str], pred: Sequence[str]) -> float:
    if len(gold) != len(pred) or not gold:
        return 0.0
    return sum(g == p for g, p in zip(gold, pred)) / len(gold)


def trace_score(gold: dict[str, object], pred: dict[str, object]) -> float:
    components = ("initial_state", "mechanism_chain", "transitions", "outcome")
    scores = [1.0 if gold.get(key) == pred.get(key) else 0.0 for key in components]
    return sum(scores) / len(scores)


def bootstrap_mean_ci(values: Sequence[float], seed: int = 20260714, resamples: int = 2000) -> tuple[float, float, float]:
    if not values:
        return (0.0, 0.0, 0.0)
    rng = random.Random(seed)
    means = [sum(rng.choices(list(values), k=len(values))) / len(values) for _ in range(resamples)]
    means.sort()
    low = means[int(0.025 * (len(means) - 1))]
    high = means[int(0.975 * (len(means) - 1))]
    return (sum(values) / len(values), low, high)


def score_status(status: str) -> float:
    return {"ok": 1.0, "refusal": 0.0, "invalid_json": 0.0, "timeout": 0.0, "tool_error": 0.0}.get(status, 0.0)


def label_distribution(labels: Sequence[str]) -> dict[str, int]:
    return dict(Counter(labels))
