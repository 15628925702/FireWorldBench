from pathlib import Path

from fireworldbench.research_run import TASKS, build_research_dataset


def test_research_build_uses_visible_group_first_holdout(tmp_path: Path) -> None:
    source = tmp_path / "data" / "raw" / "D01_Immersed-Tunnel-CFD"
    source.mkdir(parents=True)
    for kind in ("M", "U"):
        for index in range(1, 6):
            for position in ("70", "100", "130"):
                name = f"{position}{kind}{index:02d}_devc.csv"
                (source / name).write_text(
                    "s,C\nTime,Temperature\n0,20\n1,22\n2,40\n3,45\n4,100\n5,110\n",
                    encoding="utf-8",
                )

    result = build_research_dataset(tmp_path, deepseek_per_task=1)

    split = result["split"]
    assert split["overlap"] is False
    assert split["hidden_test"] is False
    assert split["ordinary_visible_holdout"] is True
    family_sets = {key: set(value) for key, value in split["families"].items()}
    assert not family_sets["train"] & family_sets["dev"]
    assert not family_sets["train"] & family_sets["holdout"]
    assert not family_sets["dev"] & family_sets["holdout"]
    assert all(result["sample_counts"][partition] > 0 for partition in ("train", "dev", "holdout"))
    assert all(result["task_counts"]["dev"][task] > 0 for task in TASKS)
    assert result["deepseek_sample_count"] == len(TASKS)
    assert result["expert_review_status"] == "NOT_AVAILABLE_PRELIMINARY_AUTO_LABELS"
    assert result["formal_benchmark_eligible"] is False
