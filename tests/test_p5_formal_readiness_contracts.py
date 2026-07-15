from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fireworldbench.formal_readiness import (
    READY_STATUS,
    REQUIRED_TASKS,
    assess_formal_readiness,
    build_formal_input_audit,
)
from fireworldbench import formal_readiness


def _write(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_formal_input_audit_records_hashes_and_missing_d01_files(tmp_path: Path) -> None:
    data_sources = _write(
        tmp_path / "sources.toml",
        """
[[sources]]
id = "D01"
name = "D01"
staging_dir = "data/raw/D01"
eligible = false
license_status = "blocked_missing_evidence"
version_status = "blocked_missing_version"
""".strip(),
    )
    _write(tmp_path / "data/raw/D01/CFD-Data/a.csv", "a,b\n1,2\n")
    assessment = _write(
        tmp_path / "assessment.json",
        {
            "datasets": [
                {
                    "dataset_id": "D01",
                    "status": "PLANNING_ADAPTER_READY",
                    "canonical_probe": {"record_count": 1, "case_count": 1},
                }
            ]
        },
    )
    tree = _write(
        tmp_path / "tree.json",
        {
            "tree": [
                {"path": "CFD-Data/a.csv", "size": 8, "sha": "blob-a"},
                {"path": "CFD-Data/b.csv", "size": 9, "sha": "blob-b"},
            ]
        },
    )

    result = build_formal_input_audit(
        data_sources,
        assessment,
        tree,
        repository_root=tmp_path,
    )

    d01 = result["datasets"][0]
    assert d01["files"][0]["relative_path"] == "CFD-Data/a.csv"
    assert len(d01["files"][0]["sha256"]) == 64
    assert d01["official_inventory"]["local_csv_count"] == 1
    assert d01["official_inventory"]["missing_csv_count"] == 1
    assert result["status"] == "BLOCKED_NO_PAPER_READY_FORMAL_INPUTS"
    assert result["planning_inputs_promoted_to_formal"] is False


def test_formal_preflight_requires_evidence_not_status_labels(tmp_path: Path) -> None:
    paths = [
        _write(tmp_path / "data.json", {"status": "FROZEN_FORMAL_INPUTS"}),
        _write(tmp_path / "models.json", {"status": "APPROVED_FROZEN", "models": []}),
        _write(tmp_path / "calibration.json", {"status": "FROZEN_COMPLETE"}),
        _write(tmp_path / "prereg.json", {"status": "FROZEN"}),
        _write(tmp_path / "runtime.json", {"status": "APPROVED_FROZEN"}),
        _write(tmp_path / "run.json", {"status": "FROZEN"}),
    ]

    result = assess_formal_readiness(*paths)

    assert result["status"] == "BLOCKED_FORMAL_PREFLIGHT"
    assert "data:formal_input_files_missing" in result["blockers"]
    assert "models:at_least_two_models_required" in result["blockers"]
    assert result["formal_run_started"] is False


def test_formal_preflight_can_reach_ready_with_complete_evidence(tmp_path: Path) -> None:
    digest = "a" * 64
    data = {
        "status": "FROZEN_FORMAL_INPUTS",
        "formal_input_files": [{"relative_path": "D01/a.csv", "size_bytes": 1, "sha256": digest}],
        "split_audit": "PASS",
        "leak_audit": "PASS",
        "uniqueness_audit": "PASS",
        "test_private_assets_accessed": False,
    }
    data["canonical_manifest_sha256"] = formal_readiness._canonical_sha256(data)
    common_model = {
        "provider": "provider",
        "exact_model_version": "immutable-version",
        "endpoint_or_checkpoint": "checkpoint",
        "adapter_kind": "openai_compatible_json",
        "credential_env": "API_KEY",
        "runtime": "runtime",
        "tokenizer_version": "tokenizer-version",
        "temperature": 0.0,
        "top_p": 1.0,
        "max_input_tokens": 16,
        "max_tokens": 1,
        "retry": 0,
        "timeout_s": 1,
        "concurrency": 1,
        "pricing": "frozen-pricing",
        "budget_usd": 1.0,
        "input_usd_per_1k_tokens": 0.001,
        "output_usd_per_1k_tokens": 0.002,
        "prompt_id": "text_table_v1",
        "prompt_hash": digest,
        "probe_status": "PROBE_PASSED",
        "probe_artifact": "artifacts/probe.json",
        "parser_version": "parser-v1",
        "failure_policy": "retain",
        "tasks": sorted(REQUIRED_TASKS),
        "tracks": ["text_only"],
        "approval_status": "APPROVED",
    }
    models = {
        "status": "APPROVED_FROZEN",
        "models": [
            {"model_id": "model-a", **common_model},
            {"model_id": "model-b", **common_model},
        ],
    }
    calibration = {
        "status": "FROZEN_COMPLETE",
        "test_contaminated": False,
        "test_asset_read": False,
        "config_sha256": digest,
        "results": [{"model_id": "model-a"}, {"model_id": "model-b"}],
    }
    prereg = {
        "status": "FROZEN",
        "hypotheses": {},
        "primary_metrics": {task: "metric" for task in REQUIRED_TASKS},
        "secondary_metrics": [],
        "model_track_matrix": {},
        "repetitions": {},
        "seeds": {},
        "aggregation_rules": {},
        "exclusions": [],
        "stopping_rules": {},
        "cost_ceiling_usd": 1.0,
        "failure_rules": {},
        "robustness_plan": [],
        "ablation_plan": [],
        "test_embargo": {
            "test_input_read": False,
            "test_gold_read": False,
            "private_mapping_read": False,
        },
        "run_directory_rule": "immutable",
        "raw_response_manifest": "raw",
        "cost_latency_failure_manifest": "usage",
        "paper_number_provenance": "chain",
    }
    runtime = {
        "status": "APPROVED_FROZEN",
        "environment_lock_sha256": digest,
        "model_runtimes": [
            {"model_id": "model-a", "available": True},
            {"model_id": "model-b", "available": True},
        ],
    }
    run = {
        "status": "FROZEN",
        "formal_run_started": False,
        "formal_results_written": False,
        "run_index_schema": {"required": []},
        "output_schema": "schema",
        "provenance_chain": ["chain"],
        "raw_response_manifest": "raw",
        "cost_latency_failure_manifest": "usage",
    }
    paths = [
        _write(tmp_path / "data.json", data),
        _write(tmp_path / "models.json", models),
        _write(tmp_path / "calibration.json", calibration),
        _write(tmp_path / "prereg.json", prereg),
        _write(tmp_path / "runtime.json", runtime),
        _write(tmp_path / "run.json", run),
    ]

    result = assess_formal_readiness(*paths)

    assert result["status"] == READY_STATUS
    assert result["blockers"] == []
    assert len(result["artifact_chain"]) == 6


def test_formal_preflight_requires_probe_for_approved_openai_compatible_model(tmp_path: Path) -> None:
    digest = "a" * 64
    data = {
        "status": "FROZEN_FORMAL_INPUTS",
        "formal_input_files": [{"relative_path": "D01/a.csv", "size_bytes": 1, "sha256": digest}],
        "split_audit": "PASS",
        "leak_audit": "PASS",
        "uniqueness_audit": "PASS",
        "test_private_assets_accessed": False,
    }
    data["canonical_manifest_sha256"] = formal_readiness._canonical_sha256(data)
    models = {
        "status": "APPROVED_FROZEN",
        "models": [
            {
                "model_id": "model-a",
                "provider": "provider",
                "exact_model_version": "immutable-version",
                "endpoint_or_checkpoint": "endpoint",
                "adapter_kind": "openai_compatible_json",
                "credential_env": "API_KEY",
                "runtime": "runtime",
                "tokenizer_version": "tokenizer-version",
                "temperature": 0.0,
                "top_p": 1.0,
                "max_input_tokens": 16,
                "max_tokens": 16,
                "retry": 0,
                "timeout_s": 1,
                "concurrency": 1,
                "pricing": "frozen",
                "budget_usd": 1.0,
                "input_usd_per_1k_tokens": 0.001,
                "output_usd_per_1k_tokens": 0.002,
                "prompt_id": "text_table_v1",
                "prompt_hash": digest,
                "parser_version": "parser-v1",
                "failure_policy": "retain",
                "tasks": sorted(REQUIRED_TASKS),
                "tracks": ["text_only"],
                "approval_status": "APPROVED",
            },
            {
                "model_id": "model-b",
                "provider": "provider",
                "exact_model_version": "immutable-version",
                "endpoint_or_checkpoint": "endpoint",
                "adapter_kind": "openai_compatible_json",
                "credential_env": "API_KEY",
                "runtime": "runtime",
                "tokenizer_version": "tokenizer-version",
                "temperature": 0.0,
                "top_p": 1.0,
                "max_input_tokens": 16,
                "max_tokens": 16,
                "retry": 0,
                "timeout_s": 1,
                "concurrency": 1,
                "pricing": "frozen",
                "budget_usd": 1.0,
                "input_usd_per_1k_tokens": 0.001,
                "output_usd_per_1k_tokens": 0.002,
                "prompt_id": "text_table_v1",
                "prompt_hash": digest,
                "parser_version": "parser-v1",
                "failure_policy": "retain",
                "tasks": sorted(REQUIRED_TASKS),
                "tracks": ["text_only"],
                "approval_status": "APPROVED",
                "probe_status": "PROBE_FAILED",
                "probe_artifact": "artifacts/probe_failed.json",
            },
        ],
    }
    calibration = {
        "status": "FROZEN_COMPLETE",
        "test_contaminated": False,
        "test_asset_read": False,
        "config_sha256": digest,
        "results": [{"model_id": "model-a"}, {"model_id": "model-b"}],
    }
    prereg = {
        "status": "FROZEN",
        "hypotheses": {},
        "primary_metrics": {task: "metric" for task in REQUIRED_TASKS},
        "secondary_metrics": [],
        "model_track_matrix": {},
        "repetitions": {},
        "seeds": {},
        "aggregation_rules": {},
        "exclusions": [],
        "stopping_rules": {},
        "cost_ceiling_usd": 1.0,
        "failure_rules": {},
        "robustness_plan": [],
        "ablation_plan": [],
        "test_embargo": {
            "test_input_read": False,
            "test_gold_read": False,
            "private_mapping_read": False,
        },
        "run_directory_rule": "immutable",
        "raw_response_manifest": "raw",
        "cost_latency_failure_manifest": "usage",
        "paper_number_provenance": "chain",
    }
    runtime = {
        "status": "APPROVED_FROZEN",
        "environment_lock_sha256": digest,
        "model_runtimes": [
            {"model_id": "model-a", "available": True},
            {"model_id": "model-b", "available": True},
        ],
    }
    run = {
        "status": "FROZEN",
        "formal_run_started": False,
        "formal_results_written": False,
        "run_index_schema": {"required": []},
        "output_schema": "schema",
        "provenance_chain": ["chain"],
        "raw_response_manifest": "raw",
        "cost_latency_failure_manifest": "usage",
    }
    paths = [
        _write(tmp_path / "data.json", data),
        _write(tmp_path / "models.json", models),
        _write(tmp_path / "calibration.json", calibration),
        _write(tmp_path / "prereg.json", prereg),
        _write(tmp_path / "runtime.json", runtime),
        _write(tmp_path / "run.json", run),
    ]

    result = assess_formal_readiness(*paths)

    assert "models:0:probe_not_passed" in result["blockers"] or "models:0:probe_artifact_missing" in result["blockers"]
    assert "models:1:probe_not_passed" in result["blockers"]
