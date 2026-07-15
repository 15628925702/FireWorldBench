"""Build and assess small train/dev quasi-experiment bundles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

TASKS = ("T1-A", "T1-B", "T1-C", "T2-A", "T2-B", "T2-C", "T3-A", "T3-B", "T3-C")
ALLOWED_SPLITS = {"train_id", "dev_id"}
QUASI_VERSION = "P5-MAIN-001-QUASI-EXPERIMENT-v1"


def _hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_samples(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    value = payload.get("samples", payload) if isinstance(payload, Mapping) else payload
    if not isinstance(value, list):
        raise TypeError("quasi-experiment input must be a JSON list or object with a samples list")
    return [dict(item) for item in value if isinstance(item, Mapping)]


def build_quasi_experiment_pack(
    train_path: Path,
    dev_path: Path,
    *,
    per_task_per_split: int = 1,
) -> dict[str, Any]:
    if per_task_per_split < 1:
        raise ValueError("per_task_per_split must be positive")
    train = _load_samples(train_path)
    dev = _load_samples(dev_path)
    if any(sample.get("split") not in ALLOWED_SPLITS for sample in train + dev):
        raise ValueError("quasi-experiment pack only permits train_id/dev_id samples")
    selected: list[dict[str, Any]] = []
    coverage: dict[str, dict[str, int]] = {task: {"train_id": 0, "dev_id": 0} for task in TASKS}
    for split_name, source in (("train_id", train), ("dev_id", dev)):
        for task in TASKS:
            matches = [sample for sample in source if sample.get("task") == task and sample.get("split") == split_name]
            chosen = matches[:per_task_per_split]
            selected.extend(chosen)
            coverage[task][split_name] = len(chosen)
    status = "READY"
    blockers: list[str] = []
    for task in TASKS:
        for split_name in ("train_id", "dev_id"):
            if coverage[task][split_name] < per_task_per_split:
                status = "BLOCKED"
                blockers.append(f"{task}:{split_name}:insufficient_samples")
    result = {
        "quasi_version": QUASI_VERSION,
        "status": status,
        "per_task_per_split": per_task_per_split,
        "sample_count": len(selected),
        "task_split_coverage": coverage,
        "samples": selected,
        "source_manifests": {
            "train": str(train_path.as_posix()),
            "dev": str(dev_path.as_posix()),
        },
        "blockers": blockers,
    }
    result["manifest_sha256"] = _hash(result)
    return result


def write_quasi_experiment_pack(
    train_path: Path,
    dev_path: Path,
    output_path: Path,
    *,
    per_task_per_split: int = 1,
) -> dict[str, Any]:
    result = build_quasi_experiment_pack(train_path, dev_path, per_task_per_split=per_task_per_split)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def assess_quasi_calibration(
    pack_path: Path,
    probe_paths: list[Path],
) -> dict[str, Any]:
    pack = json.loads(pack_path.read_text(encoding="utf-8-sig"))
    if not isinstance(pack, Mapping):
        raise TypeError("quasi-experiment pack must be a JSON object")
    samples = pack.get("samples", [])
    if not isinstance(samples, list):
        raise TypeError("quasi-experiment pack samples must be a list")
    train_count = sum(1 for sample in samples if isinstance(sample, Mapping) and sample.get("split") == "train_id")
    dev_count = sum(1 for sample in samples if isinstance(sample, Mapping) and sample.get("split") == "dev_id")
    probes: list[dict[str, Any]] = []
    blockers: list[str] = []
    for path in probe_paths:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, Mapping):
            raise TypeError(f"probe payload is not a JSON object: {path}")
        probes.append(dict(payload))
        if payload.get("status") != "PROBE_PASSED":
            blockers.append(f"{path.name}:probe_not_passed")
    if train_count == 0 or dev_count == 0:
        blockers.append("train_and_dev_both_required")
    result = {
        "quasi_version": QUASI_VERSION,
        "status": "READY" if not blockers else "BLOCKED",
        "pack_path": str(pack_path.as_posix()),
        "pack_sha256": pack.get("manifest_sha256"),
        "train_count": train_count,
        "dev_count": dev_count,
        "models": [
            {
                "model_id": probe.get("model_id"),
                "probe_status": probe.get("status"),
                "probe_path": str(path.as_posix()),
            }
            for probe, path in zip(probes, probe_paths, strict=False)
        ],
        "blockers": blockers,
    }
    result["manifest_sha256"] = _hash(result)
    return result


def write_quasi_calibration(
    pack_path: Path,
    probe_paths: list[Path],
    output_path: Path,
) -> dict[str, Any]:
    result = assess_quasi_calibration(pack_path, probe_paths)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
