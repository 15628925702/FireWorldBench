"""Deterministic, read-only source inventory and canonical case pipeline."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping
from xml.etree import ElementTree

PIPELINE_VERSION = "P3-PIPELINE-001"
SUPPORTED_SUFFIXES = {".csv", ".json", ".jsonl", ".xlsx"}
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


def _xlsx_column_index(reference: str) -> int:
    letters = re.match(r"[A-Za-z]+", reference or "")
    if not letters:
        return 0
    index = 0
    for char in letters.group(0).upper():
        index = index * 26 + ord(char) - ord("A") + 1
    return index - 1


def _read_xlsx_records(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    """Read simple tabular XLSX sheets with stdlib XML support only."""
    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("main:si", namespace):
                shared.append("".join(item.itertext()))
        sheets = sorted(
            name for name in archive.namelist()
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        )
        for sheet_name in sheets:
            root = ElementTree.fromstring(archive.read(sheet_name))
            sheet_rows: list[list[str]] = []
            for row in root.findall(".//main:sheetData/main:row", namespace):
                cells: dict[int, str] = {}
                for cell in row.findall("main:c", namespace):
                    column = _xlsx_column_index(cell.attrib.get("r", ""))
                    value = cell.find("main:v", namespace)
                    inline = cell.find("main:is", namespace)
                    text = "" if value is None else (value.text or "")
                    if cell.attrib.get("t") == "s" and text.isdigit():
                        text = shared[int(text)] if int(text) < len(shared) else ""
                    elif inline is not None:
                        text = "".join(inline.itertext())
                    cells[column] = text
                if cells:
                    width = max(cells) + 1
                    sheet_rows.append([cells.get(index, "") for index in range(width)])
            if not sheet_rows:
                continue
            header_index = next((index for index, row in enumerate(sheet_rows) if any(row)), None)
            if header_index is None:
                continue
            headers = [value.strip() or f"column_{index + 1}" for index, value in enumerate(sheet_rows[header_index])]
            for row_number, data_row in enumerate(sheet_rows[header_index + 1:], start=header_index + 2):
                if any(value.strip() for value in data_row):
                    yield row_number, dict(zip(headers, data_row))


def _read_csv_records(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        first = next(reader, [])
        second = next(reader, [])
        if any(value.strip().lower() == "time" for value in second):
            headers = second
            first_data_row = 3
        else:
            headers = first
            first_data_row = 2
            if second and any(value.strip() for value in second):
                yield first_data_row, dict(zip(headers, second))
                first_data_row += 1
        for row_index, row in enumerate(reader, start=first_data_row):
            yield row_index, dict(zip(headers, row))


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
        yield from _read_csv_records(path)
        return
    if suffix == ".xlsx":
        yield from _read_xlsx_records(path)
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
    case_id = _first(row, "case_id", "case", "scenario_id", "scenario")
    if case_id is None:
        raise ValueError("missing case_id")
    time_value = _first(row, "time_value_l0", "time_s", "time", "RecordTime", "record_time")
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
                    if path.suffix.lower() in {".csv", ".xlsx"} and _first(
                        row, "case_id", "case", "scenario_id", "scenario"
                    ) is None:
                        row = dict(row)
                        row["case_id"] = f"{source_dataset_id}:{item['relative_path']}"
                    if path.suffix.lower() in {".csv", ".xlsx"} and _first(row, "sequence_id") is None:
                        row = dict(row)
                        row["sequence_id"] = row["case_id"]
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
