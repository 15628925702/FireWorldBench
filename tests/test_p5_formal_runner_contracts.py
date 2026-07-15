from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.formal_runner import write_formal_probe, write_formal_run


def _sample(split: str = "dev_id") -> dict:
    return {
        "schema_version": "2.0",
        "sample_id": "FWB-v1-T1-A-case_1-x",
        "benchmark_version": "v1",
        "task": "T1-A",
        "split": split,
        "scenario": {"case_uid": "case_1", "domain": "fire_physics", "family_uid": "family_1", "intervention": None},
        "observations": [{"observation_id": "obs_1", "modality": "sensor_table", "time_range_s": [0, 1], "content_ref": "fixture.csv", "units": {"time": "s"}, "quality": "valid", "visible_fields": ["HRR"]}],
        "question": {"format": "structured_json", "prompt": "Use the visible observation."},
        "answer": {"label": "fire_forming"},
        "physical_trace": {"initial_state": {}, "mechanism_chain": [], "transitions": [], "outcome": {}, "evidence_links": ["obs_1"], "origin": ["deterministic_rule"]},
        "scoring_metadata": {"visibility": "private", "gold_ref": "gold_1", "metric_profile": "T1-A"},
        "provenance": {"source_id": "D01", "source_version": "fixture", "parent_manifest_sha256": "a" * 64, "builder_version": "fixture", "config_sha256": "b" * 64, "annotation_status": "automatic"},
    }


def _matrix(tmp_path: Path, *, approval_status: str = "APPROVED", budget_usd: float = 1.0) -> Path:
    path = tmp_path / "models.json"
    path.write_text(
        json.dumps(
            {
                "status": "APPROVED_FROZEN",
                "models": [
                    {
                        "model_id": "deepseek-chat",
                        "provider": "DeepSeek",
                        "exact_model_version": "deepseek-chat",
                        "endpoint_or_checkpoint": "https://api.deepseek.com/chat/completions",
                        "adapter_kind": "openai_compatible_json",
                        "credential_env": "DEEPSEEK_API_KEY",
                        "runtime": "OpenAI-compatible HTTPS adapter",
                        "tokenizer_version": "provider-default",
                        "temperature": 0.0,
                        "top_p": 1.0,
                        "max_input_tokens": 2048,
                        "max_tokens": 64,
                        "retry": 0,
                        "timeout_s": 30,
                        "concurrency": 1,
                        "pricing": "frozen",
                        "budget_usd": budget_usd,
                        "input_usd_per_1k_tokens": 0.001,
                        "output_usd_per_1k_tokens": 0.002,
                        "prompt_id": "text_table_v1",
                        "prompt_hash": "a" * 64,
                        "parser_version": "parser-v1",
                        "failure_policy": "retain",
                        "tasks": ["T1-A", "T1-B", "T1-C", "T2-A", "T2-B", "T2-C", "T3-A", "T3-B", "T3-C"],
                        "tracks": ["text_only", "table"],
                        "approval_status": approval_status,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_formal_probe_scores_visible_dev_samples(tmp_path: Path) -> None:
    samples = tmp_path / "samples.json"
    samples.write_text(json.dumps({"samples": [_sample()]}), encoding="utf-8")
    matrix = _matrix(tmp_path, approval_status="BLOCKED_NO_RUNTIME", budget_usd=1.0)

    def adapter(sample, prompt, config):
        assert "gold_1" not in prompt
        return {
            "answer": {"label": "fire_forming"},
            "evidence": ["obs_1"],
            "uncertainty": {"level": "low", "reason": "fixture"},
            "missing_information": [],
            "_provider_usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "_raw_provider_response": {"id": "raw-1"},
        }

    result = write_formal_probe(
        samples,
        matrix,
        tmp_path / "probe.json",
        "deepseek-chat",
        allow_unapproved=True,
        adapter=adapter,
    )

    assert result["status"] == "PROBE_PASSED"
    assert result["task_metrics"]["T1-A"]["primary_metric"] == 1.0
    assert result["failure_counts"] == {}


def test_formal_run_blocks_before_spending_when_budget_is_too_small(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess_sample = _sample("test_id")
    samples = root / "samples.json"
    samples.write_text(json.dumps({"samples": [subprocess_sample]}), encoding="utf-8")
    matrix = _matrix(root, budget_usd=0.0)
    readiness = root / "readiness.json"
    readiness.write_text(json.dumps({"status": "READY_FOR_FORMAL_MULTI_MODEL_FULL_RUN", "frozen_input_manifest_hash": "a" * 64, "model_matrix_hash": "b" * 64, "calibration_hash": "c" * 64, "preregistration_hash": "d" * 64, "runtime_hash": "e" * 64}), encoding="utf-8")

    def adapter(sample, prompt, config):
        raise AssertionError("budget guard should stop before any paid call")

    run = write_formal_run(
        samples,
        matrix,
        readiness,
        root / "artifacts" / "formal_runs" / "run_budget",
        "deepseek-chat",
        repository_root=root,
        require_clean_git=False,
        adapter=adapter,
    )

    assert run["status"] == "COMPLETED_WITH_FAILURES"
    public = json.loads((root / "artifacts" / "formal_runs" / "run_budget" / "public" / "cost_latency_failures.json").read_text(encoding="utf-8"))
    assert public["executed_count"] == 0
    assert public["failures"][0]["status"] == "budget_blocked"
