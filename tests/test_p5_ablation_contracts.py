from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.ablation import assess_ablation, build_ablation_plan, write_ablation_decision


def test_ablation_is_blocked_without_main_run_and_has_one_factor_diffs() -> None:
    result = assess_ablation({"status": "BLOCKED", "run_index": []})

    assert result["status"] == "BLOCKED_NO_MAIN_RUN"
    assert result["ablation_runs"] == []
    assert result["parameter_diffs"] == []
    assert result["paired_result_index"] == []
    assert all(factor["changed_factor_count"] == 1 for factor in result["factors"])
    assert result["test_asset_read"] is False


def test_ablation_plan_is_deterministic_and_exploratory() -> None:
    first = build_ablation_plan()
    second = build_ablation_plan()
    assert first == second
    assert first["extra_findings_label"] == "exploratory_only"
    assert first["test_access_ledger"] == "NO_ACCESS_CONFIRMED"


def test_ablation_file_is_machine_readable(tmp_path: Path) -> None:
    main_run = tmp_path / "main.json"
    main_run.write_text('{"status": "BLOCKED", "run_index": []}\n', encoding="utf-8")
    output = tmp_path / "ablation.json"
    result = write_ablation_decision(main_run, output)
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
