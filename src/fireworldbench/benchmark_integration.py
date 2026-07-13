"""Guarded integration decision for generated benchmark addenda."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

INTEGRATION_VERSION = "P5-BENCHMARK-INTEGRATE-001"
REQUIRED_CHAIN = [
    "canonical_adapter",
    "sample_builders",
    "group_split",
    "leak_audit",
    "gold_trace",
    "schema_validation",
    "reference_scorer",
]


def assess_integration(fdgen_decision: Mapping[str, Any]) -> dict[str, Any]:
    generated_count = fdgen_decision.get("generated_count", 0)
    manifest = fdgen_decision.get("generation_manifest", [])
    blockers: list[str] = []
    if fdgen_decision.get("status") != "READY_TO_GENERATE":
        blockers.append("fdgen_decision_not_ready")
    if not isinstance(generated_count, int) or generated_count <= 0:
        blockers.append("no_generated_cases")
    if not isinstance(manifest, list) or len(manifest) != generated_count:
        blockers.append("generated_manifest_missing_or_inconsistent")
    status = "READY_TO_INTEGRATE" if not blockers else "BLOCKED_NO_INPUT"
    return {
        "integration_version": INTEGRATION_VERSION,
        "status": status,
        "blockers": blockers,
        "input_case_count": generated_count if isinstance(generated_count, int) else 0,
        "input_manifest": manifest if status == "READY_TO_INTEGRATE" else [],
        "required_chain": REQUIRED_CHAIN,
        "canonical_manifest": None,
        "sample_manifest": None,
        "split_report": None,
        "leak_report": None,
        "gold_trace_report": None,
        "schema_report": None,
        "scorer_report": None,
        "integration_written": False,
        "existing_p3_p4_artifacts_modified": False,
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def write_integration_decision(fdgen_path: Path, output_path: Path) -> dict[str, Any]:
    fdgen_decision = json.loads(fdgen_path.read_text(encoding="utf-8"))
    if not isinstance(fdgen_decision, Mapping):
        raise TypeError("FD-Gen decision must be a JSON object")
    result = assess_integration(fdgen_decision)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
