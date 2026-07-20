"""Read-only integrity checks for the accepted FDS Core release."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_fds_core(release: Path) -> dict[str, Any]:
    manifest = json.loads((release / "release_manifest.json").read_text(encoding="utf-8"))
    errors = []
    if manifest.get("status") != "formally_accepted": errors.append("status is not formally_accepted")
    if manifest.get("events") != 180: errors.append("events is not 180")
    if manifest.get("qa_total") != 4039: errors.append("qa_total is not 4039")
    for ref, expected in sorted(manifest.get("files", {}).items()):
        path = release / ref
        if not path.is_file(): errors.append(f"missing manifest file: {ref}")
        elif _sha256(path) != expected: errors.append(f"hash mismatch: {ref}")
    questions = json.loads((release / "public/qa_test_questions.json").read_text(encoding="utf-8"))
    if any(row.get("answer") != {"choice": None, "fields": {}} for row in questions):
        errors.append("public test questions expose a non-redacted answer")
    return {
        "ok": not errors,
        "errors": errors,
        "snapshot_id": manifest.get("snapshot_id"),
        "events": manifest.get("events"),
        "qa_total": manifest.get("qa_total"),
        "files_checked": len(manifest.get("files", {})),
    }


