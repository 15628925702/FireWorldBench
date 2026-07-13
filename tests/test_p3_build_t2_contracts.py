from __future__ import annotations

from fireworldbench.schema_validation import validate_sample
from fireworldbench.t2_builder import build_t2


def canonical(*, state: str | None = "growth", mechanism: str | None = "backlayering", consistency: str | None = "consistent", violations: str | None = None) -> list[dict]:
    rows = []
    for index, time_s in enumerate((0.0, 10.0), start=1):
        variables = {"temperature": 300.0 + index}
        if state is not None:
            variables["state_label"] = state
        if mechanism is not None:
            variables["mechanism_labels"] = mechanism
        if consistency is not None:
            variables["consistency_label"] = consistency
        if violations is not None:
            variables["violation_codes"] = violations
        rows.append({
            "source_dataset_id": "D01", "source_relative_path": "records.csv", "source_sha256": "b" * 64,
            "source_row_index": index, "case_id": "case_t2", "sequence_id": "seq_1", "time_value_l0": time_s,
            "time_unit_l0": "s", "variables_l0": variables, "units_l0": {"temperature": "K"},
            "canonical_values": {"time_s": time_s, "temperature": 300.0 + index}, "conversion_trace": {"time": {"status": "PASS"}},
            "status": "PASS",
        })
    return rows


def test_t2_builds_valid_state_mechanism_and_consistency_samples() -> None:
    result = build_t2(canonical(), split="dev_id")

    assert result["sample_count"] == 3
    assert all(validate_sample(sample) == [] for sample in result["samples"])
    labels = {sample["task"]: sample["answer"]["label"] for sample in result["samples"]}
    assert labels == {"T2-A": "growth", "T2-B": "backlayering", "T2-C": "consistent"}


def test_t2_unknowns_are_explicit_and_invalid_consistency_is_underdetermined() -> None:
    result = build_t2(canonical(state=None, mechanism=None, consistency="inconsistent"), split="train_id")
    labels = {sample["task"]: sample["answer"]["label"] for sample in result["samples"]}

    assert labels == {"T2-A": "state_unknown", "T2-B": "mechanism_unknown", "T2-C": "underdetermined"}
    assert all(validate_sample(sample) == [] for sample in result["samples"])


def test_t2_refuses_test_split() -> None:
    try:
        build_t2(canonical(), split="test_id")
    except ValueError as exc:
        assert "test construction" in str(exc)
    else:
        raise AssertionError("test split must be refused")
