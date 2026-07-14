from pathlib import Path

from fireworldbench.full_planning_pilot import build_full_planning_pilot


def test_full_planning_pilot_is_group_first_and_covers_all_tasks(tmp_path: Path) -> None:
    source = tmp_path / "data" / "raw" / "D01_Immersed-Tunnel-CFD"
    source.mkdir(parents=True)
    for name in ("70M01", "130M01", "70U16", "130U16"):
        (source / f"{name}_devc.csv").write_text("s,C\nTime,Temperature\n0,20\n1,22\n2,40\n3,45\n4,100\n5,110\n", encoding="utf-8")

    result = build_full_planning_pilot(tmp_path, max_cases=4, rows_per_case=6)

    assert result["case_split"]["overlap"] is False
    assert result["train_sample_count"] == 48
    assert result["sample_count"] == 51
    assert all(count > 0 for count in result["task_counts"].values())
    assert result["formal_benchmark_eligible"] is False
    t1c = next(sample for sample in result["samples"] if sample["task"] == "T1-C")
    t3b = next(sample for sample in result["samples"] if sample["task"] == "T3-B")
    assert len(t1c["observations"]) == 1
    assert t1c["answer"]["selected_observation_id_or_stop"] in t1c["question"]["options"]
    assert t3b["answer"]["label"] != "pair_invalid"
    assert "case_a=" in t3b["question"]["prompt"]
    t3a_late = next(sample for sample in result["samples"] if sample["task"] == "T3-A" and sample["sample_id"].endswith("late-t3"))
    assert "t=4.0 s" in t3a_late["question"]["prompt"]
