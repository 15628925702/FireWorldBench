from __future__ import annotations

from fireworldbench.expert import consistency_report, validate_annotation


def annotation(sample_id: str, annotator_id: str, label: str, evidence: list[str]) -> dict:
    return {"sample_id": sample_id, "task": "T1-A", "annotator_id": annotator_id, "label": label, "evidence": evidence, "uncertainty": {"level": "medium", "reason": "calibration"}, "status": "independent"}


def test_two_rater_agreement_and_adjudication_queue() -> None:
    result = consistency_report([annotation("cal_1", "rater_a", "fire_forming", ["obs_1"]), annotation("cal_1", "rater_b", "not_fire_forming", ["obs_2"])])

    assert result["paired_sample_count"] == 1
    assert result["label_agreement"] == 0.0
    assert result["adjudication_required"] == ["cal_1"]
    assert result["expert_gate"] == "BLOCKED_UNTIL_TWO_DOMAIN_RATERS"


def test_invalid_annotation_is_reported_without_silent_drop() -> None:
    bad = annotation("cal_1", "model", "not_a_label", [])

    assert validate_annotation(bad)
    result = consistency_report([bad])
    assert result["invalid_annotation_count"] == 1
