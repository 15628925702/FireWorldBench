from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.benchmark_integration import (
    REQUIRED_CHAIN,
    assess_integration,
    write_integration_decision,
)


def test_blocked_fdgen_produces_no_input_decision() -> None:
    result = assess_integration({"status": "BLOCKED", "generated_count": 0, "generation_manifest": []})

    assert result["status"] == "BLOCKED_NO_INPUT"
    assert "no_generated_cases" in result["blockers"]
    assert result["input_manifest"] == []
    assert result["integration_written"] is False
    assert result["existing_p3_p4_artifacts_modified"] is False
    assert result["test_access_ledger"] == "NO_ACCESS_CONFIRMED"
    assert result["required_chain"] == REQUIRED_CHAIN


def test_nonempty_count_requires_complete_manifest() -> None:
    result = assess_integration({"status": "READY_TO_GENERATE", "generated_count": 2, "generation_manifest": [{"case_id": "a"}]})

    assert result["status"] == "BLOCKED_NO_INPUT"
    assert "generated_manifest_missing_or_inconsistent" in result["blockers"]


def test_complete_manifest_is_only_eligible_for_full_chain() -> None:
    result = assess_integration({"status": "READY_TO_GENERATE", "generated_count": 1, "generation_manifest": [{"case_id": "a"}]})

    assert result["status"] == "READY_TO_INTEGRATE"
    assert result["input_case_count"] == 1
    assert result["input_manifest"] == [{"case_id": "a"}]
    assert result["integration_written"] is False


def test_integration_file_entrypoint_is_machine_readable(tmp_path: Path) -> None:
    fdgen = tmp_path / "fdgen.json"
    fdgen.write_text('{"status": "BLOCKED", "generated_count": 0, "generation_manifest": []}\n', encoding="utf-8")
    output = tmp_path / "integration.json"
    result = write_integration_decision(fdgen, output)
    assert output.is_file()
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
