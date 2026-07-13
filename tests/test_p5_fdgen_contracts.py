from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.fdgen import assess_fdgen_readiness, write_fdgen_decision


def frozen_plan(tmp_path: Path) -> Path:
    path = tmp_path / "plan.json"
    path.write_text(
        json.dumps(
            {
                "generator_version": "TBD_BEFORE_PILOT",
                "fds_version": "TBD_BEFORE_PILOT",
                "budget": {"pilot_case_count": "TBD_BY_APPROVAL_BEFORE_EXECUTION", "formal_case_count": "TBD_BY_APPROVAL_BEFORE_EXECUTION"},
                "hash": "TO_BE_FILLED_AFTER_FREEZE_FILES_STABILIZE",
                "seed_policy": {"master_seed": 7},
                "preallocated_splits": {"test": "BLOCKED"},
            }
        ),
        encoding="utf-8",
    )
    return path


def test_fdgen_is_blocked_without_frozen_versions_runtime_and_approval(tmp_path: Path) -> None:
    result = assess_fdgen_readiness(frozen_plan(tmp_path))

    assert result["status"] == "BLOCKED"
    assert "generator_version_not_frozen" in result["blockers"]
    assert "fdgen_runtime_not_available" in result["blockers"]
    assert result["generated_count"] == 0
    assert result["generation_manifest"] == []
    assert result["resource_cost"] is None
    assert result["generated_data_written"] is False
    assert result["test_asset_read"] is False


def test_approved_runtime_requires_all_plan_gates(tmp_path: Path) -> None:
    plan = frozen_plan(tmp_path)
    result = assess_fdgen_readiness(plan, runtime_metadata={"executable_available": True, "approval_gates_closed": True})
    assert result["status"] == "BLOCKED"
    assert "fds_version_not_frozen" in result["blockers"]


def test_decision_file_is_machine_readable(tmp_path: Path) -> None:
    plan = frozen_plan(tmp_path)
    output = tmp_path / "fdgen.json"
    result = write_fdgen_decision(plan, output)
    assert output.is_file()
    assert result["fdgen_version"] == "P5-FDGEN-001"
