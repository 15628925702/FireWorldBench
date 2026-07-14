from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.anonymization import assess_anonymization, write_anonymization_decision


def test_anonymization_is_blocked_without_paper_export() -> None:
    result = assess_anonymization()

    assert result["status"] == "BLOCKED_NO_EXPORT"
    assert "paper_export_missing" in result["blockers"]
    assert result["anonymous_package"] is None


def test_explicit_export_root_finds_identity_and_keeps_asset_excluded(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    source.write_text("Author: Alice\npath=C:\\Users\\Alice\\paper\n", encoding="utf-8")

    result = assess_anonymization(tmp_path)

    assert result["status"] == "BLOCKED_NO_EXPORT"
    assert "identity_or_secret_findings" in result["blockers"]
    assert result["excluded_assets"] == [{"path": "README.md", "classification": "REVIEW_REQUIRED"}]


def test_anonymization_decision_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "anon.json"
    result = write_anonymization_decision(output)

    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
