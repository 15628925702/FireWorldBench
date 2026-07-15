"""Read-only assessment of planning-stage dataset integration."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from fireworldbench.pipeline import SUPPORTED_SUFFIXES, _read_records, build_canonical, inventory, sha256_bytes, write_json

STAGING_VERSION = "P3-PIPELINE-STAGING-INTEGRATION"
STAGED_DATASETS = ("D01", "D02", "D03", "D04", "D05", "D10")
DATASET_DIRS = {
    "D01": "D01_Immersed-Tunnel-CFD",
    "D02": "D02_PolyUFire",
    "D03": "D03_FDS-exp",
    "D04": "D04_FD-Gen",
    "D05": "D05_D-Fire",
    "D10": "D10_FIgLib-SmokeyNet",
}
ROLES = {
    "D01": "T1/T2 primary planning data; T3 pair prototype only",
    "D02": "external experimental validation and mechanism knowledge",
    "D03": "external validation and physics sanity check",
    "D04": "T3/OOD generator preparation only",
    "D05": "visual auxiliary only",
    "D10": "wildfire visual OOD auxiliary only",
}


def _candidate_keys(rows: list[dict[str, Any]]) -> list[str]:
    keys = {str(key) for row in rows for key in row}
    return sorted(key for key in keys if key.lower() in {
        "case", "case_id", "scenario", "scenario_id", "sequence", "sequence_id",
        "time", "time_s", "time_value_l0", "unit_time", "time_unit", "units",
    } or key.lower().startswith(("time", "case", "scenario", "sequence")))


def _csv_probe(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))[:3]
    if not rows:
        return {"header_row": None, "fields": [], "candidate_keys": [], "sample_row_count": 0}
    header_index = 0
    if len(rows) > 1 and any(value.strip().lower() == "time" for value in rows[1]):
        header_index = 1
    fields = [value.strip() for value in rows[header_index]]
    sample = [dict(zip(fields, row)) for row in rows[header_index + 1:] if fields]
    return {
        "header_row": header_index + 1,
        "fields": fields[:100],
        "candidate_keys": _candidate_keys(sample + [{field: None for field in fields}]),
        "sample_row_count": len(sample),
        "unit_row_detected": header_index == 1,
    }


def _structured_probe(root: Path, files: list[dict[str, Any]]) -> dict[str, Any]:
    probes: list[dict[str, Any]] = []
    candidate_keys: set[str] = set()
    for item in files:
        if item["suffix"] not in SUPPORTED_SUFFIXES:
            continue
        path = root / item["relative_path"]
        try:
            if item["suffix"] == ".csv":
                probe = _csv_probe(path)
            elif item["suffix"] == ".xlsx":
                xlsx_rows = [row for _, row in _read_records(path)][:2]
                probe = {
                    "fields": sorted({str(key) for row in xlsx_rows for key in row}),
                    "sample_row_count": len(xlsx_rows),
                    "adapter": "stdlib_xlsx",
                }
            elif item["suffix"] == ".xls":
                xls_rows = [row for _, row in _read_records(path)][:2]
                probe = {
                    "fields": sorted({str(key) for row in xls_rows for key in row}),
                    "sample_row_count": len(xls_rows),
                    "adapter": "xlrd_existing_runtime",
                }
            else:
                rows: list[dict[str, Any]] = []
                if item["suffix"] == ".jsonl":
                    with path.open(encoding="utf-8") as handle:
                        for line in handle:
                            if line.strip():
                                value = json.loads(line)
                                if isinstance(value, dict):
                                    rows.append(value)
                                if len(rows) >= 2:
                                    break
                else:
                    value = json.loads(path.read_text(encoding="utf-8"))
                    rows = value if isinstance(value, list) else [value] if isinstance(value, dict) else []
                probe = {"fields": sorted({str(key) for row in rows[:2] for key in row}), "sample_row_count": len(rows[:2])}
                probe["candidate_keys"] = _candidate_keys(rows[:2])
            candidate_keys.update(probe.get("candidate_keys", []))
            if len(probes) < 20:
                probes.append({"relative_path": item["relative_path"], **probe})
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            probes.append({"relative_path": item["relative_path"], "probe_status": "BLOCKED", "reason": str(exc)})
    return {"file_probes": probes, "candidate_keys": sorted(candidate_keys)}


def _blocker(dataset_id: str, suffix_counts: Counter[str], canonical: dict[str, Any]) -> tuple[str, str]:
    if dataset_id in {"D05", "D10"}:
        return "AUX_ONLY_BLOCKED", "visual auxiliary labels do not expose canonical case/time records"
    if dataset_id == "D02":
        if canonical["record_count"] == 0:
            return "UNSUPPORTED_FORMAT_BLOCKED", "no tabular records were readable from the spreadsheet staging"
        if ".xls" in suffix_counts and canonical["record_count"]:
            return "PLANNING_ADAPTER_READY", "XLS and XLSX records entered the canonical planning chain"
        return "PLANNING_ADAPTER_READY", "XLSX records entered the canonical planning chain"
    if dataset_id == "D04":
        return "GENERATOR_RUNTIME_BLOCKED", "generator assets are not executable during staging integration"
    if dataset_id in {"D01", "D03"} and canonical["record_count"]:
        return "PLANNING_ADAPTER_READY", "tabular records entered the canonical planning chain"
    return "SEMANTIC_SCHEMA_BLOCKED", (
        f"canonical probe produced {canonical['record_count']} records and "
        f"{canonical['failure_count']} failures; case/time semantics require an explicit adapter"
    )


def assess_staging(root: Path) -> dict[str, Any]:
    root = root.resolve()
    datasets: list[dict[str, Any]] = []
    for dataset_id in STAGED_DATASETS:
        source_root = root / "data" / "raw" / DATASET_DIRS[dataset_id]
        inv = inventory(source_root)
        suffix_counts = Counter(item["suffix"] or "<none>" for item in inv["files"])
        structured = _structured_probe(source_root, inv["files"])
        canonical = build_canonical(source_root, source_dataset_id=dataset_id)
        reason_code, reason = _blocker(dataset_id, suffix_counts, canonical)
        datasets.append({
            "dataset_id": dataset_id,
            "staging_root": source_root.relative_to(root).as_posix(),
            "role": ROLES[dataset_id],
            "inventory": {
                "file_count": inv["file_count"],
                "suffix_counts": dict(sorted(suffix_counts.items())),
                "manifest_sha256": sha256_bytes(json.dumps(inv, sort_keys=True, separators=(",", ":")).encode()),
            },
            "format_probe": structured,
            "canonical_probe": {
                "record_count": canonical["record_count"],
                "case_count": canonical["case_count"],
                "failure_count": canonical["failure_count"],
                "quality": canonical["quality"],
                "failure_codes": dict(Counter(item["code"] for item in canonical["failures"])),
            },
            "status": reason_code,
            "blocker": reason,
            "formal_benchmark_eligible": False,
            "local_planning_eligible": True,
            "training_eligible": "LOCAL_PLANNING_ALLOWED",
            "development_eligible": "LOCAL_PLANNING_ALLOWED",
            "testing_eligible": "BLOCKED",
            "derived_release_eligible": "BLOCKED",
            "redistribution_eligible": "BLOCKED",
            "license_status": "NOT_CHECKED_PLANNING_MODE",
            "raw_files_modified": False,
        })
    result = {
        "schema_version": 1,
        "assessment_version": STAGING_VERSION,
        "status": "BLOCKED_STAGING_INTEGRATION",
        "scope": "planning-stage read-only staging only; no formal benchmark or model run",
        "datasets": datasets,
        "raw_files_modified": False,
        "test_private_assets_accessed": False,
        "formal_benchmark_eligible": False,
        "local_planning_mode": True,
    }
    result["assessment_sha256"] = sha256_bytes(json.dumps(result, sort_keys=True, separators=(",", ":")).encode())
    return result


def write_staging_assessment(root: Path, output: Path) -> dict[str, Any]:
    result = assess_staging(root)
    write_json(result, output)
    return result
