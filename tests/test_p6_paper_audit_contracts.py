from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.paper_audit import assess_paper_audit, write_paper_audit


def test_paper_audit_is_blocked_without_four_frozen_exports() -> None:
    result = assess_paper_audit()

    assert result["status"] == "BLOCKED_NO_FROZEN_EXPORTS"
    assert len(result["blockers"]) == 4
    assert result["numeric_trace_audit"] == []
    assert result["unexplained_numeric_differences"] == []
    assert result["scan_policy"]["overwrite_existing_exports"] is False


def test_export_without_run_ids_cannot_pass_trace_audit(tmp_path: Path) -> None:
    source = tmp_path / "text.json"
    source.write_text('{"result_freeze_manifest": {"run_ids": []}}\n', encoding="utf-8")

    result = assess_paper_audit(text_path=source)

    assert "text_has_no_frozen_run_ids" in result["blockers"]
    assert result["sources"][-1]["sha256"]


def test_audit_output_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "audit.json"
    result = write_paper_audit(output)

    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
