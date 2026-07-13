from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.error_analysis import TAXONOMY, assess_error_analysis, build_error_plan, write_error_decision


def test_error_analysis_is_blocked_without_raw_and_keeps_negative_result_policy() -> None:
    result = assess_error_analysis()

    assert result["status"] == "BLOCKED_NO_RAW_OUTPUT"
    assert result["taxonomy"] == TAXONOMY
    assert result["error_labels"] == []
    assert result["sampling_list"] == []
    assert result["adjudication"]["representative_case_index"] == []
    assert result["negative_results_retained"] is True
    assert result["sampling"]["model_identity_visible"] is False


def test_error_plan_is_deterministic_and_posthoc_selection_is_forbidden() -> None:
    plan = build_error_plan()
    assert plan == build_error_plan()
    assert plan["sampling"]["posthoc_case_selection"] is False
    assert plan["adjudication"]["rater_count"] == 2


def test_error_decision_file_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "errors.json"
    result = write_error_decision(output)
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
