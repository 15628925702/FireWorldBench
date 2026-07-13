from __future__ import annotations

from fireworldbench.scorer import score_samples


LABELS = {
    "T1-A": "fire_forming", "T1-B": "fire", "T1-C": "stop_and_decide",
    "T2-A": "growth", "T2-B": "backlayering", "T2-C": "consistent",
    "T3-A": "increase", "T3-B": "case_a_higher_risk", "T3-C": "trace_supported",
}


def sample(task: str, index: int) -> dict:
    label = LABELS[task]
    answer = {"label": label}
    if task == "T1-C":
        answer.update({"selected_observation_id_or_stop": "stop", "query_cost": 0, "expected_information_value": 0.0})
    if task == "T3-A":
        answer.update({"horizon_s": 30.0, "target_variable": "temperature", "trend_label": label, "interval_or_range": {}})
    if task == "T3-B":
        answer.update({"pair_id": "pair_1", "intervention_variable": "ventilation", "direction": "closed_vs_open", "causal_chain": []})
    if task == "T3-C":
        answer.update({"initial_state": {}, "mechanism_chain": ["backlayering"], "transitions": [], "outcome": {}})
    intervention = {"single_variable": True} if task == "T3-B" else None
    return {
        "schema_version": "2.0", "sample_id": f"FWB-v1-{task}-case_{index}-x", "benchmark_version": "v1", "task": task, "split": "dev_id",
        "scenario": {"case_uid": f"case_{index}", "domain": "fire_physics", "family_uid": "family_1", "intervention": intervention},
        "observations": [{"observation_id": f"obs_{index}", "modality": "sensor_table", "time_range_s": [0, 10], "content_ref": "fixture.csv", "units": {"time": "s"}, "quality": "valid"}],
        "question": {"format": "structured_json", "prompt": "Use the observation."}, "answer": answer,
        "physical_trace": {"initial_state": answer.get("initial_state", {}), "mechanism_chain": answer.get("mechanism_chain", []), "transitions": answer.get("transitions", []), "outcome": answer.get("outcome", {}), "evidence_links": [f"obs_{index}"], "origin": ["deterministic_rule"]},
        "scoring_metadata": {"visibility": "private", "gold_ref": f"gold_{index}", "metric_profile": task},
        "provenance": {"source_id": "D01", "source_version": "fixture", "parent_manifest_sha256": "a" * 64, "builder_version": "fixture", "config_sha256": "b" * 64, "annotation_status": "automatic"},
    }


def prediction(gold: dict, *, evidence: list[str] | None = None) -> dict:
    return {"schema_version": "2.0", "sample_id": gold["sample_id"], "task": gold["task"], "answer": gold["answer"], "evidence": evidence or [gold["observations"][0]["observation_id"]], "uncertainty": {"level": "medium", "reason": "fixture"}, "missing_information": []}


def test_scorer_covers_all_nine_tasks_and_keeps_metrics_separate() -> None:
    samples = [sample(task, index) for index, task in enumerate(LABELS, start=1)]
    predictions = {item["sample_id"]: prediction(item) for item in samples}

    result = score_samples(samples, predictions)

    assert set(result["task_metrics"]) == set(LABELS)
    assert all(value["n_samples"] == 1 for value in result["task_metrics"].values())
    assert result["composite_score"]["enabled"] is False
    assert result["failure_counts"] == {}


def test_scorer_retains_failures_and_marks_unknown_evidence() -> None:
    good = sample("T1-A", 1)
    missing = sample("T2-A", 2)
    result = score_samples([good, missing], {good["sample_id"]: prediction(good, evidence=["obs_unknown"])})

    assert result["sample_scores"][0]["evidence_f1"] == 0.0
    assert "V_EVIDENCE" in result["sample_scores"][0]["violations"]
    assert result["failure_counts"] == {"invalid_prediction": 1, "missing_prediction": 1}
    assert result["case_aggregates"]["case_1"] == 1.0
