from __future__ import annotations

import json
from pathlib import Path

from fireworldbench import schema_validation  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]


def test_split_groups_are_disjoint() -> None:
    config = json.loads((ROOT / "configs" / "split_P2-SPLIT-001.json").read_text(encoding="utf-8"))
    assignments = [group for groups in config["assignments"].values() for group in groups]
    assert len(assignments) == len(set(assignments))


def test_split_manifest_covers_all_assigned_groups() -> None:
    config = json.loads((ROOT / "configs" / "split_P2-SPLIT-001.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "项目治理" / "split_groups_P2-SPLIT-001.json").read_text(encoding="utf-8"))
    assigned = {group for groups in config["assignments"].values() for group in groups}
    assert assigned == {item["group_id"] for item in manifest["groups"]}


def test_ood_gates_are_explicit() -> None:
    config = json.loads((ROOT / "configs" / "split_P2-SPLIT-001.json").read_text(encoding="utf-8"))
    assert config["axes"]["ventilation"]["status"] == "BLOCKED"
    assert config["axes"]["hrr"]["status"] == "BLOCKED"
    assert config["gates"]["ratio_8_1_1_forbidden"] is True
