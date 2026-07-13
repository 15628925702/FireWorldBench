from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.claims import build_claims_matrix, validate_claims_matrix, write_claims_matrix


def test_claims_have_status_evidence_and_no_result_ids() -> None:
    matrix = build_claims_matrix()

    assert matrix["status"] == "FROZEN_WITH_BLOCKED_CLAIMS"
    assert validate_claims_matrix(matrix) == []
    assert all(claim["status"] for claim in matrix["claims"])
    assert matrix["result_freeze_manifest"]["run_ids"] == []
    assert matrix["test_access_ledger"] == "NO_ACCESS_CONFIRMED"


def test_blocked_and_removed_claims_are_explicit() -> None:
    statuses = {claim["status"] for claim in build_claims_matrix()["claims"]}
    assert "BLOCKED_NO_RESULTS" in statuses
    assert "REMOVED_NO_FROZEN_RESULTS" in statuses
    assert "N_A_NO_APPROVED_VISUAL_RESOURCES" in statuses


def test_claims_file_is_machine_readable(tmp_path: Path) -> None:
    output = tmp_path / "claims.json"
    result = write_claims_matrix(output)
    assert json.loads(output.read_text(encoding="utf-8"))["matrix_sha256"] == result["matrix_sha256"]
