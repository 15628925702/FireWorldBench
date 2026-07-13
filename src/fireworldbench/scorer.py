"""Deterministic reference scorer for all nine FireWorldBench tasks."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from fireworldbench.evaluation import bootstrap_mean_ci, evidence_f1, macro_f1, pair_ranking_accuracy, trace_score
from fireworldbench.schema_validation import validate_prediction, validate_sample

SCORER_VERSION = "P3-SCORER-001"
TASKS = ("T1-A", "T1-B", "T1-C", "T2-A", "T2-B", "T2-C", "T3-A", "T3-B", "T3-C")


def _label(value: Mapping[str, Any]) -> str | None:
    answer = value.get("answer", {})
    return answer.get("label") if isinstance(answer, Mapping) else None


def _trace(value: Mapping[str, Any]) -> dict[str, Any]:
    answer = value.get("answer", {})
    return {key: answer.get(key) for key in ("initial_state", "mechanism_chain", "transitions", "outcome")}


def _score_one(sample: Mapping[str, Any], prediction: Mapping[str, Any] | None, *, status: str = "ok") -> dict[str, Any]:
    task = str(sample.get("task", "unknown"))
    gold_label = _label(sample)
    if status != "ok" or prediction is None:
        return {"sample_id": sample.get("sample_id"), "task": task, "case_uid": sample.get("scenario", {}).get("case_uid"), "status": status, "label_score": 0.0, "evidence_f1": 0.0, "primary_score": 0.0, "violations": []}
    pred_errors = validate_prediction(dict(prediction), dict(sample))
    pred_label = _label(prediction)
    gold_evidence = set(sample.get("physical_trace", {}).get("evidence_links", []))
    pred_evidence = set(prediction.get("evidence", []))
    unknown_evidence = pred_evidence - {item.get("observation_id") for item in sample.get("observations", [])}
    evidence_score = 0.0 if unknown_evidence else evidence_f1(gold_evidence, pred_evidence)
    label_score = 1.0 if pred_label == gold_label else 0.0
    if task == "T3-C":
        primary = trace_score(_trace(sample), _trace(prediction))
    elif task == "T3-B":
        primary = pair_ranking_accuracy([str(gold_label)], [str(pred_label)])
    elif task == "T1-C":
        query_count = 0 if prediction.get("answer", {}).get("selected_observation_id_or_stop") == "stop" else 1
        primary = max(0.0, label_score - 0.01 * query_count)
    else:
        primary = label_score
    violations: list[str] = []
    if unknown_evidence:
        violations.append("V_EVIDENCE")
    if pred_errors and not unknown_evidence:
        violations.append("V_SCHEMA")
    return {"sample_id": sample.get("sample_id"), "task": task, "case_uid": sample.get("scenario", {}).get("case_uid"), "pair_id": sample.get("answer", {}).get("pair_id"), "status": "invalid_prediction" if pred_errors else "ok", "label_score": label_score, "evidence_f1": evidence_score, "primary_score": primary, "violations": violations, "prediction_errors": pred_errors}


def score_samples(samples: Sequence[Mapping[str, Any]], predictions: Mapping[str, Mapping[str, Any]], statuses: Mapping[str, str] | None = None) -> dict[str, Any]:
    statuses = statuses or {}
    sample_scores: list[dict[str, Any]] = []
    for sample in sorted(samples, key=lambda value: str(value.get("sample_id", ""))):
        sample_id = str(sample.get("sample_id", ""))
        sample_errors = validate_sample(dict(sample))
        if sample_errors:
            sample_scores.append(_score_one(sample, None, status="invalid_sample"))
            sample_scores[-1]["sample_errors"] = sample_errors
            continue
        sample_scores.append(_score_one(sample, predictions.get(sample_id), status=statuses.get(sample_id, "missing_prediction") if sample_id not in predictions else statuses.get(sample_id, "ok")))

    task_scores: dict[str, list[float]] = defaultdict(list)
    case_scores: dict[str, list[float]] = defaultdict(list)
    pair_scores: dict[str, list[float]] = defaultdict(list)
    for item in sample_scores:
        task_scores[item["task"]].append(float(item["primary_score"]))
        case_scores[str(item.get("case_uid"))].append(float(item["primary_score"]))
        if item.get("pair_id"):
            pair_scores[str(item["pair_id"])].append(float(item["primary_score"]))
    task_metrics = {}
    for task in TASKS:
        values = task_scores.get(task, [])
        mean, low, high = bootstrap_mean_ci(values)
        task_metrics[task] = {"primary_metric": mean, "bootstrap_ci95": [low, high], "n_samples": len(values), "n_cases": len({item.get("case_uid") for item in sample_scores if item["task"] == task})}
    failure_counts = Counter(item["status"] for item in sample_scores if item["status"] != "ok")
    result = {
        "scorer_version": SCORER_VERSION,
        "statistical_unit": "case_or_validated_pair",
        "composite_score": {"enabled": False, "reason": "task metrics remain separate"},
        "sample_scores": sample_scores,
        "case_aggregates": {key: sum(values) / len(values) for key, values in sorted(case_scores.items())},
        "pair_aggregates": {key: sum(values) / len(values) for key, values in sorted(pair_scores.items())},
        "task_metrics": task_metrics,
        "failure_counts": dict(sorted(failure_counts.items())),
        "physical_violation_count": sum(len(item["violations"]) for item in sample_scores),
    }
    return result


def score_files(samples_path: Path, predictions_path: Path, output_path: Path) -> dict[str, Any]:
    samples = json.loads(samples_path.read_text(encoding="utf-8"))
    predictions = json.loads(predictions_path.read_text(encoding="utf-8"))
    sample_items = samples.get("samples", samples) if isinstance(samples, Mapping) else samples
    prediction_items = predictions.get("predictions", predictions) if isinstance(predictions, Mapping) else predictions
    prediction_map = {str(item["sample_id"]): item for item in prediction_items}
    result = score_samples(sample_items, prediction_map)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
