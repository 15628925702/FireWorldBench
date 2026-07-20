from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.preregister import (
    NO_ACCESS_CONFIRMED,
    build_preregistration,
    validate_preregistration,
    write_preregistration,
)


def test_preregistration_is_deterministic_and_test_sealed() -> None:
    first = build_preregistration()
    second = build_preregistration()
    assert first == second
    assert first["status"] == "BLOCKED_PENDING_APPROVAL"
    assert first["test_access"]["ledger"] == NO_ACCESS_CONFIRMED
    assert first["test_access"]["test_input_read"] is False
    assert validate_preregistration(first) == []


def test_matrices_are_disjoint_and_metrics_are_frozen() -> None:
    plan = build_preregistration()
    assert set(plan["main_matrix"]).isdisjoint(plan["exploratory_matrix"])
    assert len(plan["primary_metrics"]) == 9
    assert plan["repetitions"]["main"] == 1
    assert plan["stopping_rules"]["failed_runs_retained"] is True


def test_invalid_preregistration_is_rejected() -> None:
    plan = build_preregistration()
    plan["test_access"]["test_gold_read"] = True
    assert "test_gold_read" in validate_preregistration(plan)[0]


def test_preregistration_file_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "prereg.json"
    result = write_preregistration(output)
    assert json.loads(output.read_text(encoding="utf-8"))["plan_sha256"] == result["plan_sha256"]
