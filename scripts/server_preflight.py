"""Cross-platform preflight checks after moving the FireWorldBench workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_PDF_SHA256 = "ba63ab8428d1f759629a89864af7f623589d023dd6d5a29e4940fc6d629a19a6"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(repo: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def directory_summary(path: Path) -> dict[str, int | bool]:
    if not path.exists():
        return {"exists": False, "files": 0, "bytes": 0}
    files = [item for item in path.rglob("*") if item.is_file()]
    return {
        "exists": True,
        "files": len(files),
        "bytes": sum(item.stat().st_size for item in files),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    workspace = args.workspace_root.resolve()
    repo = workspace / "5.项目实现" / "v1"
    pdf = workspace / "2.方案研究" / "FireWorldBenchv2(1).pdf"
    pdf_hash = sha256(pdf) if pdf.is_file() else None
    usage = shutil.disk_usage(workspace)
    tools = {name: shutil.which(name) for name in ("git", "ffmpeg", "fds", "smokeview", "smv")}
    report: dict[str, Any] = {
        "workspace_root": str(workspace),
        "repo_exists": repo.is_dir(),
        "pdf": {
            "path": str(pdf),
            "exists": pdf.is_file(),
            "sha256": pdf_hash,
            "matches_expected": pdf_hash == EXPECTED_PDF_SHA256,
        },
        "git_head": git_head(repo) if repo.is_dir() else None,
        "python": {"version": sys.version, "executable": sys.executable},
        "tools": tools,
        "disk": {"total": usage.total, "used": usage.used, "free": usage.free},
        "directories": {
            "references": directory_summary(workspace / "1.参考文献"),
            "research_design": directory_summary(workspace / "2.方案研究"),
            "external_datasets": directory_summary(workspace / "3.数据集"),
            "repo_raw": directory_summary(repo / "data" / "raw"),
            "legacy_artifacts": directory_summary(repo / "artifacts"),
        },
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)

    required_ok = repo.is_dir() and pdf_hash == EXPECTED_PDF_SHA256 and tools["git"] is not None
    return 0 if required_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
