"""Preregistered evaluation plan with test embargo enforcement."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PREREG_VERSION = "P5-PREREG-001"
NO_ACCESS_CONFIRMED = "NO_ACCESS_CONFIRMED"


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_preregistration() -> dict[str, Any]:
    plan: dict[str, Any] = {
        "prereg_version": PREREG_VERSION,
        "status": "BLOCKED_PENDING_APPROVAL",
        "hypotheses": {
            "H1": "text_table_only supports fire-state reasoning when evidence is sufficient and does not replace missing observations",
            "H2": "retrieval changes answers only when the frozen knowledge base supplies relevant approved information",
            "H3": "physical-violation reporting remains separately measurable from task-label accuracy",
        },
        "primary_metrics": {
            "T1-A": "auprc",
            "T1-B": "macro_f1",
            "T1-C": "budgeted_decision_utility",
            "T2-A": "hierarchical_macro_f1",
            "T2-B": "mechanism_macro_f1",
            "T2-C": "macro_f1_after_calibration_protocol",
            "T3-A": "trend_direction_macro_accuracy",
            "T3-B": "pair_ranking_accuracy",
            "T3-C": "state_trace_score",
        },
        "secondary_metrics": [
            "case_level_accuracy",
            "pair_validity_rate",
            "physical_violation_rate",
            "refusal_rate",
            "invalid_json_rate",
            "latency",
            "cost",
        ],
        "statistical_families": {
            "analysis_unit": "case_or_counterfactual_pair",
            "confidence_level": 0.95,
            "bootstrap_replicates": 10000,
            "paired_case_level": True,
            "multiple_comparison": "report_each_task_family; no unregistered composite score",
        },
        "model_matrix": [
            {"slot": "text_table_primary", "track": "text_only_table", "model_id": None, "status": "BLOCKED_UNTIL_APPROVAL"},
            {"slot": "retrieval_primary", "track": "retrieval", "model_id": None, "status": "BLOCKED_UNTIL_APPROVAL"},
            {"slot": "multimodal_exploratory", "track": "multimodal", "model_id": None, "status": "BLOCKED_UNTIL_APPROVAL"},
            {"slot": "tool_exploratory", "track": "tool_use", "model_id": None, "status": "BLOCKED_UNTIL_APPROVAL"},
        ],
        "main_matrix": ["text_only_table", "retrieval"],
        "exploratory_matrix": ["multimodal", "plot", "formula_fds_proxy", "tool_use"],
        "ablations": [
            {"name": "information_budget", "changed_factor": "track", "one_factor_at_a_time": True},
            {"name": "evidence_ablation", "changed_factor": "evidence_visibility", "one_factor_at_a_time": True},
            {"name": "uncertainty_ablation", "changed_factor": "uncertainty_reporting", "one_factor_at_a_time": True},
        ],
        "repetitions": {"main": 1, "exploratory": 1, "random_seed_policy": "frozen_config_seed_only"},
        "exclusions": [
            "test_performance_model_selection",
            "manual_answer_repair",
            "success_only_case_selection",
            "unregistered_composite_score",
            "mixing_information_budgets",
        ],
        "stopping_rules": {
            "stop_on_budget_exceeded": True,
            "stop_on_missing_approval": True,
            "no_mid_run_prompt_change": True,
            "failed_runs_retained": True,
        },
        "test_access": {
            "ledger": NO_ACCESS_CONFIRMED,
            "test_input_read": False,
            "test_gold_read": False,
            "private_mapping_read": False,
            "custodian_required_for_future_test_scoring": True,
        },
        "post_freeze_change_policy": "new_version_and_exploratory_label_required",
        "selection_rule": "freeze_without_test_performance; no post-freeze model_or_prompt selection",
    }
    plan["plan_sha256"] = _hash(plan)
    return plan


def validate_preregistration(plan: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    access = plan.get("test_access", {})
    if access.get("ledger") != NO_ACCESS_CONFIRMED:
        errors.append("test access ledger must be NO_ACCESS_CONFIRMED")
    for key in ("test_input_read", "test_gold_read", "private_mapping_read"):
        if access.get(key) is not False:
            errors.append(f"{key} must be false")
    if set(plan.get("main_matrix", [])) & set(plan.get("exploratory_matrix", [])):
        errors.append("main and exploratory matrices must be disjoint")
    if "without_test_performance" not in str(plan.get("selection_rule", "")):
        errors.append("selection rule must forbid test performance")
    if not plan.get("primary_metrics"):
        errors.append("primary metrics must be frozen")
    return errors


def write_preregistration(output_path: Path) -> dict[str, Any]:
    result = build_preregistration()
    errors = validate_preregistration(result)
    if errors:
        raise ValueError(f"invalid preregistration: {errors}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
