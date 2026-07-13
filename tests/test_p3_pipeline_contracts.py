from __future__ import annotations

import json
from pathlib import Path

import pytest

from fireworldbench.pipeline import build_canonical, inventory


def test_pipeline_refuses_protected_asset_root(tmp_path: Path) -> None:
    protected = tmp_path / "test_gold"
    protected.mkdir()

    with pytest.raises(PermissionError, match="test embargo"):
        inventory(protected)


def test_inventory_is_sorted_and_hashes_files(tmp_path: Path) -> None:
    (tmp_path / "b.txt").write_text("ignored", encoding="utf-8")
    (tmp_path / "a.csv").write_text("case_id,time,time_unit,temperature\nc1,100,ms,300\n", encoding="utf-8")

    result = inventory(tmp_path)

    assert result["file_count"] == 2
    assert [item["relative_path"] for item in result["files"]] == ["a.csv", "b.txt"]
    assert result["files"][0]["readable_by_adapter"] is True
    assert len(result["files"][0]["sha256"]) == 64


def test_pipeline_normalizes_time_and_builds_case_graph(tmp_path: Path) -> None:
    source = {"case_id": "case_a", "sequence_id": "seq_1", "time": 500, "time_unit": "ms", "units": {"temperature": "K"}, "temperature": 300}
    (tmp_path / "records.json").write_text(json.dumps([source]), encoding="utf-8")

    result = build_canonical(tmp_path, source_dataset_id="D01")

    assert result["record_count"] == 1
    assert result["failure_count"] == 0
    assert result["inventory"]["file_count"] == 1
    assert result["quality"] == {"pass_records": 1, "blocked_records": 0, "failed_rows": 0}
    assert result["records"][0]["canonical_values"]["time_s"] == 0.5
    assert result["records"][0]["conversion_trace"]["time"]["rule"] == "ms_to_s"
    assert result["case_graph"]["nodes"][0]["case_id"] == "case_a"
    assert result["case_graph"]["edges"][0]["type"] == "contains"


def test_pipeline_retains_bad_rows_and_unknown_units(tmp_path: Path) -> None:
    (tmp_path / "records.jsonl").write_text(
        '{"case_id":"case_a","time":1,"time_unit":"furlong"}\n'
        '{"time":2,"time_unit":"s"}\n',
        encoding="utf-8",
    )

    result = build_canonical(tmp_path, source_dataset_id="D01")

    assert result["record_count"] == 1
    assert result["records"][0]["status"] == "UNKNOWN_UNIT"
    assert result["failure_count"] == 1
    assert result["failures"][0]["code"] == "ROW_INVALID"
