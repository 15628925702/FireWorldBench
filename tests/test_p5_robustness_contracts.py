from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.robustness import assess_robustness, build_robustness_manifest, write_robustness_decision


def test_robustness_is_blocked_without_main_run_and_preserves_labels() -> None:
    result = assess_robustness({"status": "BLOCKED", "run_index": []})

    assert result["status"] == "BLOCKED_NO_MAIN_RUN"
    assert len(result["transformations"]) == 6
    assert all(item["label_invariant_required"] for item in result["transformations"])
    assert result["label_change_is_not_robustness_evidence"] is True
    assert result["performance_slices"] == []
    assert result["failure_slices"] == []
    assert result["cost_slices"] == []


def test_robustness_manifest_is_deterministic() -> None:
    assert build_robustness_manifest() == build_robustness_manifest()


def test_robustness_file_is_machine_readable(tmp_path: Path) -> None:
    main_run = tmp_path / "main.json"
    main_run.write_text('{"status": "BLOCKED", "run_index": []}\n', encoding="utf-8")
    output = tmp_path / "robust.json"
    result = write_robustness_decision(main_run, output)
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == result["status"]
