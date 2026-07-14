from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.paper_export import assess_paper_export, write_paper_export_decision


def test_export_is_blocked_without_frozen_results_and_creates_no_roots() -> None:
    result = assess_paper_export()

    assert result["status"] == "BLOCKED_NO_FROZEN_RESULTS"
    assert result["generated"] is False
    assert result["public_root"] is None
    assert result["private_root"] is None
    assert result["manifest_policy"]["manifest_self_hash_excluded"] is True


def test_export_manifest_without_run_ids_is_blocked(tmp_path: Path) -> None:
    results = tmp_path / "results.json"
    results.write_text('{"result_freeze_manifest": {"run_ids": []}}\n', encoding="utf-8")

    result = assess_paper_export(results)

    assert result["status"] == "BLOCKED_NO_FROZEN_RESULTS"
    assert "result_freeze_manifest_has_no_run_ids" in result["blockers"]
    assert result["source_results_sha256"]


def test_export_decision_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "export.json"
    result = write_paper_export_decision(output)

    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
