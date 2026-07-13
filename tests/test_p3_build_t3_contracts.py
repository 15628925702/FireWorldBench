from __future__ import annotations

from fireworldbench.schema_validation import validate_sample
from fireworldbench.t3_builder import build_t3


def canonical(*, valid_pair: bool = True, valid_trace: bool = True, trend: str | None = "increase") -> list[dict]:
    rows = []
    for case_id, index in (("case_a", 1), ("case_b", 2)):
        variables = {
            "temperature": 300.0 + index, "trend_label": trend, "target_variable": "temperature", "horizon_s": 30.0,
            "pair_id": "pair_1", "pair_valid": valid_pair, "single_variable": valid_pair,
            "pair_label": "case_a_higher_risk", "intervention_variable": "ventilation", "intervention_direction": "closed_vs_open",
        }
        if valid_trace:
            variables.update({"trace_label": "trace_supported", "initial_state": {"state": "forming"}, "mechanism_chain": ["buoyant_plume"], "transitions": [{"from": "forming", "to": "growth"}], "outcome": {"state": "growth"}})
        rows.append({
            "source_dataset_id": "D01", "source_relative_path": "records.csv", "source_sha256": ("c" if case_id == "case_a" else "d") * 64,
            "source_row_index": index, "case_id": case_id, "sequence_id": "seq_1", "time_value_l0": float(index),
            "time_unit_l0": "s", "variables_l0": variables, "units_l0": {"temperature": "K"},
            "canonical_values": {"time_s": float(index), "temperature": 300.0 + index}, "conversion_trace": {"time": {"status": "PASS"}},
            "status": "PASS",
        })
    return rows


def test_t3_builds_valid_trend_pair_and_trace_samples() -> None:
    result = build_t3(canonical(), split="dev_id")

    assert result["sample_count"] == 5
    assert all(validate_sample(sample) == [] for sample in result["samples"])
    labels = {(sample["task"], sample["answer"]["label"]) for sample in result["samples"]}
    assert ("T3-A", "increase") in labels
    assert ("T3-B", "case_a_higher_risk") in labels
    assert ("T3-C", "trace_supported") in labels


def test_t3_invalid_pair_and_missing_horizon_are_explicit() -> None:
    result = build_t3(canonical(valid_pair=False, valid_trace=False, trend=None), split="train_id")
    labels = {(sample["task"], sample["answer"]["label"]) for sample in result["samples"]}

    assert ("T3-A", "trend_unknown") in labels
    assert ("T3-B", "pair_invalid") in labels
    assert ("T3-C", "trace_unknown") in labels
    assert all(validate_sample(sample) == [] for sample in result["samples"])


def test_t3_refuses_test_split() -> None:
    try:
        build_t3(canonical(), split="test_id")
    except ValueError as exc:
        assert "test construction" in str(exc)
    else:
        raise AssertionError("test split must be refused")
