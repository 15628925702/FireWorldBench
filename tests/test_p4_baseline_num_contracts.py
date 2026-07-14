from __future__ import annotations

from fireworldbench.baseline import run_baseline


def sample(sample_id: str, split: str, task: str = "T1-A", label: str = "fire_forming") -> dict:
    return {"sample_id": sample_id, "split": split, "task": task, "answer": {"label": label}}


def test_chance_is_seeded_and_majority_uses_train_only() -> None:
    dev = [sample("dev_1", "dev_id")]
    train = [sample("train_1", "train_id", label="not_fire_forming"), sample("train_2", "train_id", label="not_fire_forming")]

    chance_a = run_baseline(dev, strategy="chance", seed=7)
    chance_b = run_baseline(dev, strategy="chance", seed=7)
    majority = run_baseline(dev, strategy="majority", train_samples=train)

    assert chance_a == chance_b
    assert majority["predictions"][0]["answer"]["label"] == "not_fire_forming"
    assert majority["predictions"][0]["schema_version"] == "2.0"


def test_temporal_and_test_split_boundaries() -> None:
    result = run_baseline([sample("dev_1", "dev_id", task="T3-A")], strategy="temporal_persistence")
    assert result["predictions"][0]["answer"]["label"] == "stable"
    try:
        run_baseline([sample("test_1", "test_id")], strategy="chance")
    except ValueError as exc:
        assert "train_id" in str(exc)
    else:
        raise AssertionError("test split must be refused")
