"""Formal-structure, small-N local pilot across all FireWorldBench tasks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from fireworldbench.pipeline import write_json
from fireworldbench.planning_pilot import _records_from_file
from fireworldbench.t1_builder import build_t1
from fireworldbench.t2_builder import build_t2
from fireworldbench.t3_builder import build_t3

FULL_PILOT_VERSION = "P4-FORMAL-STRUCTURE-PLANNING-SMOKE-001"
_METADATA_KEYS = {
    "fire_label", "anomaly_label", "state_label", "mechanism_labels", "consistency_label",
    "trend_label", "target_variable", "horizon_s", "pair_id", "single_variable", "pair_valid",
}


def _peak(record: dict[str, Any]) -> float:
    values = [value for key, value in record["variables_l0"].items() if key not in _METADATA_KEYS and isinstance(value, (int, float))]
    return max(values) if values else 0.0


def _annotate_case(records: list[dict[str, Any]]) -> None:
    first_peak, last_peak = _peak(records[0]), _peak(records[-1])
    peak = max(_peak(record) for record in records)
    trend = "increase" if last_peak > first_peak + 5.0 else "decrease" if last_peak + 5.0 < first_peak else "stable"
    state = "growth" if trend == "increase" else "developed_or_peak" if peak >= 60.0 else "baseline_or_no_fire"
    horizon = float(records[-1]["canonical_values"]["time_s"] - records[0]["canonical_values"]["time_s"])
    for record in records:
        record["variables_l0"].update({
            "fire_label": "fire_forming" if peak >= 60.0 else "not_fire_forming",
            "anomaly_label": "fire" if peak >= 60.0 else "non_fire",
            "state_label": state,
            "mechanism_labels": [],
            "consistency_label": "consistent",
            "trend_label": trend,
            "target_variable": "max_visible_temperature",
            "horizon_s": horizon,
        })


def _prompt_measurements(sample: dict[str, Any], records: list[dict[str, Any]]) -> None:
    lines: list[str] = []
    for observation, record in zip(sample["observations"], records):
        fields = [key for key in record["variables_l0"] if key not in _METADATA_KEYS]
        fields = sorted(fields, key=lambda key: (-abs(record["variables_l0"][key]) if isinstance(record["variables_l0"][key], (int, float)) else 0.0, key))[:6]
        values = ", ".join(f"{key}={record['variables_l0'][key]}" for key in fields)
        lines.append(f"{observation['observation_id']}: t={record['canonical_values']['time_s']} s; {values}")
    context = "\nVisible measurement rows:\n" + "\n".join(lines)
    if sample["task"] == "T3-B":
        context += "\nPair metadata: no verified single-variable intervention is available."
    sample["question"]["prompt"] += context


def _build_split(records: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    parent = hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    outputs = [build_t1(records, split=split, parent_manifest_sha256=parent), build_t2(records, split=split, parent_manifest_sha256=parent), build_t3(records, split=split, parent_manifest_sha256=parent)]
    samples = [sample for output in outputs for sample in output["samples"]]
    by_case: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_case.setdefault(record["case_id"], []).append(record)
    for sample in samples:
        case_id = sample["physical_trace"]["initial_state"].get("case_id")
        context_records = by_case.get(case_id, records)
        _prompt_measurements(sample, context_records)
    return sorted(samples, key=lambda item: (item["task"], item["sample_id"]))


def build_full_planning_pilot(root: Path, *, max_cases: int = 4, rows_per_case: int = 6) -> dict[str, Any]:
    if max_cases < 2 or max_cases % 2:
        raise ValueError("max_cases must be an even number of at least two")
    root = root.resolve()
    source_root = root / "data" / "raw" / "D01_Immersed-Tunnel-CFD"
    paths = sorted(source_root.rglob("*.csv"), key=lambda path: path.as_posix())[:max_cases]
    if len(paths) != max_cases:
        raise ValueError("not enough D01 CSV cases for the requested pilot")
    cases: list[list[dict[str, Any]]] = []
    for path in paths:
        records = _records_from_file(path, source_root, rows_per_case)
        if not records:
            raise ValueError(f"no usable rows in {path.name}")
        _annotate_case(records)
        cases.append(records)
    midpoint = max_cases // 2
    train_records = [record for case in cases[:midpoint] for record in case]
    dev_records = [record for case in cases[midpoint:] for record in case]
    for record in dev_records:
        record["variables_l0"].update({"pair_id": "pair_dev_001", "single_variable": False, "pair_valid": False})
    train_samples = _build_split(train_records, "train_id")
    dev_samples = _build_split(dev_records, "dev_id")
    result = {
        "pilot_version": FULL_PILOT_VERSION,
        "scope": "local planning only; formal benchmark and publication use remain disabled",
        "planning_mode": True,
        "formal_benchmark_eligible": False,
        "source_dataset_ids": ["D01"],
        "case_split": {
            "strategy": "source_case_group_first",
            "train_case_count": len(cases[:midpoint]),
            "dev_case_count": len(cases[midpoint:]),
            "overlap": False,
        },
        "record_count": len(train_records) + len(dev_records),
        "train_samples": train_samples,
        "samples": dev_samples,
        "train_sample_count": len(train_samples),
        "sample_count": len(dev_samples),
        "task_counts": {task: sum(sample["task"] == task for sample in dev_samples) for task in ("T1-A", "T1-B", "T1-C", "T2-A", "T2-B", "T2-C", "T3-A", "T3-B", "T3-C")},
        "raw_files_modified": False,
        "test_private_assets_accessed": False,
    }
    result["manifest_sha256"] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return result


def write_full_planning_pilot(root: Path, output: Path, train_output: Path, max_cases: int, rows_per_case: int) -> dict[str, Any]:
    result = build_full_planning_pilot(root, max_cases=max_cases, rows_per_case=rows_per_case)
    write_json(result, output)
    write_json({"samples": result["train_samples"], "pilot_version": result["pilot_version"]}, train_output)
    return result
