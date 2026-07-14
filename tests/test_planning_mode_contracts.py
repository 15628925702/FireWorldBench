import json
from pathlib import Path

from fireworldbench.real_benchmark import build_candidate_manifest
from fireworldbench.staging_integration import assess_staging


def test_planning_mode_allows_local_train_dev_but_not_formal_release(tmp_path: Path) -> None:
    raw_root = tmp_path / "data" / "raw"
    for name in (
        "D01_Immersed-Tunnel-CFD", "D02_PolyUFire", "D03_FDS-exp",
        "D04_FD-Gen", "D05_D-Fire", "D10_FIgLib-SmokeyNet",
    ):
        (raw_root / name).mkdir(parents=True)
    fds = raw_root / "D01_Immersed-Tunnel-CFD" / "case.csv"
    fds.write_text("s,kW/m2\nTime,HRRPUA\n0,1\n1,2\n", encoding="utf-8")

    candidate = build_candidate_manifest(tmp_path)
    staging = assess_staging(tmp_path)

    assert candidate["local_planning_mode"] is True
    assert candidate["datasets"][0]["training_eligible"] == "LOCAL_PLANNING_ALLOWED"
    assert candidate["datasets"][0]["development_eligible"] == "LOCAL_PLANNING_ALLOWED"
    assert candidate["formal_benchmark_eligible"] is False
    assert candidate["datasets"][0]["redistribution_eligible"] == "BLOCKED"
    assert staging["local_planning_mode"] is True
    assert all(item["testing_eligible"] == "BLOCKED" for item in staging["datasets"])
    assert json.loads(json.dumps(candidate))["raw_files_modified"] is False
