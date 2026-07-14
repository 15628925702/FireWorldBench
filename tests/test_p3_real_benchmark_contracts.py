from pathlib import Path

from fireworldbench.real_benchmark import build_candidate_manifest


def test_fds_candidate_builder_is_explicit_and_non_formal(tmp_path: Path) -> None:
    raw_root = tmp_path / "data" / "raw"
    for name in ("D01_Immersed-Tunnel-CFD", "D02_PolyUFire", "D03_FDS-exp"):
        (raw_root / name).mkdir(parents=True)
    csv_path = raw_root / "D01_Immersed-Tunnel-CFD" / "case.csv"
    csv_path.write_text("s,kW/m2\nTime,HRRPUA\n0,1\n1,2\n", encoding="utf-8")
    before = csv_path.read_bytes()

    result = build_candidate_manifest(tmp_path)

    d01 = next(item for item in result["datasets"] if item["dataset_id"] == "D01")
    assert result["status"] == "CANDIDATE_CASES_BUILT_FORMAL_USE_BLOCKED"
    assert d01["candidate_case_count"] == 1
    assert d01["candidate_cases"][0]["format"] == "FDS_CSV_TWO_ROW_HEADER"
    assert d01["candidate_cases"][0]["time_range"] == {"min": 0.0, "max": 1.0, "unit": "s"}
    assert result["formal_benchmark_eligible"] is False
    assert csv_path.read_bytes() == before
