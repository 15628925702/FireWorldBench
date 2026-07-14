"""Formal-structure, small-N local pilot across all FireWorldBench tasks."""

from __future__ import annotations

import hashlib
import json
import re
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
    "trend_label", "target_variable", "horizon_s", "pair_id", "single_variable", "pair_valid", "pair_case_role", "source_case_group_id",
}


def _peak(record: dict[str, Any]) -> float:
    values = [value for key, value in record["variables_l0"].items() if key not in _METADATA_KEYS and isinstance(value, (int, float))]
    return max(values) if values else 0.0


def _annotate_case(records: list[dict[str, Any]]) -> None:
    first_peak, last_peak = _peak(records[0]), _peak(records[-1])
    peak = max(_peak(record) for record in records)
    trend = "increase" if last_peak > first_peak + 5.0 else "decrease" if last_peak + 5.0 < first_peak else "stable"
    state = "developed_or_peak" if peak >= 60.0 else "forming_or_early" if peak >= 35.0 else "baseline_or_no_fire"
    horizon = float(records[-1]["canonical_values"]["time_s"] - records[0]["canonical_values"]["time_s"])
    for record in records:
        record["variables_l0"].update({
            "fire_label": "fire_forming" if peak >= 60.0 else "not_fire_forming",
            "anomaly_label": "fire" if peak >= 60.0 else "non_fire",
            "state_label": state,
            "mechanism_labels": [],
            "consistency_label": "underdetermined",
            "trend_label": trend,
            "target_variable": "max_visible_temperature",
            "horizon_s": horizon,
    })


