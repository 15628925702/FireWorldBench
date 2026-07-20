from __future__ import annotations

from fireworldbench.evaluation import (
    bootstrap_mean_ci,
    evidence_f1,
    macro_f1,
    pair_ranking_accuracy,
    score_status,
    trace_score,
)


def test_classification_and_evidence_scores() -> None:
    assert macro_f1(["fire", "non_fire"], ["fire", "fire"], ["fire", "non_fire"]) == 1 / 3
    assert evidence_f1({"obs_a", "obs_b"}, {"obs_b", "obs_c"}) == 0.5


def test_pair_and_trace_scores_use_explicit_units() -> None:
    assert pair_ranking_accuracy(["a", "b"], ["a", "a"]) == 0.5
    gold = {"initial_state": {"x": 1}, "mechanism_chain": ["ceiling_jet"], "transitions": [], "outcome": {"risk": "high"}}
    assert trace_score(gold, gold) == 1.0


def test_bootstrap_is_reproducible_and_failures_are_scored() -> None:
    assert bootstrap_mean_ci([0.0, 1.0, 1.0], seed=7, resamples=100) == bootstrap_mean_ci([0.0, 1.0, 1.0], seed=7, resamples=100)
    assert score_status("invalid_json") == 0.0
    assert score_status("ok") == 1.0
