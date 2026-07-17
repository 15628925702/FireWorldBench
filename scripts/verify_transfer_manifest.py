"""Verify a transferred workspace against its SHA-256 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)

    workspace = args.workspace_root.resolve()
    manifest: dict[str, Any] = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors: list[str] = []
    checked_bytes = 0
    for record in manifest["files"]:
        path = workspace / Path(record["path"])
        if not path.is_file():
            errors.append(f"missing: {record['path']}")
            continue
        size = path.stat().st_size
        checked_bytes += size
        if size != record["bytes"]:
            errors.append(f"size mismatch: {record['path']}")
            continue
        if sha256(path) != record["sha256"]:
            errors.append(f"hash mismatch: {record['path']}")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"verified {manifest['file_count']} files / {checked_bytes} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
