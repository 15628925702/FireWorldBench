"""T3-A/B/C trend, counterfactual, and state-trace builders."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from typing import Any, Mapping, Sequence

from fireworldbench.pipeline import PIPELINE_VERSION
from fireworldbench.t1_builder import _observations

BUILDER_VERSION = "P3-BUILD-T3-001"
ALLOWED_SPLITS = {"train_id", "dev_id"}
TREND_LABELS = {"increase", "decrease", "stable", "mixed_or_non_monotonic"}
PAIR_LABELS = {"case_a_higher_risk", "case_b_higher_risk", "no_material_difference"}
TRACE_LABELS = {"trace_supported", "trace_partially_supported"}


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_").lower() or "unknown"


def _value(rows: Sequence[Mapping[str, Any]], key: str) -> Any:
    values = [row.get("variables_l0", {}).get(key) for row in rows if row.get("variables_l0", {}).get(key) not in (None, "")]
    return values[0] if len(values) == 1 or len(set(map(str, values))) == 1 and values else None


def _group_cases(records: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        case_id = str(record.get("case_id", ""))
        if case_id:
            groups[case_id].append(record)
    return dict(sorted(groups.items()))


def _sample(task: str, sample_key: str, rows: Sequence[Mapping[str, Any]], observations: list[dict[str, Any]], answer: dict[str, Any], split: str, benchmark_version: str, parent_manifest_sha256: str, config_sha256: str, intervention: dict[str, Any] | None = None) -> dict[str, Any]:
    evidence = [item["observation_id"] for item in observations]
    sample_id = f"FWB-v1-{task}-{_safe_id(sample_key)}-t3"
    clean_observations = [{key: value for key, value in item.items() if not key.startswith("_")} for item in observations]
    return {
        "schema_version": "2.0", "sample_id": sample_id, "benchmark_version": benchmark_version, "task": task, "split": split,
        "scenario": {"case_uid": f"case_{_safe_id(sample_key)}", "domain": "fire_physics", "family_uid": "family_t3", "intervention": intervention},
        "observations": clean_observations,
        "question": {"format": "structured_json", "prompt": f"Reason about the fire trend, intervention, or trace for {sample_key} using only supplied observations."},
        "answer": answer,
        "physical_trace": {"initial_state": answer.get("initial_state", {}), "mechanism_chain": answer.get("causal_chain", answer.get("mechanism_chain", [])), "transitions": answer.get("transitions", []), "outcome": answer.get("outcome", {"label": answer.get("label")}), "evidence_links": evidence, "origin": ["deterministic_rule"]},
        "scoring_metadata": {"visibility": "private", "gold_ref": "gold_" + _digest(sample_id)[:16], "metric_profile": task},
        "provenance": {"source_id": str(rows[0].get("source_dataset_id", "D01")), "source_version": PIPELINE_VERSION, "parent_manifest_sha256": parent_manifest_sha256, "builder_version": BUILDER_VERSION, "config_sha256": config_sha256, "annotation_status": "automatic"},
    }


def build_t3(records: Sequence[Mapping[str, Any]], *, split: str = "dev_id", benchmark_version: str = "0.1.0", parent_manifest_sha256: str | None = None, config_sha256: str | None = None) -> dict[str, Any]:
    if split not in ALLOWED_SPLITS:
        raise ValueError("T3 builder only permits train_id or dev_id; test construction is forbidden")
    parent_manifest_sha256 = parent_manifest_sha256 or _digest(records)
    config_sha256 = config_sha256 or _digest({"builder_version": BUILDER_VERSION, "split": split})
    samples: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    cases = _group_cases(records)
    for case_id, rows in cases.items():
        observations, observation_failures = _observations(rows)
        failures.extend({"case_id": case_id, **failure} for failure in observation_failures)
        if not observations:
            failures.append({"case_id": case_id, "code": "CASE_NO_VALID_OBSERVATIONS"})
            continue
        trend = _value(rows, "trend_label")
        target = _value(rows, "target_variable")
        horizon = _value(rows, "horizon_s")
        valid_horizon = isinstance(horizon, (int, float)) and float(horizon) > 0
        trend_label = trend if trend in TREND_LABELS and target and valid_horizon else "trend_unknown"
        trend_evidence = [item["observation_id"] for item in observations] if trend_label != "trend_unknown" else []
        samples.append(_sample("T3-A", case_id, rows, observations, {"label": trend_label, "horizon_s": float(horizon) if valid_horizon else 0.0, "target_variable": str(target or "unknown"), "trend_label": trend_label, "interval_or_range": {}, "evidence": trend_evidence, "uncertainty": "medium" if trend_evidence else "unknown"}, split, benchmark_version, parent_manifest_sha256, config_sha256))
        trace_label = _value(rows, "trace_label")
        initial_state = _value(rows, "initial_state")
        mechanism_chain = _value(rows, "mechanism_chain")
        transitions = _value(rows, "transitions")
        outcome = _value(rows, "outcome")
        valid_trace = trace_label in TRACE_LABELS and isinstance(initial_state, Mapping) and isinstance(mechanism_chain, list) and isinstance(transitions, list) and isinstance(outcome, Mapping)
        trace_label = trace_label if valid_trace else "trace_unknown"
        trace_evidence = [item["observation_id"] for item in observations] if valid_trace else []
        samples.append(_sample("T3-C", case_id, rows, observations, {"label": trace_label, "initial_state": dict(initial_state) if isinstance(initial_state, Mapping) else {}, "mechanism_chain": mechanism_chain if isinstance(mechanism_chain, list) else [], "transitions": transitions if isinstance(transitions, list) else [], "outcome": dict(outcome) if isinstance(outcome, Mapping) else {}, "evidence": trace_evidence, "uncertainty": "medium" if trace_evidence else "unknown"}, split, benchmark_version, parent_manifest_sha256, config_sha256))

    pair_groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        pair_id = record.get("variables_l0", {}).get("pair_id")
        if pair_id:
            pair_groups[str(pair_id)].append(record)
    for pair_id, rows in sorted(pair_groups.items()):
        observations, observation_failures = _observations(rows)
        failures.extend({"pair_id": pair_id, **failure} for failure in observation_failures)
        if not observations:
            failures.append({"pair_id": pair_id, "code": "PAIR_NO_VALID_OBSERVATIONS"})
            continue
        single_variable = _value(rows, "single_variable") is True or str(_value(rows, "single_variable")).lower() == "true"
        pair_valid = _value(rows, "pair_valid") is True or str(_value(rows, "pair_valid")).lower() == "true"
        label = _value(rows, "pair_label")
        label = label if pair_valid and single_variable and label in PAIR_LABELS else ("pair_invalid" if not pair_valid or not single_variable else "underdetermined")
        intervention = {"single_variable": single_variable, "variable": _value(rows, "intervention_variable"), "direction": _value(rows, "intervention_direction")}
        evidence = [item["observation_id"] for item in observations] if label not in {"pair_invalid", "underdetermined"} else []
        samples.append(_sample("T3-B", pair_id, rows, observations, {"label": label, "pair_id": pair_id, "intervention_variable": str(intervention["variable"] or "unknown"), "direction": str(intervention["direction"] or "unknown"), "causal_chain": [], "evidence": evidence, "uncertainty": "medium" if evidence else "unknown"}, split, benchmark_version, parent_manifest_sha256, config_sha256, intervention=intervention))
    samples.sort(key=lambda sample: (sample["task"], sample["scenario"]["case_uid"]))
    result = {"builder_version": BUILDER_VERSION, "split": split, "sample_count": len(samples), "case_count": len(cases), "failure_count": len(failures), "samples": samples, "failures": failures, "test_samples_generated": False}
    result["manifest_sha256"] = _digest(result)
    return result
