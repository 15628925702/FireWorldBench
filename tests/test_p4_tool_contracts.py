from __future__ import annotations

from pathlib import Path

from fireworldbench.tool_tracks import ToolPolicy, ToolSandbox, replay_trace, run_tool_ablation, run_tool_ablation_file


def sample(split: str = "dev_id") -> dict[str, str]:
    return {"sample_id": "dev-1", "split": split, "task": "T1-A"}


def test_sandbox_enforces_whitelist_limits_and_replay() -> None:
    policy = ToolPolicy("retrieval", "kb-v1", ("knowledge_base_lookup",), 1, 1, "retrieval_only")
    sandbox = ToolSandbox(policy, {"knowledge_base_lookup": lambda args: {"answer": "known"}})

    assert sandbox.call("knowledge_base_lookup", {"query": "fire"}) == {"answer": "known"}
    assert sandbox.call("plot_series", {})["status"] == "rejected_tool"
    assert replay_trace(sandbox.trace) == [{"answer": "known"}, {"status": "rejected_tool", "error": "tool is not on the frozen whitelist"}]


def test_tool_ablation_is_blocked_without_approved_model_and_refuses_test() -> None:
    blocked = run_tool_ablation([sample()])
    assert blocked["status"] == "BLOCKED"
    assert blocked["budget_mixing"] is False
    assert blocked["joint_ranking"] is False
    try:
        run_tool_ablation([sample("test_id")])
    except ValueError as exc:
        assert "train_id" in str(exc)
    else:
        raise AssertionError("test split must be refused")


def test_same_callback_runs_tracks_separately_with_cost_and_trace() -> None:
    policies = {
        "retrieval": ToolPolicy("retrieval", "kb-v1", ("knowledge_base_lookup",), 1, 1, "retrieval_only"),
        "plot": ToolPolicy("plot", "plot-v1", ("plot_series",), 1, 1, "plot_only"),
    }

    def adapter(item, sandbox, config):
        tool = "knowledge_base_lookup" if config["track"] == "retrieval" else "plot_series"
        sandbox.handlers[tool] = lambda args: {"track": config["track"]}
        sandbox.call(tool, {"sample_id": item["sample_id"]})
        return {"answer": {"label": "insufficient_information"}}

    result = run_tool_ablation([sample()], policies=policies, adapter=adapter)
    assert result["status"] == "COMPLETED"
    assert result["tracks"]["retrieval"]["cost_units"] == 1
    assert result["tracks"]["plot"]["trace_replay"][0]["track"] == "plot"
    assert result["budget_mixing"] is False


def test_tool_file_entrypoint_records_blocked_report(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        '{"policies": {"retrieval": {"knowledge_base_id": "kb", "allowed_tools": ["knowledge_base_lookup"], "max_calls": 1, "max_cost_units": 1, "information_budget": "retrieval_only"}}}\n',
        encoding="utf-8",
    )
    output = tmp_path / "tool.json"
    result = run_tool_ablation_file(config, output)
    assert result["status"] == "BLOCKED"
    assert output.is_file()
