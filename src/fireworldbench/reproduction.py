"""Guarded clean-room reproduction readiness decision."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPRO_VERSION = "P7-REPRO-001"


def _release_info(release_root: Path | None) -> tuple[str | None, bool]:
    if release_root is None:
        return None, False
    readme = release_root / "README.md"
    if not readme.is_file():
        return None, False
    source = readme.read_bytes()
    return hashlib.sha256(source).hexdigest(), True


def assess_reproduction(release_root: Path | None = None) -> dict[str, Any]:
    readme_sha256, has_readme = _release_info(release_root)
    blockers = [
        "paper_release_missing" if release_root is None else "release_readme_missing",
        "clean_environment_not_created",
        "legal_rebuild_inputs_missing",
    ]
    if has_readme:
        blockers.remove("release_readme_missing")
    return {
        "reproduction_version": REPRO_VERSION,
        "status": "READY_TO_REPRODUCE" if not blockers else "BLOCKED_NO_RELEASE_INPUT",
        "blockers": blockers,
        "release_root": str(release_root) if release_root is not None else None,
        "release_readme_sha256": readme_sha256,
        "clean_environment": {
            "created": False,
            "environment_lock": None,
            "packages_installed": False,
            "downloads_performed": False,
        },
        "rebuild_targets": ["benchmark", "representative_baseline", "paper_number_registry"],
        "rebuild_log": [],
        "rebuild_hashes": [],
        "deviations": [],
        "minimum_result_reproduced": False,
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def write_reproduction_decision(output_path: Path, release_root: Path | None = None) -> dict[str, Any]:
    result = assess_reproduction(release_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
