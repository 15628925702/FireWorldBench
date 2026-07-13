from __future__ import annotations

from pathlib import Path

from fireworldbench.vision_baseline import assess_visual_baseline, assess_visual_baseline_file


def test_visual_baseline_is_formal_na_without_approved_resources() -> None:
    result = assess_visual_baseline([])

    assert result["status"] == "N/A"
    assert result["detection_metrics"] is None
    assert result["physical_reasoning_metrics"] is None
    assert result["region_slices"] == []
    assert result["interference_slices"] == []
    assert result["test_asset_read"] is False


def test_visual_baseline_keeps_train_dev_boundary_and_does_not_scan_root(tmp_path: Path) -> None:
    result = assess_visual_baseline(
        [{"sample_id": "dev-1", "split": "dev_id", "visual_ref": "unresolved"}],
        visual_root=tmp_path / "future-approved-assets",
    )

    assert result["status"] == "N/A"
    assert result["sample_count"] == 1
    assert not (tmp_path / "future-approved-assets").exists()


def test_visual_baseline_refuses_test_samples_and_protected_paths(tmp_path: Path) -> None:
    try:
        assess_visual_baseline([{"sample_id": "test-1", "split": "test_id"}])
    except ValueError as exc:
        assert "train_id" in str(exc)
    else:
        raise AssertionError("test split must be refused")

    try:
        assess_visual_baseline([], visual_root=tmp_path / "private" / "visuals")
    except PermissionError as exc:
        assert "protected" in str(exc)
    else:
        raise AssertionError("protected visual root must be refused")


def test_visual_baseline_file_writes_machine_readable_na(tmp_path: Path) -> None:
    output = tmp_path / "vision.json"
    result = assess_visual_baseline_file(output)

    assert output.is_file()
    assert result["baseline_version"] == "P4-BASELINE-VISION"
