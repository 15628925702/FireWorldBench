from __future__ import annotations

import json
from pathlib import Path

from scripts import build_transfer_manifest, verify_transfer_manifest


def test_transfer_manifest_excludes_caches_and_verifies(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    keep = workspace / "2.方案研究" / "core.pdf"
    keep.parent.mkdir(parents=True)
    keep.write_bytes(b"core")
    cache = workspace / ".pytest_cache" / "cache.bin"
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"ignored")
    output = workspace / "migration" / "transfer_manifest.json"

    assert (
        build_transfer_manifest.main(["--workspace-root", str(workspace), "--output", str(output)])
        == 0
    )
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert [record["path"] for record in manifest["files"]] == ["2.方案研究/core.pdf"]
    assert (
        verify_transfer_manifest.main(
            ["--workspace-root", str(workspace), "--manifest", str(output)]
        )
        == 0
    )

    keep.write_bytes(b"changed")
    assert (
        verify_transfer_manifest.main(
            ["--workspace-root", str(workspace), "--manifest", str(output)]
        )
        == 1
    )
