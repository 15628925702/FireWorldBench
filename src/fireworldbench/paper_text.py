"""Guarded manuscript-number registry and source scan."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

TEXT_VERSION = "P6-PAPER-TEXT-001"
NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])(?:\d+(?:\.\d+)?%?|\d+%)")
ALLOWLIST_CATEGORIES = (
    "year",
    "version",
    "page_count",
    "seed",
    "threshold",
    "citation_index",
)


def _scan_manuscript(path: Path) -> tuple[list[dict[str, Any]], str]:
    content = path.read_text(encoding="utf-8")
    source_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    entries: list[dict[str, Any]] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        for match in NUMBER_PATTERN.finditer(line):
            token = match.group(0)
            entries.append(
                {
                    "token": token,
                    "normalized_value": token.rstrip("%"),
                    "unit": "percent" if token.endswith("%") else "unspecified",
                    "source_file": str(path),
                    "line": line_number,
                    "column": match.start() + 1,
                    "classification": "UNMAPPED",
                    "run_id": None,
                    "metric": None,
                    "rounding": None,
                    "provenance": None,
                }
            )
    return entries, source_sha256


def _result_source_has_run_ids(path: Path) -> tuple[bool, str]:
    source = path.read_bytes()
    payload = json.loads(source.decode("utf-8"))
    manifest = payload.get("result_freeze_manifest") if isinstance(payload, Mapping) else None
    run_ids = manifest.get("run_ids") if isinstance(manifest, Mapping) else None
    return bool(run_ids), hashlib.sha256(source).hexdigest()


def assess_text_registry(
    results_path: Path | None = None,
    manuscript_path: Path | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    results_sha256: str | None = None
    manuscript_sha256: str | None = None
    manuscript_scan: list[dict[str, Any]] = []

    if results_path is None:
        blockers.append("frozen_statistics_missing")
    else:
        has_run_ids, results_sha256 = _result_source_has_run_ids(results_path)
        if not has_run_ids:
            blockers.append("result_freeze_manifest_has_no_run_ids")

    if manuscript_path is not None:
        manuscript_scan, manuscript_sha256 = _scan_manuscript(manuscript_path)
        if manuscript_scan:
            blockers.append("unmapped_manuscript_numbers")

    return {
        "text_version": TEXT_VERSION,
        "status": "READY_TO_EXPORT" if not blockers else "BLOCKED_NO_FROZEN_RESULTS",
        "blockers": blockers,
        "source_results_sha256": results_sha256,
        "manuscript_source_sha256": manuscript_sha256,
        "text_number_map_columns": [
            "number_id",
            "value",
            "unit",
            "run_id",
            "metric",
            "rounding",
            "provenance",
        ],
        "text_number_registry": [],
        "manuscript_number_scan": manuscript_scan,
        "non_result_number_allowlist": {
            "categories": list(ALLOWLIST_CATEGORIES),
            "entries": [],
            "provenance_required": True,
        },
        "unmapped_result_numbers": manuscript_scan,
        "run_metric_provenance": [],
        "manual_text_copy": False,
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def write_text_decision(
    output_path: Path,
    results_path: Path | None = None,
    manuscript_path: Path | None = None,
) -> dict[str, Any]:
    result = assess_text_registry(results_path, manuscript_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
