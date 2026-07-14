"""Small local train/dev pilot inputs derived from FDS-style staging CSV files."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from fireworldbench.pipeline import sha256_file, write_json
from fireworldbench.t1_builder import build_t1

PILOT_VERSION = "P4-PLANNING-PILOT-001"


def _number(value: str) -> float | str:
    try:
        return float(value)
    except ValueError:
        return value


def _records_from_file(path: Path, root: Path, max_rows: int, *, sample_strategy: str = "uniform") -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        units = next(reader, [])
        headers = next(reader, [])
        time_index = next((index for index, value in enumerate(headers) if value.strip().lower() == "time"), None)
        if time_index is None:
            raise ValueError("FDS planning pilot requires a Time header")
        relative = path.relative_to(root).as_posix()
        case_id = "D01:" + relative
        source_sha = sha256_file(path)
        raw_records: list[dict[str, Any]] = []
        for row_index, row in enumerate(reader, start=3):
            time_value = _number(row[time_index]) if time_index < len(row) else ""
            if not isinstance(time_value, float):
                continue
            variables = {
                headers[index].strip(): _number(value)
                for index, value in enumerate(row)
                if index < len(headers) and headers[index].strip() and index != time_index
            }
            variables.update({"fire_label": "fire_forming", "anomaly_label": "fire"})
            raw_records.append({
                "source_dataset_id": "D01",
                "source_relative_path": relative,
                "source_sha256": source_sha,
                "source_row_index": row_index,
                "case_id": case_id,
                "sequence_id": case_id,
                "time_value_l0": time_value,
                "time_unit_l0": units[time_index].strip() if time_index < len(units) else "s",
                "variables_l0": variables,
                "units_l0": {
                    headers[index].strip(): units[index].strip() if index < len(units) else "UNKNOWN"
                    for index in range(len(headers)) if headers[index].strip() and index != time_index
                },
                "canonical_values": {"time_s": time_value},
                "conversion_trace": {"time": {"rule": "source_s", "status": "PASS"}},
                "status": "PASS",
                "builder_version": PILOT_VERSION,
            })
    if max_rows < 1:
        raise ValueError("rows_per_case must be positive")
    if len(raw_records) <= max_rows:
        return raw_records
    if max_rows == 1:
        return [raw_records[-1]]
    if sample_strategy == "early_mid_late":
        if max_rows != 6:
            raise ValueError("early_mid_late sampling requires six rows")
        middle = len(raw_records) // 2
        indices = [0, 1, middle - 1, middle, len(raw_records) - 2, len(raw_records) - 1]
        return [raw_records[index] for index in indices]
    if sample_strategy != "uniform":
        raise ValueError(f"unknown sample strategy: {sample_strategy}")
    indices = sorted({round(index * (len(raw_records) - 1) / (max_rows - 1)) for index in range(max_rows)})
    return [raw_records[index] for index in indices]


def _prompt_with_measurements(sample: dict[str, Any], records: list[dict[str, Any]]) -> None:
    lines: list[str] = []
    observations = sample["observations"]
    for observation, record in zip(observations, records):
        variables = record["variables_l0"]
        candidate_fields = [key for key in variables if key not in {"fire_label", "anomaly_label"}]
        fields = sorted(
            candidate_fields,
            key=lambda key: (-abs(variables[key]) if isinstance(variables[key], (int, float)) else 0.0, key),
        )[:6]
        values = ", ".join(f"{key}={variables[key]}" for key in fields)
        lines.append(f"{observation['observation_id']}: t={record['canonical_values']['time_s']} s; {values}")
    sample["question"]["prompt"] += "\nVisible measurement rows:\n" + "\n".join(lines)


def build_planning_t1_pilot(root: Path, *, max_cases: int = 2, rows_per_case: int = 6) -> dict[str, Any]:
    root = root.resolve()
    source_root = root / "data" / "raw" / "D01_Immersed-Tunnel-CFD"
    files = sorted(source_root.rglob("*.csv"), key=lambda path: path.as_posix())[:max_cases]
    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    per_case: dict[str, list[dict[str, Any]]] = {}
    for path in files:
        try:
            case_records = _records_from_file(path, source_root, rows_per_case)
            if not case_records:
                raise ValueError("no usable numeric rows")
            records.extend(case_records)
            per_case[case_records[0]["case_id"]] = case_records
        except (OSError, UnicodeError, ValueError) as exc:
            failures.append({"relative_path": path.relative_to(source_root).as_posix(), "reason": str(exc)})
    parent_manifest_sha256 = hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    result = build_t1(records, split="dev_id", benchmark_version="planning-pilot", parent_manifest_sha256=parent_manifest_sha256)
    result["samples"] = [sample for sample in result["samples"] if sample["task"] in {"T1-A", "T1-B"}]
    result["sample_count"] = len(result["samples"])
    for sample in result["samples"]:
        case_id = sample["physical_trace"]["initial_state"]["case_id"]
        _prompt_with_measurements(sample, per_case[case_id])
    result.update({
        "pilot_version": PILOT_VERSION,
        "source_scope": "D01 local planning staging only",
        "planning_mode": True,
        "formal_benchmark_eligible": False,
        "test_samples_generated": False,
        "raw_files_modified": False,
        "source_failures": failures,
        "record_count": len(records),
        "pilot_tasks": ["T1-A", "T1-B"],
        "excluded_tasks": {"T1-C": "requires an interactive next-observation interface, not a full-context prompt"},
    })
    result["manifest_sha256"] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return result


def write_planning_t1_pilot(root: Path, output: Path, max_cases: int, rows_per_case: int) -> dict[str, Any]:
    result = build_planning_t1_pilot(root, max_cases=max_cases, rows_per_case=rows_per_case)
    write_json(result, output)
    return result
