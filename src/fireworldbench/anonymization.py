"""Guarded double-blind and redistribution-license audit."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ANON_VERSION = "P7-ANON-001"
TEXT_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".csv", ".toml", ".yaml", ".yml", ".tex"}
PATTERNS = {
    "absolute_path": re.compile(r"(?:[A-Za-z]:\\|\\\\|/(?:home|Users|mnt)/)"),
    "private_url": re.compile(r"https?://[^\s]+"),
    "secret": re.compile(r"(?:sk-[A-Za-z0-9_-]{12,}|BEGIN (?:RSA |EC )?PRIVATE KEY|api[_-]?key\s*[:=])", re.I),
    "git_metadata": re.compile(r"(?:\.git(?:/|\\)|refs/heads/|git@[^\s:]+:)", re.I),
    "test_gold": re.compile(r"(?:test[_-]?gold|private[_-]?mapping|source_case_key|restricted_run)", re.I),
    "identity": re.compile(r"(?:\\Users\\[^\\/\s]+|/home/[^/\s]+|author\s*[:=]|authors?\s*[:=])", re.I),
}


def _scan_root(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    findings: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        content = path.read_text(encoding="utf-8", errors="replace")
        digest.update(relative.encode("utf-8"))
        digest.update(content.encode("utf-8"))
        assets.append({"path": relative, "classification": "REVIEW_REQUIRED"})
        for line_number, line in enumerate(content.splitlines(), start=1):
            for category, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append({"category": category, "path": relative, "line": line_number})
    return findings, assets, digest.hexdigest()


def assess_anonymization(export_root: Path | None = None) -> dict[str, Any]:
    blockers: list[str] = []
    findings: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    source_sha256: str | None = None
    if export_root is None:
        blockers.append("paper_export_missing")
    else:
        findings, assets, source_sha256 = _scan_root(export_root)
        if findings:
            blockers.append("identity_or_secret_findings")
        blockers.append("third_party_license_declaration_required")
    return {
        "anonymization_version": ANON_VERSION,
        "status": "READY_ANON_PACKAGE" if not blockers else "BLOCKED_NO_EXPORT",
        "blockers": blockers,
        "scanned_export_root": str(export_root) if export_root is not None else None,
        "source_tree_sha256": source_sha256,
        "findings": findings,
        "public_assets": [],
        "excluded_assets": assets,
        "third_party_declaration": {
            "status": "UNRESOLVED",
            "redistributable": None,
            "licenses": [],
            "source_versions": [],
        },
        "anonymous_package": None,
        "test_access_ledger": "NO_ACCESS_CONFIRMED",
        "test_asset_read": False,
    }


def write_anonymization_decision(output_path: Path, export_root: Path | None = None) -> dict[str, Any]:
    result = assess_anonymization(export_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
