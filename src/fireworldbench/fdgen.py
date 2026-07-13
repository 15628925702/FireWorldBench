"""Readiness audit for the frozen FDS/FD-Gen generation plan."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

FDGEN_VERSION = "P5-FDGEN-001"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def assess_fdgen_readiness(plan_path: Path, *, runtime_metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Audit the frozen plan without starting a simulator or reading datasets."""

    plan_bytes = plan_path.read_bytes()
    plan = json.loads(plan_bytes.decode("utf-8"))
    runtime = dict(runtime_metadata or {})
    blockers: list[str] = []
    for field in ("generator_version", "fds_version"):
        if plan.get(field) in {None, "", "TBD_BEFORE_PILOT"}:
            blockers.append(field + "_not_frozen")
    budget = plan.get("budget", {})
    for field in ("pilot_case_count", "formal_case_count"):
        if budget.get(field) in {None, "", "TBD_BY_APPROVAL_BEFORE_EXECUTION"}:
            blockers.append(field + "_not_approved")
    if plan.get("hash") in {None, "", "TO_BE_FILLED_AFTER_FREEZE_FILES_STABILIZE"}:
        blockers.append("frozen_plan_hash_not_final")
    if not runtime.get("executable_available", False):
        blockers.append("fdgen_runtime_not_available")
    if not runtime.get("approval_gates_closed", False):
        blockers.append("generation_approval_gates_not_closed")
    status = "READY_TO_GENERATE" if not blockers else "BLOCKED"
    return {
        "fdgen_version": FDGEN_VERSION,
        "status": status,
        "blockers": blockers,
        "frozen_plan_sha256": _sha256_bytes(plan_bytes),
        "generator_version": plan.get("generator_version"),
        "fds_version": plan.get("fds_version"),
        "seed_policy": plan.get("seed_policy"),
        "preallocated_splits": plan.get("preallocated_splits"),
        "generated_count": 0,
        "success_count": 0,
        "failure_count": 0,
        "generation_manifest": [],
        "failure_log": [],
        "resource_cost": None,
        "generated_data_written": False,
        "test_asset_read": False,
        "runtime_metadata": runtime,
    }


def write_fdgen_decision(plan_path: Path, output_path: Path) -> dict[str, Any]:
    result = assess_fdgen_readiness(plan_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
