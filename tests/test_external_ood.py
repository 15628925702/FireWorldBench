from __future__ import annotations

import json
from pathlib import Path

from fireworld.external_ood import build_immersed_tunnel_candidates
from fireworld.validation import validate_event_semantics, validate_schema


def test_immersed_builder_only_creates_candidates(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    csv_dir = raw / "immersed_tunnel_mirror" / "CFD-Data"
    csv_dir.mkdir(parents=True)
    (csv_dir / "source_label_must_not_leak.csv").write_text(
        "s,degC,degC\nTime,sensor_a,sensor_b\n0,20,21\n1,21,22\n2,22,23\n",
        encoding="utf-8",
    )
    output = tmp_path / "external_ood"

    result = build_immersed_tunnel_candidates(raw, output)

    assert result == {"raw_files": 1, "parsed": 1, "candidates": 1, "failures": 0}
    event_path = next((output / "events" / "immersed_tunnel").glob("*.json"))
    event = json.loads(event_path.read_text(encoding="utf-8"))
    assert event["status"] == "candidate"
    assert event["ground_truth"]["labels"] == []
    assert "source_label_must_not_leak" not in event_path.read_text(encoding="utf-8")
    assert validate_schema(event, "fire_event.schema.json") == []
    assert validate_event_semantics(event) == []

    report = json.loads(
        (output / "reports" / "immersed_tunnel" / "candidate_ingest_report.json").read_text()
    )
    assert report["formal_qualified_events"] == 0
    assert report["formal_qa"] == 0
