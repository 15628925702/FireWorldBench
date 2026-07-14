"""Deterministic, train/dev-only numerical and temporal baselines."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from fireworldbench.schema_validation import TASK_LABELS

BASELINE_VERSION = "P4-BASELINE-NUM"
ALLOWED_SPLITS = {"train_id", "dev_id"}


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _majority(train_samples: Sequence[Mapping[str, Any]], task: str) -> str | None:
    labels = [sample.get("answer", {}).get("label") for sample in train_samples if sample.get("task") == task]
    labels = [str(label) for label in labels if label in TASK_LABELS.get(task, set())]
    return Counter(labels).most_common(1)[0][0] if labels else None


def _label(sample: Mapping[str, Any], strategy: str, seed: int, train_samples: Sequence[Mapping[str, Any]], thresholds: Mapping[str, float]) -> str | None:
    task = str(sample.get("task"))
    labels = sorted(TASK_LABELS.get(task, {"insufficient_information"}))
    if strategy == "chance":
        return labels[int(_hash([seed, sample.get("sample_id")])[:8], 16) % len(labels)]
    if strategy in {"majority", "traditional_ml", "domain_threshold"}:
        majority = _majority(train_samples, task)
        if majority:
            return majority
        if strategy == "domain_threshold" and task == "T1-A" and task in thresholds:
            return "fire_forming" if thresholds[task] >= 0.5 else "not_fire_forming"
        return None
    if strategy == "temporal_persistence":
        return {"T3-A": "stable", "T2-A": "baseline_or_no_fire"}.get(task, _majority(train_samples, task))
    raise ValueError(f"unknown baseline strategy: {strategy}")


def run_baseline(samples: Sequence[Mapping[str, Any]], *, strategy: str, seed: int = 20260714, train_samples: Sequence[Mapping[str, Any]] = (), thresholds: Mapping[str, float] | None = None) -> dict[str, Any]:
    thresholds = dict(thresholds or {})
    if any(sample.get("split") not in ALLOWED_SPLITS for sample in samples):
        raise ValueError("baseline only permits train_id or dev_id")
    if strategy == "domain_threshold" and thresholds and any(sample.get("split") == "test_id" for sample in train_samples):
        raise ValueError("threshold calibration cannot use test samples")
    config = {"baseline_version": BASELINE_VERSION, "strategy": strategy, "seed": seed, "thresholds": thresholds}
    predictions: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for sample in sorted(samples, key=lambda item: str(item.get("sample_id", ""))):
        label = _label(sample, strategy, seed, train_samples, thresholds)
        if label is None:
            failures.append({"sample_id": sample.get("sample_id"), "code": "NO_TRAIN_CALIBRATION_SUPPORT"})
            continue
        predictions.append({"schema_version": "2.0", "sample_id": sample.get("sample_id"), "task": sample.get("task"), "answer": {"label": label}, "evidence": [], "uncertainty": {"level": "unknown", "reason": f"{strategy} baseline"}, "missing_information": []})
    return {"baseline_version": BASELINE_VERSION, "strategy": strategy, "seed": seed, "config_sha256": _hash(config), "sample_count": len(predictions), "failure_count": len(failures), "predictions": predictions, "failures": failures, "test_tuning": False}


def run_baseline_file(samples_path: Path, output_path: Path, strategy: str, train_path: Path | None = None) -> dict[str, Any]:
    payload = json.loads(samples_path.read_text(encoding="utf-8"))
    train_payload = json.loads(train_path.read_text(encoding="utf-8")) if train_path else {"samples": []}
    samples = payload.get("samples", payload) if isinstance(payload, Mapping) else payload
    train_samples = train_payload.get("samples", train_payload) if isinstance(train_payload, Mapping) else train_payload
    result = run_baseline(samples, strategy=strategy, train_samples=train_samples)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
