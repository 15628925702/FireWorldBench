from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.reproduction import assess_reproduction, write_reproduction_decision


def test_reproduction_is_blocked_without_release_root() -> None:
    result = assess_reproduction()

    assert result["status"] == "BLOCKED_NO_RELEASE_INPUT"
    assert result["clean_environment"]["created"] is False
    assert result["rebuild_log"] == []
    assert result["rebuild_hashes"] == []
    assert result["minimum_result_reproduced"] is False


def test_release_root_without_readme_is_blocked(tmp_path: Path) -> None:
    result = assess_reproduction(tmp_path)

    assert result["status"] == "BLOCKED_NO_RELEASE_INPUT"
    assert "release_readme_missing" in result["blockers"]


def test_reproduction_decision_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "repro.json"
    result = write_reproduction_decision(output)

    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
