"""Opaque ID generation and release leakage scanning for P2-LEAK-001."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from pathlib import Path
from typing import Any


PUBLIC_ID_RE = re.compile(r"^FWB-v[0-9]+-T[123]-[ABC]-(train_id|dev_id|test_id|test_ood_[a-z_]+)-[a-f0-9]{16}$")
FORBIDDEN_KEYS = {"gold", "gold_ref", "physical_trace", "scoring_metadata", "source_case_key", "private_salt", "reverse_mapping"}


def make_opaque_id(benchmark_version: str, task: str, split: str, private_key: str, private_case_key: str) -> str:
    """Create a public ID without exposing the private case key or key material."""
    message = f"{benchmark_version}|{task}|{split}|{private_case_key}".encode("utf-8")
    digest = hmac.new(private_key.encode("utf-8"), message, hashlib.sha256).hexdigest()[:16]
    return f"FWB-{benchmark_version}-{task}-{split}-{digest}"


def _walk(value: Any, path: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            found.append((child_path, key))
            found.extend(_walk(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_walk(child, f"{path}[{index}]"))
    return found


def scan_public_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sample_id = payload.get("sample_id")
    if not isinstance(sample_id, str) or not PUBLIC_ID_RE.fullmatch(sample_id):
        errors.append("sample_id is not an opaque public ID")
    for path, key in _walk(payload):
        if key in FORBIDDEN_KEYS:
            errors.append(f"forbidden private field: {path}")
        if isinstance(payload.get(key), str) and (":" in payload[key] or "\\" in payload[key]):
            errors.append(f"path-like metadata in public payload: {path}")
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    for token in ("immersed-tunnel", "polyufire", "dfire", "detectiumfire", "70u01", "130m08"):
        if token in serialized:
            errors.append(f"raw source answer token in public payload: {token}")
    return sorted(set(errors))


def main() -> None:
    if not os.environ.get("FWB_PRIVATE_ID_SALT"):
        print(json.dumps({"status": "BLOCKED", "reason": "FWB_PRIVATE_ID_SALT is intentionally not present in normal development"}))
        return
    print(make_opaque_id("v1", "T1-A", "dev_id", os.environ["FWB_PRIVATE_ID_SALT"], "private-case-key"))


if __name__ == "__main__":
    main()
