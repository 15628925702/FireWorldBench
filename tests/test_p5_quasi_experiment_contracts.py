from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.quasi_experiment import build_quasi_experiment_pack, assess_quasi_calibration


def _sample(task: str, split: str, suffix: str) -> dict:
    return {
        "schema_version": "2.0",
        "sample_id": f"FWB-v1-{task}-case_{suffix}-x",
        "benchmark_version": "0.1.0",
        "task": task,
        "split": split,
        "scenario": {"case_uid": f"case_{suffix}", "domain": "fire_physics", "family_uid": f"family_{suffix}", "intervention": None},
        "observations": [{"observation_id": f"obs_{suffix}", "modality": "sensor_table", "time_range_s": [0, 1], "content_ref": "fixture.csv", "units": {"time": "s"}, "quality": "valid"}],
        "question": {"format": "structured_json", "prompt": "fixture"},
        "answer": {"label": "fire_forming"},
        "physical_trace": {"initial_state": {}, "mechanism_chain": [], "transitions": [], "outcome": {}, "evidence_links": [f"obs_{suffix}"], "origin": ["deterministic_rule"]},
        "scoring_metadata": {"visibility": "private", "gold_ref": f"gold_{suffix}", "metric_profile": task},
        "provenance": {"source_id": "D01", "source_version": "fixture", "parent_manifest_sha256": "a" * 64, "builder_version": "fixture", "config_sha256": "b" * 64, "annotation_status": "automatic"},
    }


def test_quasi_pack_requires_train_and_dev_task_coverage(tmp_path: Path) -> None:
    train = tmp_path / "train.json"
    dev = tmp_path / "dev.json"
    train.write_text(json.dumps({"samples": [_sample("T1-A", "train_id", "1")]}), encoding="utf-8")
    dev.write_text(json.dumps({"samples": [_sample("T1-A", "dev_id", "2")]}), encoding="utf-8")
    result = build_quasi_experiment_pack(train, dev, per_task_per_split=1)
    assert result["status"] == "BLOCKED"
    assert "T1-B:train_id:insufficient_samples" in result["blockers"]


def test_quasi_calibration_ready_when_pack_and_probes_are_ready(tmp_path: Path) -> None:
    pack = tmp_path / "pack.json"
    pack.write_text(
        json.dumps(
            {
                "samples": [_sample("T1-A", "train_id", "1"), _sample("T1-A", "dev_id", "2")],
                "manifest_sha256": "c" * 64,
            }
        ),
        encoding="utf-8",
    )
    probe_a = tmp_path / "probe_a.json"
    probe_b = tmp_path / "probe_b.json"
    probe_a.write_text(json.dumps({"model_id": "m1", "status": "PROBE_PASSED"}), encoding="utf-8")
    probe_b.write_text(json.dumps({"model_id": "m2", "status": "PROBE_PASSED"}), encoding="utf-8")
    result = assess_quasi_calibration(pack, [probe_a, probe_b])
    assert result["status"] == "READY"
    assert result["train_count"] == 1
    assert result["dev_count"] == 1
