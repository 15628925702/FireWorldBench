"""Formal visual-baseline decision for the current resource boundary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

VISION_VERSION = "P4-BASELINE-VISION"
ALLOWED_SPLITS = {"train_id", "dev_id"}
PROTECTED_PATH_PARTS = {"private", "test", "test_gold", "test_input", "gold"}


def _assert_safe_path(path: Path) -> None:
    parts = {part.casefold() for part in path.parts}
    blocked = sorted(parts & PROTECTED_PATH_PARTS)
    if blocked:
        raise PermissionError(f"visual baseline refuses protected path component(s): {blocked}")


def assess_visual_baseline(
    samples: Sequence[Mapping[str, Any]],
    *,
    visual_root: Path | None = None,
) -> dict[str, Any]:
    """Return a reproducible N/A decision until approved visual resources exist.

    The function deliberately does not inspect ``visual_root``. A future visual
    implementation must provide approved assets and annotations before metrics
    can be computed, and test/private resources must remain unreachable here.
    """

    if visual_root is not None:
        _assert_safe_path(visual_root)
    if any(sample.get("split") not in ALLOWED_SPLITS for sample in samples):
        raise ValueError("visual baseline only permits train_id or dev_id")
    return {
        "baseline_version": VISION_VERSION,
        "status": "N/A",
        "reason": "no_approved_visual_dataset_or_task_required_visual_input",
        "sample_count": len(samples),
        "detection_metrics": None,
        "physical_reasoning_metrics": None,
        "region_slices": [],
        "interference_slices": [],
        "resource_gaps": [
            "approved_visual_dataset",
            "visual_region_annotations",
            "interference_annotation_protocol",
            "visual_baseline_runtime",
        ],
        "claims_forbidden": [
            "visual_detection_accuracy_is_not_physical_reasoning",
            "N/A_must_not_be_reported_as_zero_accuracy",
            "no_visual_result_without_approved_assets_and_annotations",
        ],
        "test_asset_read": False,
    }


def write_visual_decision(output_path: Path, result: Mapping[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def assess_visual_baseline_file(
    output_path: Path,
    *,
    samples_path: Path | None = None,
    visual_root: Path | None = None,
) -> dict[str, Any]:
    samples: list[Mapping[str, Any]] = []
    if samples_path is not None:
        _assert_safe_path(samples_path)
        payload = json.loads(samples_path.read_text(encoding="utf-8"))
        samples_payload = payload.get("samples", payload) if isinstance(payload, Mapping) else payload
        if not isinstance(samples_payload, list):
            raise TypeError("visual samples must be a JSON list or an object with a samples list")
        samples = samples_payload
    result = assess_visual_baseline(samples, visual_root=visual_root)
    write_visual_decision(output_path, result)
    return result
