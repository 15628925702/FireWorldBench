from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.paper_text import assess_text_registry, write_text_decision


def test_text_registry_is_blocked_without_frozen_statistics() -> None:
    result = assess_text_registry()

    assert result["status"] == "BLOCKED_NO_FROZEN_RESULTS"
    assert result["text_number_registry"] == []
    assert result["run_metric_provenance"] == []
    assert result["manual_text_copy"] is False


def test_claims_manifest_without_run_ids_cannot_supply_text_numbers(tmp_path: Path) -> None:
    results = tmp_path / "claims.json"
    results.write_text('{"result_freeze_manifest": {"run_ids": []}}\n', encoding="utf-8")

    result = assess_text_registry(results)

    assert result["status"] == "BLOCKED_NO_FROZEN_RESULTS"
    assert "result_freeze_manifest_has_no_run_ids" in result["blockers"]
    assert result["unmapped_result_numbers"] == []


def test_manuscript_scan_requires_mapping_and_decision_is_machine_readable(tmp_path: Path) -> None:
    manuscript = tmp_path / "paper.tex"
    manuscript.write_text("Accuracy was 91.5% in 2027.\n", encoding="utf-8")
    output = tmp_path / "text.json"

    result = write_text_decision(output, manuscript_path=manuscript)

    assert result["status"] == "BLOCKED_NO_FROZEN_RESULTS"
    assert "unmapped_manuscript_numbers" in result["blockers"]
    assert len(result["manuscript_number_scan"]) == 2
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
