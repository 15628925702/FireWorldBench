"""Deterministic, read-only source inventory and canonical case pipeline."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

PIPELINE_VERSION = "P3-PIPELINE-001"
SUPPORTED_SUFFIXES = {".csv", ".json", ".jsonl"}
PROTECTED_PATH_PARTS = {"test_gold", "private_id_mapping", "private_scoring_metadata", "restricted_test_inputs"}
TIME_TO_SECONDS = {"s": 1.0, "sec": 1.0, "ms": 0.001, "min": 60.0}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def inventory(root: Path) -> dict[str, Any]:
    """Inventory files without modifying or loading their content."""
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"inventory root is not a directory: {root}")
    private_root = os.environ.get("FIREWORLDBENCH_PRIVATE_ROOT")
    if private_root and root == Path(private_root).resolve():
        raise PermissionError("test embargo forbids ordinary pipeline access to private root")
    if any(part.lower() in PROTECTED_PATH_PARTS for part in root.parts):
        raise PermissionError("test embargo forbids pipeline access to protected asset path")
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file() or path.is_symlink():
            continue
        files.append(
            {
                "relative_path": _relative(path, root),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "suffix": path.suffix.lower(),
                "readable_by_adapter": path.suffix.lower() in SUPPORTED_SUFFIXES,
            }
        )
    return {
        "pipeline_version": PIPELINE_VERSION,
        "root_label": root.name or root.anchor,
        "file_count": len(files),
        "files": files,
    }


def _as_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _read_records(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        with path.open(encoding="utf-8", newline="") as handle:
            for index, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("JSONL row must be an object")
                yield index, value
        return
    if suffix == ".json":
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
        if isinstance(value, dict):
            yield 1, value
        elif isinstance(value, list):
            for index, row in enumerate(value, start=1):
                if not isinstance(row, dict):
                    raise ValueError("JSON array row must be an object")
                yield index, row
        else:
            raise ValueError("JSON input must be an object or array")
        return
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for index, row in enumerate(csv.DictReader(handle), start=2):
                yield index, dict(row)
        return
    raise ValueError(f"unsupported adapter suffix: {suffix or '<none>'}")


def _first(row: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


def _variables(row: Mapping[str, Any]) -> dict[str, Any]:
    explicit = row.get("variables_l0")
    if isinstance(explicit, Mapping):
        return dict(explicit)
    ignored = {
        "source_dataset_id", "source_relative_path", "case_id", "sequence_id",
        "time", "time_s", "time_value_l0", "time_unit", "time_unit_l0", "units",
    }
    return {str(key): value for key, value in row.items() if key not in ignored}


def adapt_row(
    row: Mapping[str, Any], *, source_dataset_id: str, source_relative_path: str,
    source_sha256: str, source_row_index: int,
) -> dict[str, Any]:
    """Map common CSV/JSON keys into the explicit L0 contract."""
    case_id = _first(row, "case_id", "case", "scenario_id")
    if case_id is None:
        raise ValueError("missing case_id")
    time_value = _first(row, "time_value_l0", "time_s", "time")
    time_unit = _first(row, "time_unit_l0", "time_unit", "unit_time") or "UNKNOWN"
    units = row.get("units", {})
    if not isinstance(units, Mapping):
        units = {}
    return {
        "source_dataset_id": source_dataset_id,
        "source_relative_path": source_relative_path,
        "source_sha256": source_sha256,
        "source_row_index": source_row_index,
        "case_id": str(case_id),
        "sequence_id": str(_first(row, "sequence_id") or case_id),
        "time_value_l0": time_value,
        "time_unit_l0": str(time_unit),
        "variables_l0": _variables(row),
        "units_l0": {str(key): str(value) for key, value in units.items()},
    }


def normalize_record(record: Mapping[str, Any], *, builder_version: str = PIPELINE_VERSION) -> dict[str, Any]:
    """Normalize only reversible, explicitly supported units."""
    raw_time = record.get("time_value_l0")
    unit = str(record.get("time_unit_l0") or "UNKNOWN").strip().lower()
    number = _as_float(raw_time)
    canonical_values: dict[str, float | None] = {}
    conversion_trace: dict[str, Any] = {"time": {"rule": "identity", "status": "PASS"}}
    status = "PASS"
    if number is None:
        status = "MISSING_TIME"
        conversion_trace["time"] = {"rule": "none", "status": "BLOCKED", "reason": "non_numeric_or_missing"}
    elif unit in TIME_TO_SECONDS:
        factor = TIME_TO_SECONDS[unit]
        canonical_values["time_s"] = number * factor
        conversion_trace["time"] = {"rule": f"{unit}_to_s", "factor": factor, "status": "PASS"}
    else:
        status = "UNKNOWN_UNIT"
        conversion_trace["time"] = {"rule": "unit_unknown", "status": "BLOCKED", "unit": unit}

    for name, value in dict(record.get("variables_l0", {})).items():
        numeric = _as_float(value)
        if numeric is not None and str(record.get("units_l0", {}).get(name, "UNKNOWN")).upper() != "UNKNOWN":
            canonical_values[str(name)] = numeric
        elif value not in (None, ""):
            canonical_values[str(name)] = None

    output = dict(record)
    output.update({"canonical_values": canonical_values, "conversion_trace": conversion_trace, "status": status})
    output["builder_version"] = builder_version
    return output


def _error(path: str, row: int | None, code: str, message: str) -> dict[str, Any]:
    return {"source_relative_path": path, "source_row_index": row, "code": code, "message": message}


def build_canonical(
    source_root: Path, *, source_dataset_id: str = "UNKNOWN", builder_version: str = PIPELINE_VERSION,
) -> dict[str, Any]:
    """Build deterministic records and a case/sequence graph from supported files."""
    root = source_root.resolve()
    inv = inventory(root)
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for item in inv["files"]:
        path = root / item["relative_path"]
        if not item["readable_by_adapter"]:
            failures.append(_error(item["relative_path"], None, "UNSUPPORTED_SUFFIX", "no safe adapter"))
            continue
        try:
            rows = _read_records(path)
            for row_number, row in rows:
                try:
                    adapted = adapt_row(
                        row, source_dataset_id=source_dataset_id,
                        source_relative_path=item["relative_path"],
                        source_sha256=item["sha256"], source_row_index=row_number,
                    )
                    records.append(normalize_record(adapted, builder_version=builder_version))
                except (TypeError, ValueError, KeyError) as exc:
                    failures.append(_error(item["relative_path"], row_number, "ROW_INVALID", str(exc)))
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            failures.append(_error(item["relative_path"], None, "FILE_INVALID", str(exc)))

    records.sort(key=lambda row: (row["case_id"], row["sequence_id"], row["source_relative_path"], row["source_row_index"]))
    cases: dict[str, dict[str, Any]] = defaultdict(lambda: {"case_id": "", "sequences": {}})
    for record_index, record in enumerate(records):
        case = cases[record["case_id"]]
        case["case_id"] = record["case_id"]
        sequence = case["sequences"].setdefault(record["sequence_id"], {"sequence_id": record["sequence_id"], "record_indices": []})
        sequence["record_indices"].append(record_index)
    graph_cases = []
    for case_id in sorted(cases):
        case = cases[case_id]
        graph_cases.append({"case_id": case_id, "sequences": [case["sequences"][key] for key in sorted(case["sequences"])]})
    config = {"pipeline_version": PIPELINE_VERSION, "source_dataset_id": source_dataset_id, "builder_version": builder_version}
    config_sha256 = sha256_bytes(json.dumps(config, sort_keys=True, separators=(",", ":")).encode())
    for record in records:
        record["config_sha256"] = config_sha256
    manifest = {
        "pipeline_version": PIPELINE_VERSION,
        "source_dataset_id": source_dataset_id,
        "inventory": inv,
        "record_count": len(records),
        "case_count": len(graph_cases),
        "failure_count": len(failures),
        "quality": {
            "pass_records": sum(record["status"] == "PASS" for record in records),
            "blocked_records": sum(record["status"] != "PASS" for record in records),
            "failed_rows": len(failures),
        },
        "records": records,
        "case_graph": {"nodes": graph_cases, "edges": [{"from": case["case_id"], "to": seq["sequence_id"], "type": "contains"} for case in graph_cases for seq in case["sequences"]]},
        "failures": failures,
        "config": config,
        "config_sha256": config_sha256,
    }
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    manifest["manifest_sha256"] = sha256_bytes(encoded)
    return manifest


def write_json(value: Mapping[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
