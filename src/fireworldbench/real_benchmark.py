"""Construct deterministic, non-formal candidate cases from observed staging formats."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from fireworldbench.pipeline import sha256_file, sha256_bytes, write_json

BUILD_VERSION = "P3-REAL-BENCHMARK-BUILD"
SOURCE_DIRS = {"D01": "D01_Immersed-Tunnel-CFD", "D02": "D02_PolyUFire", "D03": "D03_FDS-exp"}


def _number(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fds_csv(path: Path, root: Path, dataset_id: str) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        units = next(reader, [])
        headers = next(reader, [])
        if not headers or not any(str(value).strip().lower() == "time" for value in headers):
            raise ValueError("expected FDS two-row header with Time column")
        time_index = next(index for index, value in enumerate(headers) if value.strip().lower() == "time")
        field_units = {
            headers[index].strip(): (units[index].strip() if index < len(units) else "UNKNOWN")
            for index in range(len(headers)) if headers[index].strip()
        }
        relative = path.relative_to(root).as_posix()
        case_id = f"{dataset_id}:{relative}"
        fixture: list[dict[str, Any]] = []
        row_count = 0
        numeric_time_count = 0
        time_min: float | None = None
        time_max: float | None = None
        for row_index, row in enumerate(reader, start=3):
            row_count += 1
            raw_time = row[time_index] if time_index < len(row) else ""
            time_value = _number(raw_time)
            if time_value is not None:
                numeric_time_count += 1
                time_min = time_value if time_min is None else min(time_min, time_value)
                time_max = time_value if time_max is None else max(time_max, time_value)
            if len(fixture) < 2:
                values = {
                    headers[index].strip(): _number(value) if _number(value) is not None else value
                    for index, value in enumerate(row) if index < len(headers) and headers[index].strip()
                }
                fixture.append({"row_index": row_index, "case_id": case_id, "sequence_id": case_id, "time": values.get(headers[time_index].strip()), "values": values})
        if row_count == 0 or numeric_time_count == 0:
            raise ValueError("no numeric time rows")
    return {
        "dataset_id": dataset_id,
        "relative_path": relative,
        "sha256": sha256_file(path),
        "case_id": case_id,
        "sequence_id": case_id,
        "format": "FDS_CSV_TWO_ROW_HEADER",
        "fields": list(field_units),
        "units": field_units,
        "row_count": row_count,
        "numeric_time_count": numeric_time_count,
        "time_range": {"min": time_min, "max": time_max, "unit": field_units.get(headers[time_index].strip(), "UNKNOWN")},
        "fixture": fixture,
    }


def _dataset(root: Path, dataset_id: str) -> dict[str, Any]:
    source_root = root / "data" / "raw" / SOURCE_DIRS[dataset_id]
    files = sorted(source_root.rglob("*.csv"), key=lambda path: path.as_posix())
    candidates: list[dict[str, Any]] = []
    blockers: list[dict[str, str]] = []
    for path in files:
        try:
            candidates.append(_fds_csv(path, source_root, dataset_id))
        except (OSError, UnicodeError, ValueError) as exc:
            blockers.append({"relative_path": path.relative_to(source_root).as_posix(), "code": "FORMAT_OR_SEMANTIC_BLOCKED", "reason": str(exc)})
    if dataset_id == "D02":
        spreadsheet_count = sum(1 for path in source_root.rglob("*") if path.is_file() and path.suffix.lower() in {".xls", ".xlsx"})
        blockers.append({"relative_path": ".", "code": "SPREADSHEET_ADAPTER_BLOCKED", "reason": f"{spreadsheet_count} XLS/XLSX files require an approved spreadsheet adapter"})
    return {
        "dataset_id": dataset_id,
        "source_root": source_root.relative_to(root).as_posix(),
        "candidate_case_count": len(candidates),
        "candidate_cases": candidates,
        "blockers": blockers,
        "formal_benchmark_eligible": False,
        "training_eligible": "BLOCKED",
        "development_eligible": "BLOCKED",
        "testing_eligible": "BLOCKED",
        "derived_release_eligible": "BLOCKED",
        "redistribution_eligible": "BLOCKED",
        "license_status": "UNKNOWN",
        "version_status": "UNKNOWN",
    }


def build_candidate_manifest(root: Path) -> dict[str, Any]:
    root = root.resolve()
    datasets = [_dataset(root, dataset_id) for dataset_id in SOURCE_DIRS]
    result: dict[str, Any] = {
        "schema_version": 1,
        "build_version": BUILD_VERSION,
        "status": "CANDIDATE_CASES_BUILT_FORMAL_USE_BLOCKED",
        "scope": "derived planning candidates only; not train/dev/test and no model results",
        "datasets": datasets,
        "candidate_case_count": sum(item["candidate_case_count"] for item in datasets),
        "raw_files_modified": False,
        "test_private_assets_accessed": False,
        "formal_benchmark_eligible": False,
        "next_gate": "source/version/license approval, schema mapping, group split and gold provenance",
    }
    result["manifest_sha256"] = sha256_bytes(json.dumps(result, sort_keys=True, separators=(",", ":")).encode())
    return result


def write_candidate_manifest(root: Path, output: Path) -> dict[str, Any]:
    result = build_candidate_manifest(root)
    write_json(result, output)
    return result