def _window_cases(records: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    if len(records) != 6:
        raise ValueError("formal-structure pilot expects six evenly sampled rows per source case")
    windows: list[list[dict[str, Any]]] = []
    for index, name in enumerate(("early", "middle", "late")):
        source_group = records[0]["case_id"]
        window: list[dict[str, Any]] = []
        for record in records[index * 2:(index + 1) * 2]:
            copied = dict(record)
            copied["variables_l0"] = dict(record["variables_l0"])
            copied["case_id"] = f"{source_group}:{name}"
            copied["sequence_id"] = copied["case_id"]
            copied["variables_l0"]["source_case_group_id"] = source_group
            window.append(copied)
        _annotate_case(window)
        windows.append(window)
    return windows


def _prompt_measurements(sample: dict[str, Any], records: list[dict[str, Any]]) -> None:
    lines: list[str] = []
    for observation, record in zip(sample["observations"], records):
        fields = [key for key in record["variables_l0"] if key not in _METADATA_KEYS]
        fields = sorted(fields, key=lambda key: (-abs(record["variables_l0"][key]) if isinstance(record["variables_l0"][key], (int, float)) else 0.0, key))[:6]
        values = ", ".join(f"{key}={record['variables_l0'][key]}" for key in fields)
        lines.append(f"{observation['observation_id']}: t={record['canonical_values']['time_s']} s; {values}")
    context = "\nVisible measurement rows:\n" + "\n".join(lines)
    if sample["task"] == "T3-B":
        grouped: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            grouped.setdefault(record["case_id"], []).append(record)
        summary = [
            f"{case_records[0]['variables_l0'].get('pair_case_role', 'case_unknown')}={case_id}: observed maximum={max(_peak(record) for record in case_records)}"
            for case_id, case_records in sorted(grouped.items())
        ]
        context += "\nVerified pair metadata: same smoke-exhaust configuration, only ignition-source longitudinal position changes.\n" + "\n".join(summary)
    if sample["task"] == "T2-B":
        context += "\nMechanism boundary: scalar measurements without a discriminating flow or geometry observation do not identify a mechanism; choose mechanism_unknown rather than infer one."
    if sample["task"] == "T1-A":
        context += "\nLocal planning warning rule: all displayed temperatures at or below 25 C means not_fire_forming; any displayed temperature at or above 60 C means fire_forming; otherwise insufficient_information."
    if sample["task"] == "T1-B":
        context += "\nLocal planning classification rule: all displayed temperatures at or below 25 C means non_fire; any displayed temperature at or above 60 C means fire; otherwise insufficient_information."
    if sample["task"] == "T1-C":
        context += "\nLocal planning query rule: when one candidate next observation is available, choose query_observation and select that candidate."
    if sample["task"] == "T2-A":
        context += "\nLocal planning state rule: all displayed temperatures at or below 25 C is baseline_or_no_fire; any displayed temperature at or above 60 C is developed_or_peak; otherwise forming_or_early."
    sample["question"]["prompt"] += context


def _build_split(records: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    parent = hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    outputs = [build_t1(records, split=split, parent_manifest_sha256=parent), build_t2(records, split=split, parent_manifest_sha256=parent), build_t3(records, split=split, parent_manifest_sha256=parent)]
    samples = [sample for output in outputs for sample in output["samples"]]
    by_case: dict[str, list[dict[str, Any]]] = {}
    by_case_uid: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_case.setdefault(record["case_id"], []).append(record)
        case_uid = "case_" + re.sub(r"[^A-Za-z0-9_-]+", "_", str(record["case_id"])).strip("_").lower()
        by_case_uid[case_uid] = by_case[record["case_id"]]
    for sample in samples:
        case_id = sample["physical_trace"]["initial_state"].get("case_id")
        context_records = by_case.get(case_id) or by_case_uid.get(sample["scenario"]["case_uid"], records)
        if sample["task"] == "T3-B":
            pair_id = sample["answer"]["pair_id"]
            context_records = [record for record in records if record["variables_l0"].get("pair_id") == pair_id]
        if sample["task"] == "T1-C" and len(sample["observations"]) > 1:
            visible = sample["observations"][0]
            candidate = sample["observations"][1]["observation_id"]
            sample["observations"] = [visible]
            sample["question"] = {
                "format": "structured_json",
                "prompt": "Using the initial observation only, choose whether to query the one available next observation or stop.",
                "options": [candidate, "stop"],
            }
            sample["answer"].update({"label": "query_observation", "selected_observation_id_or_stop": candidate, "evidence": [visible["observation_id"]]})
            sample["physical_trace"]["evidence_links"] = [visible["observation_id"]]
            context_records = context_records[:1]
        _prompt_measurements(sample, context_records)
        source_group = context_records[0]["variables_l0"].get("source_case_group_id") if context_records else None
        if source_group:
            group_digest = hashlib.sha256(str(source_group).encode()).hexdigest()[:12]
            sample["scenario"]["family_uid"] = f"family_{group_digest}"
    return sorted(samples, key=lambda item: (item["task"], item["sample_id"]))


def build_full_planning_pilot(root: Path, *, max_cases: int = 4, rows_per_case: int = 6) -> dict[str, Any]:
    if max_cases != 4:
        raise ValueError("formal-structure planning pilot requires exactly four cases")
    root = root.resolve()
    source_root = root / "data" / "raw" / "D01_Immersed-Tunnel-CFD"
    all_paths = {path.stem.removesuffix("_devc"): path for path in source_root.rglob("*.csv")}
    selected_names = ["70M01", "130M01", "70U16", "130U16"]
    paths = [all_paths[name] for name in selected_names[:max_cases] if name in all_paths]
    if len(paths) != max_cases:
        raise ValueError("not enough D01 CSV cases for the requested pilot")
    source_cases: list[list[list[dict[str, Any]]]] = []
    for path in paths:
        records = _records_from_file(path, source_root, rows_per_case, sample_strategy="early_mid_late")
        if not records:
            raise ValueError(f"no usable rows in {path.name}")
        source_cases.append(_window_cases(records))
    midpoint = max_cases // 2
    train_records = [record for source in source_cases[:midpoint] for window in source for record in window]
    dev_source_cases = source_cases[midpoint:]
    dev_records = [record for source in dev_source_cases for window in source for record in window]
    for window_index, (case_a, case_b) in enumerate(zip(dev_source_cases[0], dev_source_cases[1]), start=1):
        first_peak = max(_peak(record) for record in case_a)
        second_peak = max(_peak(record) for record in case_b)
        pair_label = "case_a_higher_risk" if first_peak > second_peak else "case_b_higher_risk" if second_peak > first_peak else "no_material_difference"
        for role, case_records in zip(("case_a", "case_b"), (case_a, case_b)):
            for record in case_records:
                record["variables_l0"].update({
                    "pair_id": f"pair_dev_{window_index:03d}",
                    "single_variable": True,
                    "pair_valid": True,
                    "pair_label": pair_label,
                    "pair_case_role": role,
                    "intervention_variable": "ignition_source_longitudinal_position_m",
                    "intervention_direction": "70m_vs_130m",
                })
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
            "train_case_count": len(source_cases[:midpoint]),
            "dev_case_count": len(source_cases[midpoint:]),
            "train_window_count": len(source_cases[:midpoint]) * 3,
            "dev_window_count": len(dev_source_cases) * 3,
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
