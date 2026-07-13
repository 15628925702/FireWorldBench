from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.paper_tables import assess_table_export, write_table_export_decision


def test_tables_are_blocked_without_frozen_results() -> None:
    result = assess_table_export()

    assert result["status"] == "BLOCKED_NO_FROZEN_RESULTS"
    assert "frozen_results_missing" in result["blockers"]
    assert result["csv_outputs"] == []
    assert result["json_outputs"] == []
    assert result["latex_outputs"] == []
    assert result["manual_number_copy"] is False


def test_claims_matrix_without_run_ids_cannot_export_tables(tmp_path: Path) -> None:
    results = tmp_path / "claims.json"
    results.write_text('{"result_freeze_manifest": {"run_ids": []}}\n', encoding="utf-8")
    result = assess_table_export(results)

    assert result["status"] == "BLOCKED_NO_FROZEN_RESULTS"
    assert "result_freeze_manifest_has_no_run_ids" in result["blockers"]


def test_table_decision_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "tables.json"
    result = write_table_export_decision(output)
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
