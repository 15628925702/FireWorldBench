from pathlib import Path

from fireworldbench.staging_integration import assess_staging


def test_staging_assessment_is_fail_closed_and_read_only(tmp_path: Path) -> None:
    source = tmp_path / "data" / "raw" / "D01_Immersed-Tunnel-CFD"
    source.mkdir(parents=True)
    raw = source / "sample.csv"
    raw.write_text("s,kW/m2\nTime,HRRPUA\n0,1\n", encoding="utf-8")
    for name in (
        "D02_PolyUFire", "D03_FDS-exp", "D04_FD-Gen", "D05_D-Fire", "D10_FIgLib-SmokeyNet"
    ):
        (tmp_path / "data" / "raw" / name).mkdir(parents=True)
    before = raw.read_bytes()

    result = assess_staging(tmp_path)

    assert result["status"] == "BLOCKED_STAGING_INTEGRATION"
    assert result["raw_files_modified"] is False
    assert raw.read_bytes() == before
    assert all(item["formal_benchmark_eligible"] is False for item in result["datasets"])
