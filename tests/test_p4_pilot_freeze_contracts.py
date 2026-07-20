from __future__ import annotations

from pathlib import Path

from fireworldbench.pilot_freeze import (
    NO_ACCESS_CONFIRMED,
    build_pilot_plan,
    validate_pilot_plan,
    write_pilot_plan,
)


def test_pilot_plan_is_deterministic_and_test_sealed() -> None:
    first = build_pilot_plan()
    second = build_pilot_plan()
    assert first == second
    assert first["status"] == "BLOCKED_PENDING_APPROVAL"
    assert first["split_policy"]["test_access_ledger"] == NO_ACCESS_CONFIRMED
    assert first["split_policy"]["test_tuning"] is False
    assert first["test_asset_read"] is False
    assert validate_pilot_plan(first) == []


def test_main_and_exploratory_matrices_are_disjoint() -> None:
    plan = build_pilot_plan()
    assert set(plan["main_matrix"]).isdisjoint(plan["exploratory_matrix"])
    assert plan["sample_counts"] == {"train_id": None, "dev_id": None}
    assert plan["budgets"]["max_cost_usd"] is None


def test_invalid_test_selection_rule_is_rejected() -> None:
    plan = build_pilot_plan()
    plan["selection_rule"] = "select model by test performance"
    assert "selection rule" in validate_pilot_plan(plan)[0]


def test_plan_file_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "pilot.json"
    result = write_pilot_plan(output)
    assert output.is_file()
    assert result["pilot_version"] == "P4-PILOT-FREEZE-001"
