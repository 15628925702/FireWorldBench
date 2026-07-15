"""Lightweight personal-research dataset build with visible holdout data."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from fireworldbench.full_planning_pilot import _build_split, _peak, _window_cases
from fireworldbench.pipeline import sha256_file, write_json
from fireworldbench.planning_pilot import _number

RESEARCH_VERSION = "P5-RESEARCH-RUN-001"
TASKS = ("T1-A", "T1-B", "T1-C", "T2-A", "T2-B", "T2-C", "T3-A", "T3-B", "T3-C")
NAME_PATTERN = re.compile(r"^(70|100|130)([MU]\d{2})_devc$")


def _family(stem: str) -> str:
    match = NAME_PATTERN.fullmatch(stem)
    if match is None:
        raise ValueError(f"unexpected D01 case name: {stem}")
    return match.group(2)


def _partition_families(families: list[str], seed: int) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {"train": [], "dev": [], "holdout": []}
    for kind in ("M", "U"):
        values = sorted(
            (value for value in families if value.startswith(kind)),
            key=lambda value: hashlib.sha256(f"{seed}:{value}".encode()).hexdigest(),
        )
        if len(values) < 3:
            raise ValueError(f"at least three complete {kind} families are required")
        train_count = max(1, round(len(values) * 0.70))
        dev_count = max(1, round(len(values) * 0.15))
        if train_count + dev_count >= len(values):
            train_count = len(values) - 2
            dev_count = 1
        result["train"].extend(values[:train_count])
        result["dev"].extend(values[train_count : train_count + dev_count])
        result["holdout"].extend(values[train_count + dev_count :])
    return {key: sorted(value) for key, value in result.items()}


def _numeric_row_count(path: Path) -> int:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, [])
        headers = next(reader, [])
        time_index = next(
            (index for index, value in enumerate(headers) if value.strip().casefold() == "time"),
            None,
        )
        if time_index is None:
            raise ValueError(f"Time header missing in {path.name}")
        return sum(
            1
            for row in reader
            if time_index < len(row) and isinstance(_number(row[time_index]), float)
        )


def _sample_case(path: Path, source_root: Path) -> list[dict[str, Any]]:
    row_count = _numeric_row_count(path)
    if row_count < 6:
        raise ValueError(f"at least six numeric rows required in {path.name}")
    middle = row_count // 2
    selected = {0, 1, middle - 1, middle, row_count - 2, row_count - 1}
    relative = path.relative_to(source_root).as_posix()
    case_id = "D01:" + relative
    source_sha = sha256_file(path)
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        units = next(reader, [])
        headers = next(reader, [])
        time_index = next(
            index for index, value in enumerate(headers) if value.strip().casefold() == "time"
        )
        numeric_index = 0
        for row_index, row in enumerate(reader, start=3):
            time_value = _number(row[time_index]) if time_index < len(row) else ""
            if not isinstance(time_value, float):
                continue
            if numeric_index in selected:
                variables = {
                    headers[index].strip(): _number(value)
                    for index, value in enumerate(row)
                    if index < len(headers) and headers[index].strip() and index != time_index
                }
                records.append(
                    {
                        "source_dataset_id": "D01",
                        "source_relative_path": relative,
                        "source_sha256": source_sha,
                        "source_row_index": row_index,
                        "case_id": case_id,
                        "sequence_id": case_id,
                        "time_value_l0": time_value,
                        "time_unit_l0": units[time_index].strip()
                        if time_index < len(units)
                        else "s",
                        "variables_l0": variables,
                        "units_l0": {
                            headers[index].strip(): units[index].strip()
                            if index < len(units)
                            else "UNKNOWN"
                            for index in range(len(headers))
                            if headers[index].strip() and index != time_index
                        },
                        "canonical_values": {"time_s": time_value},
                        "conversion_trace": {"time": {"rule": "source_s", "status": "PASS"}},
                        "status": "PASS",
                        "builder_version": RESEARCH_VERSION,
                    }
                )
            numeric_index += 1
    if len(records) != 6:
        raise ValueError(f"six sampled rows were not recovered from {path.name}")
    return records


def _mark_pairs(
    partition: str,
    families: list[str],
    windows: Mapping[str, list[list[dict[str, Any]]]],
) -> None:
    for family in families:
        case_a = windows[f"70{family}"]
        case_b = windows[f"130{family}"]
        for window_index, (window_a, window_b) in enumerate(
            zip(case_a, case_b, strict=True), start=1
        ):
            first_peak = max(_peak(record) for record in window_a)
            second_peak = max(_peak(record) for record in window_b)
            label = (
                "case_a_higher_risk"
                if first_peak > second_peak
                else "case_b_higher_risk"
                if second_peak > first_peak
                else "no_material_difference"
            )
            for role, records in (("case_a", window_a), ("case_b", window_b)):
                for record in records:
                    record["variables_l0"].update(
                        {
                            "pair_id": f"pair_{partition}_{family}_{window_index:02d}",
                            "single_variable": True,
                            "pair_valid": True,
                            "pair_label": label,
                            "pair_case_role": role,
                            "intervention_variable": "ignition_source_longitudinal_position_m",
                            "intervention_direction": "70m_vs_130m",
                        }
                    )


def _balanced_subset(samples: list[dict[str, Any]], per_task: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for task in TASKS:
        task_samples = sorted(
            (sample for sample in samples if sample.get("task") == task),
            key=lambda sample: str(sample.get("sample_id")),
        )
        selected.extend(task_samples[:per_task])
    return selected


def build_research_dataset(
    root: Path,
    *,
    seed: int = 20260716,
    deepseek_per_task: int = 2,
) -> dict[str, Any]:
    source_root = root.resolve() / "data" / "raw" / "D01_Immersed-Tunnel-CFD"
    paths: dict[str, Path] = {}
    failures: list[dict[str, str]] = []
    for path in sorted(source_root.rglob("*.csv"), key=lambda item: item.as_posix()):
        try:
            _family(path.stem)
        except ValueError as exc:
            failures.append(
                {
                    "relative_path": path.relative_to(source_root).as_posix(),
                    "reason": str(exc),
                }
            )
            continue
        paths[path.stem.removesuffix("_devc")] = path
    complete_families = sorted(
        family
        for family in {name[2:] if name.startswith("70") else name[3:] for name in paths}
        if all(f"{position}{family}" in paths for position in ("70", "100", "130"))
    )
    partitions = _partition_families(complete_families, seed)
    selected_names = {
        name
        for family in complete_families
        for name in (f"70{family}", f"100{family}", f"130{family}")
    }
    windows: dict[str, list[list[dict[str, Any]]]] = {}
    for name in sorted(selected_names):
        try:
            windows[name] = _window_cases(_sample_case(paths[name], source_root))
        except (OSError, UnicodeError, ValueError) as exc:
            failures.append(
                {
                    "relative_path": paths[name].relative_to(source_root).as_posix(),
                    "reason": str(exc),
                }
            )
    if failures:
        raise ValueError(f"research dataset build has {len(failures)} source failures")

    outputs: dict[str, list[dict[str, Any]]] = {}
    partition_records: dict[str, int] = {}
    for partition, families in partitions.items():
        _mark_pairs(partition, families, windows)
        names = [f"{position}{family}" for family in families for position in ("70", "100", "130")]
        records = [record for name in names for window in windows[name] for record in window]
        split = "train_id" if partition == "train" else "dev_id"
        samples = _build_split(records, split)
        outputs[partition] = samples
        partition_records[partition] = len(records)

    deepseek_samples = _balanced_subset(outputs["dev"], deepseek_per_task)
    family_sets = {key: set(value) for key, value in partitions.items()}
    overlap = any(
        family_sets[left] & family_sets[right]
        for left, right in (("train", "dev"), ("train", "holdout"), ("dev", "holdout"))
    )
    result: dict[str, Any] = {
        "research_version": RESEARCH_VERSION,
        "status": "READY_FOR_PRELIMINARY_RESEARCH",
        "scope": "personal_learning_research_only",
        "source_dataset_ids": ["D01"],
        "source_csv_count": len(paths),
        "complete_family_count": len(complete_families),
        "split": {
            "strategy": "visible_group_first_by_M_or_U_case_number",
            "seed": seed,
            "families": partitions,
            "overlap": overlap,
            "hidden_test": False,
            "ordinary_visible_holdout": True,
        },
        "record_counts": partition_records,
        "sample_counts": {key: len(value) for key, value in outputs.items()},
        "task_counts": {
            partition: {task: sum(sample["task"] == task for sample in samples) for task in TASKS}
            for partition, samples in outputs.items()
        },
        "train_samples": outputs["train"],
        "dev_samples": outputs["dev"],
        "holdout_samples": outputs["holdout"],
        "deepseek_samples": deepseek_samples,
        "deepseek_sample_count": len(deepseek_samples),
        "expert_review_status": "NOT_AVAILABLE_PRELIMINARY_AUTO_LABELS",
        "license_status": "PERSONAL_RESEARCH_ONLY_NOT_CLEARED_FOR_PUBLICATION",
        "formal_benchmark_eligible": False,
        "raw_files_modified": False,
        "test_private_assets_accessed": False,
    }
    hash_input = {key: value for key, value in result.items() if not key.endswith("_samples")}
    hash_input["sample_hashes"] = {
        key: hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        for key, value in outputs.items()
    }
    result["manifest_sha256"] = hashlib.sha256(
        json.dumps(hash_input, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result


def write_research_dataset(
    root: Path,
    output: Path,
    train_output: Path,
    dev_output: Path,
    holdout_output: Path,
    deepseek_output: Path,
    *,
    seed: int,
    deepseek_per_task: int,
) -> dict[str, Any]:
    result = build_research_dataset(root, seed=seed, deepseek_per_task=deepseek_per_task)
    write_json(
        {"samples": result["train_samples"], "research_version": RESEARCH_VERSION},
        train_output,
    )
    write_json({"samples": result["dev_samples"], "research_version": RESEARCH_VERSION}, dev_output)
    write_json(
        {"samples": result["holdout_samples"], "research_version": RESEARCH_VERSION},
        holdout_output,
    )
    write_json(
        {"samples": result["deepseek_samples"], "research_version": RESEARCH_VERSION},
        deepseek_output,
    )
    summary = {key: value for key, value in result.items() if not key.endswith("_samples")}
    write_json(summary, output)
    return result
