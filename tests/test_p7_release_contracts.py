from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.release_audit import assess_release_freeze, write_release_audit


def test_release_freeze_is_blocked_by_critical_risks() -> None:
    result = assess_release_freeze()

    assert result["status"] == "BLOCKED_CRITICAL_RISKS"
    assert len(result["critical_risks"]) >= 5
    assert result["external_release"]["tag_created"] is False
    assert result["external_release"]["github_release_created"] is False
    assert result["local_freeze_only"] is True


def test_release_audit_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "release.json"
    result = write_release_audit(output)

    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
