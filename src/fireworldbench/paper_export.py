"""Guarded public/private paper-export package decision."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

EXPORT_VERSION = "P6-EXPORT-001"
PUBLIC_ROOT = "paper_exports_public/<release_id>/"
PRIVATE_ROOT = "paper_exports_private/<release_id>/"
EXPECTED_PUBLIC_PATHS = (
    "README.md",
    "manifest.json",
    "checksums.sha256",
    "provenance/run_index.csv",
    "provenance/table_cell_map.csv",
    "provenance/figure_point_map.csv",
    "provenance/text_number_map.csv",
    "provenance/claims_evidence.csv",
    "provenance/versions.json",
    "statistics/aggregate_metrics.json",
    "statistics/confidence_intervals.csv",
    "statistics/tests_and_effects.csv",
    "statistics/failures_and_costs.csv",
    "analysis/limitations.md",
    "environment/code_version.json",
    "environment/data_manifest_refs.json",
    "environment/resolved_configs/",
)
EXPECTED_PRIVATE_PATHS = (
    "README.md",
    "manifest.json",
    "checksums.sha256",
    "private/test_label_refs.json",
    "private/restricted_run_refs.json",
)


def _source_info(results_path: Path | None) -> tuple[str | None, bool]:
    if results_path is None:
        return None, False
    source = results_path.read_bytes()
    payload = json.loads(source.decode("utf-8"))
    manifest = payload.get("result_freeze_manifest") if isinstance(payload, Mapping) else None
    run_ids = manifest.get("run_ids", []) if isinstance(manifest, Mapping) else []
    return hashlib.sha256(source).hexdigest(), bool(run_ids)


def assess_paper_export(results_path: Path | None = None) -> dict[str, Any]:
    source_sha256, has_run_ids = _source_info(results_path)
    blockers: list[str] = []
    if results_path is None:
        blockers.append("frozen_results_missing")
    elif not has_run_ids:
        blockers.append("result_freeze_manifest_has_no_run_ids")
    return {
        "export_version": EXPORT_VERSION,
        "status": "READY_TO_PACKAGE" if not blockers else "BLOCKED_NO_FROZEN_RESULTS",
        "blockers": blockers,
        "release_id": None,
        "source_results_sha256": source_sha256,
        "generated": False,
        "public_root": None,
        "private_root": None,
        "public_private_separate": True,
        "expected_public_paths": list(EXPECTED_PUBLIC_PATHS),
        "expected_private_paths": list(EXPECTED_PRIVATE_PATHS),
        "manifest_policy": {
            "manifest_self_hash_excluded": True,
            "checksums_cover_manifest": True,
            "checksums_cover_all_other_files": True,
        },
        "public_leak_scan": {
            "status": "BLOCKED_NO_INPUT",
            "private_roots": False,
            "test_gold": False,
            "identity": False,
            "restricted_refs": False,
            "secrets": False,
            "absolute_paths": False,
        },
        "reconstruction": {
            "status": "BLOCKED_NO_INPUT",
            "output_root": None,
            "reconstructed_items": [],
            "hash_or_value_differences": [],
        },
        "claims_table_figure_text_complete": False,
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def write_paper_export_decision(output_path: Path, results_path: Path | None = None) -> dict[str, Any]:
    result = assess_paper_export(results_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
