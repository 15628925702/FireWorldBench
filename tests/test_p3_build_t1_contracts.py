from __future__ import annotations

from fireworldbench.schema_validation import validate_sample
from fireworldbench.t1_builder import build_t1


def canonical(case_id: str = "case_a", *, fire_label: str | None = "fire_forming") -> list[dict]:
    rows = []
    for index, time_s in enumerate((0.0, 10.0), start=1):
        variables = {"temperature": 300.0 + index, "fire_label": fire_label}
        rows.append({
            "source_dataset_id": "D01", "source_relative_path": "records.csv", "source_sha256": "a" * 64,
            "source_row_index": index, "case_id": case_id, "sequence_id": "seq_1", "time_value_l0": time_s,
            "time_unit_l0": "s", "variables_l0": variables, "units_l0": {"temperature": "K"},
            "canonical_values": {"time_s": time_s, "temperature": 300.0 + index}, "conversion_trace": {"time": {"status": "PASS"}},
            "status": "PASS",
        })
    return rows


def test_t1_builds_three_schema_valid_samples_and_no_future_leak() -> None:
    result = build_t1(canonical(), split="dev_id")

    assert result["sample_count"] == 3
    assert result["test_samples_generated"] is False
    assert all(validate_sample(sample) == [] for sample in result["samples"])
    assert result["samples"][0]["answer"]["label"] == "fire_forming"
    assert all(max(item["time_range_s"][1] for item in sample["observations"]) <= 10.0 for sample in result["samples"])


def test_t1_unknown_signal_is_explicit_refusal() -> None:
    result = build_t1(canonical(fire_label=None), split="train_id")
    labels = {sample["task"]: sample["answer"]["label"] for sample in result["samples"]}

    assert labels["T1-A"] == "insufficient_information"
    assert labels["T1-B"] == "insufficient_information"


def test_t1_refuses_test_split_and_unapproved_thresholds() -> None:
    try:
        build_t1(canonical(), split="test_id")
    except ValueError as exc:
        assert "test construction" in str(exc)
    else:
        raise AssertionError("test split must be refused")
    try:
        build_t1(canonical(), thresholds={"fire": 0.5}, threshold_source="test")
    except ValueError as exc:
        assert "train or calibration" in str(exc)
    else:
        raise AssertionError("unapproved threshold source must be refused")
