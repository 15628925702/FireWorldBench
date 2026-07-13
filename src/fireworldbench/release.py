"""Reproducible MVP RC1 public/private package builder."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Mapping

RELEASE_VERSION = "P3-MVP-RC1-001"
PRIVATE_FIELDS = {"scoring_metadata"}


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _public_sample(sample: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in sample.items() if key not in PRIVATE_FIELDS}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _package_manifest(root: Path, package: str) -> dict[str, Any]:
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "manifest.json" and path.name != "checksums.sha256":
            files.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": _sha256(path)})
    return {"release_version": RELEASE_VERSION, "package": package, "files": files, "test_gold_included": False, "model_rankings_included": False}


def _finalize_package(root: Path, package: str) -> None:
    manifest = _package_manifest(root, package)
    _write_json(root / "manifest.json", manifest)
    lines = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "checksums.sha256":
            lines.append(f"{_sha256(path)}  {path.relative_to(root).as_posix()}")
    (root / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_mvp_rc1(input_path: Path, output_root: Path) -> dict[str, Any]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    samples = payload.get("samples", payload) if isinstance(payload, Mapping) else payload
    if not isinstance(samples, list):
        raise ValueError("release input must contain a samples list")
    if output_root.exists():
        shutil.rmtree(output_root)
    public_root = output_root / "public"
    private_root = output_root / "private"
    public_root.mkdir(parents=True)
    private_root.mkdir(parents=True)
    public_samples = [_public_sample(sample) for sample in samples]
    private_metadata = [{"sample_id": sample.get("sample_id"), "scoring_metadata": sample.get("scoring_metadata")} for sample in samples if sample.get("scoring_metadata")]
    _write_json(public_root / "samples_public.json", {"release_version": RELEASE_VERSION, "samples": public_samples})
    _write_json(private_root / "scoring_metadata.json", {"release_version": RELEASE_VERSION, "status": "NO_TEST_GOLD_INCLUDED", "items": private_metadata})
    card = {"benchmark": "FireWorldBench", "release_id": "mvp-rc1", "release_version": RELEASE_VERSION, "scope": "benchmark smoke and schema validation only", "sample_count": len(samples), "test_gold_included": False, "private_id_mapping_included": False, "model_rankings_included": False, "rebuild_command": "fwb mvp-build --input <frozen_samples.json> --output <release_root>"}
    _write_json(public_root / "benchmark_card.json", card)
    (public_root / "README.md").write_text("# FireWorldBench MVP RC1\n\nThis package contains public benchmark sample fields only. Test gold, private ID mapping, and model rankings are excluded.\n", encoding="utf-8")
    (private_root / "README.md").write_text("# FireWorldBench MVP RC1 private metadata\n\nThis local package contains explicit scoring metadata only; no test gold or private ID mapping is included.\n", encoding="utf-8")
    _finalize_package(public_root, "public")
    _finalize_package(private_root, "private")
    return {"release_version": RELEASE_VERSION, "sample_count": len(samples), "public_root": public_root.as_posix(), "private_root": private_root.as_posix(), "test_gold_included": False}
