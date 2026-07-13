from __future__ import annotations

import json
from pathlib import Path

from fireworldbench.release import build_mvp_rc1


def test_mvp_build_is_reproducible_and_public_package_excludes_private_fields(tmp_path: Path) -> None:
    sample = {"sample_id": "FWB-v1-T1-A-case_1-x", "task": "T1-A", "answer": {"label": "fire_forming"}, "scoring_metadata": {"visibility": "private", "gold_ref": "gold_1"}}
    source = tmp_path / "samples.json"
    source.write_text(json.dumps({"samples": [sample]}), encoding="utf-8")
    first = tmp_path / "first"
    second = tmp_path / "second"

    build_mvp_rc1(source, first)
    build_mvp_rc1(source, second)

    first_files = sorted(path.relative_to(first).as_posix() for path in first.rglob("*") if path.is_file())
    second_files = sorted(path.relative_to(second).as_posix() for path in second.rglob("*") if path.is_file())
    assert first_files == second_files
    for relative in first_files:
        assert (first / relative).read_bytes() == (second / relative).read_bytes()
    public = json.loads((first / "public/samples_public.json").read_text(encoding="utf-8"))
    assert "scoring_metadata" not in public["samples"][0]
    assert json.loads((first / "public/manifest.json").read_text(encoding="utf-8"))["test_gold_included"] is False


def test_mvp_build_rejects_non_sample_input(tmp_path: Path) -> None:
    source = tmp_path / "bad.json"
    source.write_text(json.dumps({"records": []}), encoding="utf-8")
    try:
        build_mvp_rc1(source, tmp_path / "release")
    except ValueError as exc:
        assert "samples list" in str(exc)
    else:
        raise AssertionError("non-sample input must be rejected")
