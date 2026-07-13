from __future__ import annotations

from pathlib import Path

from fireworldbench.llm_baseline import LLMConfig, freeze_config, run_llm_pilot, run_llm_pilot_file


def sample(sample_id: str = "dev-1", split: str = "dev_id") -> dict[str, str]:
    return {"sample_id": sample_id, "split": split, "task": "T1-A"}


def test_frozen_configs_are_deterministic_and_block_without_approval() -> None:
    config = LLMConfig(track="text_only_table", prompt_id="text_table_v1")
    assert freeze_config(config)["config_sha256"] == freeze_config(config)["config_sha256"]

    result = run_llm_pilot([sample()], config)
    assert result["status"] == "BLOCKED"
    assert result["executed_count"] == 0
    assert result["cost"]["estimated_usd"] is None
    assert result["test_asset_read"] is False


def test_approved_mock_pilot_reports_repeats_variance_cost_and_failures() -> None:
    config = LLMConfig(
        track="text_only_table",
        prompt_id="text_table_v1",
        model_id="approved/mock-v1",
        approved=True,
        repeats=2,
        input_usd_per_1k_tokens=1.0,
        output_usd_per_1k_tokens=1.0,
        max_cost_usd=10.0,
    )

    def adapter(item, prompt, frozen):
        label = "fire_forming" if item["sample_id"] == "dev-1" else "not_fire_forming"
        return {"answer": {"label": label}}

    result = run_llm_pilot([sample()], config, adapter=adapter)
    assert result["status"] == "COMPLETED"
    assert result["dev_runs"][0]["repeats"] == 2
    assert result["variance"]["repeat_disagreement_rate"] == 0.0
    assert result["cost"]["estimated_usd"] > 0


def test_llm_pilot_refuses_test_split_and_cli_file_is_blocked(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '{"default_config": {"track": "multimodal", "prompt_id": "multimodal_v1"}}\n',
        encoding="utf-8",
    )
    output = tmp_path / "pilot.json"
    result = run_llm_pilot_file(None, config_path, output)
    assert result["status"] == "BLOCKED"
    assert output.is_file()
    try:
        run_llm_pilot([sample("test-1", "test_id")], LLMConfig(track="text_only_table", prompt_id="text_table_v1"))
    except ValueError as exc:
        assert "train_id" in str(exc)
    else:
        raise AssertionError("test split must be refused")
