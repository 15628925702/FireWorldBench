"""Guarded paper-figure source and rendering decision."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

FIGURES_VERSION = "P6-PAPER-FIGURES-001"


def assess_figure_export(results_path: Path | None = None) -> dict[str, Any]:
    blockers: list[str] = []
    source_sha256: str | None = None
    if results_path is None:
        blockers.append("frozen_figure_source_missing")
    else:
        source = results_path.read_bytes()
        source_sha256 = hashlib.sha256(source).hexdigest()
        payload = json.loads(source.decode("utf-8"))
        if not isinstance(payload, Mapping) or not payload.get("result_freeze_manifest", {}).get("run_ids"):
            blockers.append("figure_source_has_no_run_ids")
    return {
        "figures_version": FIGURES_VERSION,
        "status": "READY_TO_RENDER" if not blockers else "BLOCKED_NO_FIGURE_SOURCE",
        "blockers": blockers,
        "source_data_sha256": source_sha256,
        "figure_data": [],
        "plot_specs": [],
        "scripts": [],
        "styles": {"vector_required": True, "minimum_raster_dpi": 300, "manual_points": False},
        "rendered_pdf": [],
        "rendered_png": [],
        "caption_facts": [],
        "table_source_alignment_required": True,
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def write_figure_decision(output_path: Path, results_path: Path | None = None) -> dict[str, Any]:
    result = assess_figure_export(results_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
