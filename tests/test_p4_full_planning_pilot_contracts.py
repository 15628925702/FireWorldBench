from pathlib import Path

from fireworldbench.full_planning_pilot import build_full_planning_pilot


def test_full_planning_pilot_is_group_first_and_covers_all_tasks(tmp_path: Path) -> None:
    source = tmp_path / "data" / "raw" / "D01_Immersed-Tunnel-CFD"
    source.mkdir(parents=True)
    for index in range(4):
        (source / f"case_{index}.csv").write_text("s,C\nTime,Temperature\n0,20\n1,40\n2,100\n", encoding="utf-8")

    result = build_full_planning_pilot(tmp_path, max_cases=4, rows_per_case=3)

    assert result["case_split"]["overlap"] is False
    assert result["train_sample_count"] == 16
    assert result["sample_count"] == 17
    assert all(count > 0 for count in result["task_counts"].values())
    assert result["formal_benchmark_eligible"] is False
