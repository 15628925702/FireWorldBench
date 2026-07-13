"""Guarded paper-table export decision."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

TABLES_VERSION = "P6-PAPER-TABLES-001"


def assess_table_export(results_path: Path | None = None) -> dict[str, Any]:
    blockers: list[str] = []
    source_sha256: str | None = None
    if results_path is None:
        blockers.append("frozen_results_missing")
    else:
        source = results_path.read_bytes()
        source_sha256 = __import__("hashlib").sha256(source).hexdigest()
        payload = json.loads(source.decode("utf-8"))
        if not isinstance(payload, Mapping) or not payload.get("result_freeze_manifest", {}).get("run_ids"):
            blockers.append("result_freeze_manifest_has_no_run_ids")
    return {
        "tables_version": TABLES_VERSION,
        "status": "READY_TO_EXPORT" if not blockers else "BLOCKED_NO_FROZEN_RESULTS",
        "blockers": blockers,
        "source_results_sha256": source_sha256,
        "table_spec": {"main": [], "appendix": [], "cell_provenance_required": True},
        "csv_outputs": [],
        "json_outputs": [],
        "latex_outputs": [],
        "run_metric_mapping": [],
        "manual_number_copy": False,
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def write_table_export_decision(output_path: Path, results_path: Path | None = None) -> dict[str, Any]:
    result = assess_table_export(results_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
