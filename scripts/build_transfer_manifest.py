"""Build a deterministic SHA-256 manifest for the server transfer set."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "tmp",
    "temp",
    "output",
}
EXCLUDED_FILE_NAMES = {"transfer_manifest.json"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def included_files(workspace: Path) -> list[Path]:
    files: list[Path] = []
    for path in workspace.rglob("*"):
        relative = path.relative_to(workspace)
        if any(part in EXCLUDED_DIRECTORY_NAMES for part in relative.parts):
            continue
        if path.is_file() and path.name not in EXCLUDED_FILE_NAMES:
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(workspace).as_posix())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    workspace = args.workspace_root.resolve()
    files = included_files(workspace)
    records: list[dict[str, Any]] = []
    total_bytes = 0
    for path in files:
        size = path.stat().st_size
        total_bytes += size
        records.append(
            {
                "path": path.relative_to(workspace).as_posix(),
                "bytes": size,
                "sha256": sha256(path),
            }
        )
    manifest = {
        "schema_version": "FWB-TRANSFER-1",
        "workspace_layout": "research_workspace_root",
        "excluded_directory_names": sorted(EXCLUDED_DIRECTORY_NAMES),
        "file_count": len(records),
        "total_bytes": total_bytes,
        "files": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(records)} files / {total_bytes} bytes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
