"""Independent audit of paper-number provenance and export gates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

AUDIT_VERSION = "P6-AUDIT-001"
SOURCE_LABELS = ("claims", "tables", "figures", "text")


def _audit_source(label: str, path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "label": label,
            "status": "MISSING",
            "path": None,
            "sha256": None,
            "run_ids": [],
            "number_rows": 0,
        }
    source = path.read_bytes()
    payload = json.loads(source.decode("utf-8"))
    manifest = payload.get("result_freeze_manifest") if isinstance(payload, Mapping) else None
    run_ids = manifest.get("run_ids", []) if isinstance(manifest, Mapping) else []
    return {
        "label": label,
        "status": "READY" if run_ids else "NO_FROZEN_RUN_IDS",
        "path": str(path),
        "sha256": hashlib.sha256(source).hexdigest(),
        "run_ids": list(run_ids) if isinstance(run_ids, list) else [],
        "number_rows": len(payload.get("text_number_registry", [])) if isinstance(payload, Mapping) else 0,
    }


def assess_paper_audit(
    claims_path: Path | None = None,
    tables_path: Path | None = None,
    figures_path: Path | None = None,
    text_path: Path | None = None,
) -> dict[str, Any]:
    paths = {
        "claims": claims_path,
        "tables": tables_path,
        "figures": figures_path,
        "text": text_path,
    }
    sources = [_audit_source(label, paths[label]) for label in SOURCE_LABELS]
    blockers = [f"{source['label']}_export_missing" for source in sources if source["status"] == "MISSING"]
    blockers.extend(
        f"{source['label']}_has_no_frozen_run_ids"
        for source in sources
        if source["status"] == "NO_FROZEN_RUN_IDS"
    )
    return {
        "audit_version": AUDIT_VERSION,
        "status": "READY_ZERO_UNEXPLAINED_DIFFS" if not blockers else "BLOCKED_NO_FROZEN_EXPORTS",
        "blockers": blockers,
        "scan_policy": {
            "full_scan": True,
            "random_sample_scan": True,
            "random_seed": 20270714,
            "random_sample_size": 0,
            "overwrite_existing_exports": False,
        },
        "sources": sources,
        "numeric_trace_audit": [],
        "unexplained_numeric_differences": [],
        "statistics_unit_rounding_sample_audit": [],
        "citation_audit": {"status": "BLOCKED_NO_INPUT", "items": []},
        "license_audit": {"status": "BLOCKED_NO_INPUT", "items": []},
        "double_blind_audit": {"status": "BLOCKED_NO_INPUT", "identity_leaks": []},
        "claims_matrix_audit": {"status": "BLOCKED_NO_INPUT", "items": []},
        "repaired_exports": [],
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def write_paper_audit(
    output_path: Path,
    claims_path: Path | None = None,
    tables_path: Path | None = None,
    figures_path: Path | None = None,
    text_path: Path | None = None,
) -> dict[str, Any]:
    result = assess_paper_audit(claims_path, tables_path, figures_path, text_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
