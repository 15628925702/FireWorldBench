"""Claims-evidence matrix and result freeze guard."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CLAIMS_VERSION = "P5-CLAIMS-FREEZE-001"


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_claims_matrix() -> dict[str, Any]:
    claims = [
        {"claim_id": "C-001", "claim": "The benchmark has auditable schema, split, leakage, scoring, and run contracts.", "status": "SUPPORTED_PROTOCOL", "evidence": ["src/fireworldbench/schema_validation.py", "src/fireworldbench/scorer.py", "configs/test_embargo.toml"]},
        {"claim_id": "C-002", "claim": "The benchmark demonstrates model performance on fire-physics reasoning.", "status": "BLOCKED_NO_RESULTS", "evidence": ["configs/main_run_P5-MAIN-001.json", "configs/stats_P5-STATS-001.json"], "permitted_wording": "No performance result is available.", "forbidden_wording": "Do not report accuracy, ranking, or superiority."},
        {"claim_id": "C-003", "claim": "The benchmark includes newly generated FD-Gen/FDS cases.", "status": "BLOCKED_NO_GENERATED_CASES", "evidence": ["configs/fdgen_P5-FDGEN-001.json", "configs/benchmark_integration_P5-BENCHMARK-INTEGRATE-001.json"], "permitted_wording": "Generation is frozen but not executed.", "forbidden_wording": "Do not claim generated-case coverage."},
        {"claim_id": "C-004", "claim": "The visual baseline measures physical world understanding.", "status": "N_A_NO_APPROVED_VISUAL_RESOURCES", "evidence": ["configs/vision_baseline_P4-BASELINE-VISION.json"], "permitted_wording": "Visual baseline is N/A pending approved resources.", "forbidden_wording": "Do not equate detection accuracy with physical reasoning."},
        {"claim_id": "C-005", "claim": "The evaluation is reproducible from frozen configuration and raw outputs.", "status": "SUPPORTED_CONDITIONALLY", "evidence": ["src/fireworldbench/stats.py", "src/fireworldbench/harness.py", "configs/prereg_P5-PREREG-001.json"], "permitted_wording": "The protocol is designed for reproducible recomputation when raw outputs exist."},
        {"claim_id": "C-006", "claim": "The project has a paper-ready numerical result table.", "status": "REMOVED_NO_FROZEN_RESULTS", "evidence": ["configs/stats_P5-STATS-001.json"], "permitted_wording": "No paper-ready result table is available."},
    ]
    result: dict[str, Any] = {
        "claims_version": CLAIMS_VERSION,
        "status": "FROZEN_WITH_BLOCKED_CLAIMS",
        "claims": claims,
        "result_freeze_manifest": {"run_ids": [], "result_hashes": [], "raw_prediction_hashes": [], "metrics": {}},
        "limitations_and_negative_results": [
            "no_approved_model_or_runtime",
            "no_paper_ready_train_dev_manifest",
            "no_generated_fdgen_cases",
            "no_raw_predictions",
            "visual_baseline_na",
            "expert_annotation_resource_unavailable",
        ],
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }
    result["matrix_sha256"] = _hash(result)
    return result


def validate_claims_matrix(matrix: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for claim in matrix.get("claims", []):
        if not claim.get("status") or not claim.get("evidence"):
            errors.append(f"claim lacks status/evidence: {claim.get('claim_id')}")
    if matrix.get("result_freeze_manifest", {}).get("run_ids"):
        errors.append("result freeze manifest unexpectedly contains run ids")
    if matrix.get("test_asset_read") is not False or matrix.get("test_access_ledger") != "NO_ACCESS_CONFIRMED":
        errors.append("test embargo fields are invalid")
    return errors


def write_claims_matrix(output_path: Path) -> dict[str, Any]:
    result = build_claims_matrix()
    errors = validate_claims_matrix(result)
    if errors:
        raise ValueError(f"invalid claims matrix: {errors}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
