"""Deterministic train/dev pilot matrix and budget freeze."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PILOT_VERSION = "P4-PILOT-FREEZE-001"
NO_ACCESS_CONFIRMED = "NO_ACCESS_CONFIRMED"


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_pilot_plan() -> dict[str, Any]:
    """Build the frozen plan without reading data or contacting models."""

    plan: dict[str, Any] = {
        "pilot_version": PILOT_VERSION,
        "status": "BLOCKED_PENDING_APPROVAL",
        "blockers": [
            "approved_model_ids",
            "api_or_local_runtime_budget",
            "frozen_train_dev_sample_manifest",
        ],
        "split_policy": {
            "allowed_splits": ["train_id", "dev_id"],
            "forbidden_splits": ["test_id", "test_ood", "external_test"],
            "test_access_ledger": NO_ACCESS_CONFIRMED,
            "test_tuning": False,
        },
        "model_slots": [
            {"slot": "text_table_primary", "track": "text_only_table", "model_id": None, "status": "BLOCKED_UNTIL_APPROVAL"},
            {"slot": "multimodal_exploratory", "track": "multimodal", "model_id": None, "status": "BLOCKED_UNTIL_APPROVAL"},
        ],
        "tracks": [
            {"name": "text_only_table", "information_budget": "text_table_only", "prompt_id": "text_table_v1", "role": "main"},
            {"name": "retrieval", "information_budget": "retrieval_only", "prompt_id": "text_table_v1", "role": "main"},
            {"name": "multimodal", "information_budget": "approved_visual_plus_text", "prompt_id": "multimodal_v1", "role": "exploratory"},
            {"name": "plot", "information_budget": "plot_only", "prompt_id": "text_table_v1", "role": "exploratory"},
            {"name": "formula_fds_proxy", "information_budget": "formula_or_fds_proxy_only", "prompt_id": "text_table_v1", "role": "exploratory"},
            {"name": "tool_use", "information_budget": "declared_tool_use_only", "prompt_id": "text_table_v1", "role": "exploratory"},
        ],
        "sample_counts": {"train_id": None, "dev_id": None},
        "repetitions": {"primary": 1, "exploratory": 1},
        "failure_rules": {
            "invalid_json": "count_as_failure",
            "timeout": "count_as_failure_after_retries",
            "tool_failure": "retain_trace_and_count_as_failure",
            "refusal": "report_separately_and_do_not_repair",
            "budget_exceeded": "stop_track_and_report",
        },
        "budgets": {
            "max_input_tokens_per_sample": 4096,
            "max_output_tokens_per_sample": 512,
            "max_retries": 0,
            "max_wall_time_s": 1800,
            "max_cost_usd": None,
            "cost_status": "BLOCKED_UNTIL_PRICING_APPROVAL",
        },
        "main_matrix": ["text_only_table", "retrieval"],
        "exploratory_matrix": ["multimodal", "plot", "formula_fds_proxy", "tool_use"],
        "selection_rule": "freeze_without_test_performance; no post-freeze model_or_prompt_selection",
        "test_asset_read": False,
    }
    plan["plan_sha256"] = _hash(plan)
    return plan


def validate_pilot_plan(plan: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    split_policy = plan.get("split_policy", {})
    if split_policy.get("test_access_ledger") != NO_ACCESS_CONFIRMED:
        errors.append("test_access_ledger must be NO_ACCESS_CONFIRMED")
    if split_policy.get("test_tuning") is not False:
        errors.append("test_tuning must be false")
    main = set(plan.get("main_matrix", []))
    exploratory = set(plan.get("exploratory_matrix", []))
    if main & exploratory:
        errors.append("main and exploratory matrices must be disjoint")
    if plan.get("test_asset_read") is not False:
        errors.append("test_asset_read must be false")
    if "test" in str(plan.get("selection_rule", "")).lower() and "without_test_performance" not in str(plan.get("selection_rule")):
        errors.append("selection rule must forbid test-performance selection")
    return errors


def write_pilot_plan(output_path: Path, plan: Mapping[str, Any] | None = None) -> dict[str, Any]:
    result = dict(plan or build_pilot_plan())
    errors = validate_pilot_plan(result)
    if errors:
        raise ValueError(f"invalid pilot plan: {errors}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
