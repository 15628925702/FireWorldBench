"""T2-A/B/C state and mechanism sample builders."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from typing import Any, Mapping, Sequence

from fireworldbench.pipeline import PIPELINE_VERSION
from fireworldbench.t1_builder import _observations

BUILDER_VERSION = "P3-BUILD-T2-001"
ALLOWED_SPLITS = {"train_id", "dev_id"}
STATE_LABELS = {"baseline_or_no_fire", "forming_or_early", "growth", "developed_or_peak", "decay_or_ventilation_change"}
MECHANISM_LABELS = {"buoyant_plume", "ceiling_jet", "longitudinal_ventilation", "sidewall_extraction", "backlayering", "smoke_layer_formation", "sensor_artifact", "multiple_mechanisms"}
CONSISTENCY_LABELS = {"consistent", "inconsistent"}
VIOLATION_CODES = {"V_DIRECTION", "V_TEMPORAL_ORDER", "V_VENTILATION_SIGN", "V_BACKLAYERING", "V_MASS_ENERGY", "V_UNIT", "V_EVIDENCE", "V_OBSERVABILITY", "V_CAUSAL_LEAP", "V_STATE_TRANSITION", "V_PAIR_INVALID", "V_METADATA_LEAK"}


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_").lower() or "unknown"


def _group(records: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        case_id = str(record.get("case_id", ""))
        if case_id:
            groups[case_id].append(record)
    for rows in groups.values():
        rows.sort(key=lambda row: (str(row.get("sequence_id", "")), int(row.get("source_row_index", 0))))
    return dict(sorted(groups.items()))


def _value(rows: Sequence[Mapping[str, Any]], key: str) -> Any:
    values = [row.get("variables_l0", {}).get(key) for row in rows if row.get("variables_l0", {}).get(key) not in (None, "")]
    return values[0] if len(set(map(str, values))) == 1 and values else None


def _list_value(rows: Sequence[Mapping[str, Any]], key: str) -> list[str]:
    value = _value(rows, key)
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _sample(task: str, case_id: str, rows: Sequence[Mapping[str, Any]], observations: list[dict[str, Any]], answer: dict[str, Any], split: str, benchmark_version: str, parent_manifest_sha256: str, config_sha256: str) -> dict[str, Any]:
    evidence = [item["observation_id"] for item in observations]
    sample_id = f"FWB-v1-{task}-{_safe_id(case_id)}-t2"
    clean_observations = [{key: value for key, value in item.items() if not key.startswith("_")} for item in observations]
    return {
        "schema_version": "2.0", "sample_id": sample_id, "benchmark_version": benchmark_version, "task": task, "split": split,
        "scenario": {"case_uid": f"case_{_safe_id(case_id)}", "domain": "fire_physics", "family_uid": "family_t2", "intervention": None},
        "observations": clean_observations,
        "question": {"format": "structured_json", "prompt": f"Assess the physical fire state or mechanism for case {case_id} using only supplied observations."},
        "answer": answer,
        "physical_trace": {"initial_state": {"case_id": case_id}, "mechanism_chain": answer.get("mechanism_labels", []), "transitions": [], "outcome": {"label": answer.get("label")}, "evidence_links": evidence, "origin": ["deterministic_rule"]},
        "scoring_metadata": {"visibility": "private", "gold_ref": "gold_" + _digest(sample_id)[:16], "metric_profile": task},
        "provenance": {"source_id": str(rows[0].get("source_dataset_id", "D01")), "source_version": PIPELINE_VERSION, "parent_manifest_sha256": parent_manifest_sha256, "builder_version": BUILDER_VERSION, "config_sha256": config_sha256, "annotation_status": "automatic"},
    }


def build_t2(records: Sequence[Mapping[str, Any]], *, split: str = "dev_id", benchmark_version: str = "0.1.0", parent_manifest_sha256: str | None = None, config_sha256: str | None = None) -> dict[str, Any]:
    if split not in ALLOWED_SPLITS:
        raise ValueError("T2 builder only permits train_id or dev_id; test construction is forbidden")
    parent_manifest_sha256 = parent_manifest_sha256 or _digest(records)
    config_sha256 = config_sha256 or _digest({"builder_version": BUILDER_VERSION, "split": split})
    samples: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for case_id, rows in _group(records).items():
        observations, observation_failures = _observations(rows)
        failures.extend({"case_id": case_id, **failure} for failure in observation_failures)
        if not observations:
            failures.append({"case_id": case_id, "code": "CASE_NO_VALID_OBSERVATIONS"})
            continue
        state = _value(rows, "state_label")
        state_label = state if state in STATE_LABELS else "state_unknown"
        state_evidence = [item["observation_id"] for item in observations] if state_label != "state_unknown" else []
        samples.append(_sample("T2-A", case_id, rows, observations, {"label": state_label, "state_label": state_label, "risk_level": "medium" if state_evidence else "unknown", "evidence": state_evidence, "uncertainty": "medium" if state_evidence else "unknown"}, split, benchmark_version, parent_manifest_sha256, config_sha256))
        mechanisms = _list_value(rows, "mechanism_labels")
        mechanisms = [label for label in mechanisms if label in MECHANISM_LABELS]
        mechanism_label = mechanisms[0] if len(mechanisms) == 1 else ("multiple_mechanisms" if len(mechanisms) > 1 else "mechanism_unknown")
        mechanism_evidence = [item["observation_id"] for item in observations] if mechanisms else []
        samples.append(_sample("T2-B", case_id, rows, observations, {"label": mechanism_label, "mechanism_labels": mechanisms or ["mechanism_unknown"], "evidence": mechanism_evidence, "uncertainty": "medium" if mechanism_evidence else "unknown", "missing_information": [] if mechanism_evidence else ["discriminating_mechanism_observation"]}, split, benchmark_version, parent_manifest_sha256, config_sha256))
        consistency = _value(rows, "consistency_label")
        violation_codes = [code for code in _list_value(rows, "violation_codes") if code in VIOLATION_CODES]
        if consistency not in CONSISTENCY_LABELS or (consistency == "inconsistent" and not violation_codes):
            consistency = "underdetermined"
        consistency_evidence = [item["observation_id"] for item in observations] if consistency != "underdetermined" else []
        samples.append(_sample("T2-C", case_id, rows, observations, {"label": consistency, "consistency_label": consistency, "violation_codes": violation_codes, "evidence": consistency_evidence, "uncertainty": "medium" if consistency_evidence else "unknown"}, split, benchmark_version, parent_manifest_sha256, config_sha256))
    samples.sort(key=lambda sample: (sample["scenario"]["case_uid"], sample["task"]))
    result = {"builder_version": BUILDER_VERSION, "split": split, "sample_count": len(samples), "case_count": len({sample["scenario"]["case_uid"] for sample in samples}), "failure_count": len(failures), "samples": samples, "failures": failures, "test_samples_generated": False}
    result["manifest_sha256"] = _digest(result)
    return result
