"""T1-A/B/C builders with explicit observability and train-only calibration gates."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from typing import Any, Mapping, Sequence

from fireworldbench.pipeline import PIPELINE_VERSION

BUILDER_VERSION = "P3-BUILD-T1-001"
ALLOWED_SPLITS = {"train_id", "dev_id"}
KNOWN_GOLD_ORIGINS = {"direct_measurement", "simulator_truth", "deterministic_rule", "expert_annotation"}


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_").lower() or "unknown"


def _group_records(records: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        case_id = str(record.get("case_id", ""))
        if case_id:
            grouped[case_id].append(record)
    def sort_key(row: Mapping[str, Any]) -> tuple[float, str, int]:
        raw_time = row.get("canonical_values", {}).get("time_s", 0.0)
        time_s = float(raw_time) if isinstance(raw_time, (int, float)) else float("inf")
        raw_index = row.get("source_row_index", 0)
        row_index = int(raw_index) if isinstance(raw_index, (int, float, str)) and str(raw_index).isdigit() else 0
        return time_s, str(row.get("sequence_id", "")), row_index

    return {case_id: sorted(rows, key=sort_key) for case_id, rows in sorted(grouped.items())}


def _observations(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    observations: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        status = row.get("status")
        time_s = row.get("canonical_values", {}).get("time_s")
        if status != "PASS" or not isinstance(time_s, (int, float)):
            failures.append({"code": "OBSERVATION_NOT_CANONICAL", "source_row_index": row.get("source_row_index"), "reason": status or "missing_time_s"})
            continue
        units = {str(key): str(value) for key, value in dict(row.get("units_l0", {})).items() if str(value).strip() and str(value).upper() != "UNKNOWN"}
        units["time"] = "s"
        observation_id = "obs_" + _digest([row.get("source_sha256"), row.get("source_row_index"), row.get("sequence_id")])[:12]
        observations.append({
            "observation_id": observation_id,
            "modality": "sensor_table",
            "time_range_s": [float(time_s), float(time_s)],
            "quality": "valid",
            "content_ref": str(row.get("source_relative_path", "")),
            "units": units,
            "visible_fields": sorted(str(key) for key in dict(row.get("variables_l0", {}))),
            "_row_index": index - 1,
        })
    return observations, failures


def _explicit_label(rows: Sequence[Mapping[str, Any]], key: str) -> str | None:
    values = {str(row.get("variables_l0", {}).get(key)) for row in rows if row.get("variables_l0", {}).get(key) not in (None, "")}
    return values.pop() if len(values) == 1 else None


def _sample(
    *, task: str, case_id: str, rows: Sequence[Mapping[str, Any]], observations: list[dict[str, Any]],
    answer: dict[str, Any], gold_origin: str, split: str, benchmark_version: str,
    parent_manifest_sha256: str, config_sha256: str,
) -> dict[str, Any]:
    evidence = [item["observation_id"] for item in observations]
    sample_id = f"FWB-v1-{task}-{_safe_id(case_id)}-t1"
    clean_observations = [{key: value for key, value in item.items() if not key.startswith("_")} for item in observations]
    return {
        "schema_version": "2.0",
        "sample_id": sample_id,
        "benchmark_version": benchmark_version,
        "task": task,
        "split": split,
        "scenario": {"case_uid": f"case_{_safe_id(case_id)}", "domain": "fire_physics", "family_uid": "family_t1", "intervention": None},
        "observations": clean_observations,
        "question": {
            "format": "structured_json",
            "prompt": f"Assess the fire-warning task for case {case_id} using only the supplied observations.",
        },
        "answer": answer,
        "physical_trace": {
            "initial_state": {"case_id": case_id},
            "mechanism_chain": [],
            "transitions": [],
            "outcome": {"label": answer.get("label")},
            "evidence_links": evidence,
            "origin": [gold_origin],
        },
        "scoring_metadata": {"visibility": "private", "gold_ref": "gold_" + _digest(sample_id)[:16], "metric_profile": task},
        "provenance": {
            "source_id": str(rows[0].get("source_dataset_id", "D01")),
            "source_version": PIPELINE_VERSION,
            "parent_manifest_sha256": parent_manifest_sha256,
            "builder_version": BUILDER_VERSION,
            "config_sha256": config_sha256,
            "annotation_status": "automatic",
        },
    }


def build_t1(
    records: Sequence[Mapping[str, Any]], *, split: str = "dev_id", benchmark_version: str = "0.1.0",
    parent_manifest_sha256: str | None = None, config_sha256: str | None = None,
    thresholds: Mapping[str, float] | None = None, threshold_source: str | None = None,
) -> dict[str, Any]:
    """Build T1 samples from canonical records; never builds test samples."""
    if split not in ALLOWED_SPLITS:
        raise ValueError("T1 builder only permits train_id or dev_id; test construction is forbidden")
    if thresholds and threshold_source not in {"train", "calibration"}:
        raise ValueError("thresholds must come from train or calibration")
    parent_manifest_sha256 = parent_manifest_sha256 or _digest(records)
    config_sha256 = config_sha256 or _digest({"builder_version": BUILDER_VERSION, "split": split, "threshold_source": threshold_source})
    samples: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for case_id, rows in _group_records(records).items():
        observations, observation_failures = _observations(rows)
        failures.extend({"case_id": case_id, **failure} for failure in observation_failures)
        if not observations:
            failures.append({"case_id": case_id, "code": "CASE_NO_VALID_OBSERVATIONS"})
            continue
        fire_label = _explicit_label(rows, "fire_label")
        fire_label = fire_label if fire_label in {"fire_forming", "not_fire_forming"} else "insufficient_information"
        fire_evidence = [item["observation_id"] for item in observations] if fire_label != "insufficient_information" else []
        samples.append(_sample(task="T1-A", case_id=case_id, rows=rows, observations=observations, split=split, benchmark_version=benchmark_version, parent_manifest_sha256=parent_manifest_sha256, config_sha256=config_sha256, gold_origin="deterministic_rule", answer={"label": fire_label, "risk_level": "medium" if fire_label != "insufficient_information" else "unknown", "evidence": fire_evidence, "uncertainty": "medium" if fire_label != "insufficient_information" else "unknown", "missing_information": [] if fire_evidence else ["validated_fire_signal"]}))
        anomaly_label = _explicit_label(rows, "anomaly_label")
        allowed_anomaly = {"fire", "non_fire", "ventilation_disturbance", "sensor_fault"}
        anomaly_label = anomaly_label if anomaly_label in allowed_anomaly else "insufficient_information"
        anomaly_evidence = [item["observation_id"] for item in observations] if anomaly_label != "insufficient_information" else []
        samples.append(_sample(task="T1-B", case_id=case_id, rows=rows, observations=observations, split=split, benchmark_version=benchmark_version, parent_manifest_sha256=parent_manifest_sha256, config_sha256=config_sha256, gold_origin="deterministic_rule", answer={"label": anomaly_label, "dominant_mechanism": anomaly_label, "evidence": anomaly_evidence, "uncertainty": "medium" if anomaly_evidence else "unknown", "missing_information": [] if anomaly_evidence else ["discriminating_observation"]}))
        selected = observations[1]["observation_id"] if len(observations) > 1 else None
        query_label = "query_observation" if selected else "stop_and_decide"
        samples.append(_sample(task="T1-C", case_id=case_id, rows=rows, observations=observations, split=split, benchmark_version=benchmark_version, parent_manifest_sha256=parent_manifest_sha256, config_sha256=config_sha256, gold_origin="deterministic_rule", answer={"label": query_label, "selected_observation_id_or_stop": selected or "stop", "query_cost": 1 if selected else 0, "expected_information_value": 1.0 if selected else 0.0, "evidence": [] if selected is None else [selected]}))
    samples.sort(key=lambda sample: (sample["scenario"]["case_uid"], sample["task"]))
    result = {"builder_version": BUILDER_VERSION, "split": split, "sample_count": len(samples), "case_count": len({sample["scenario"]["case_uid"] for sample in samples}), "failure_count": len(failures), "samples": samples, "failures": failures, "threshold_source": threshold_source, "test_samples_generated": False}
    result["manifest_sha256"] = _digest(result)
    return result
