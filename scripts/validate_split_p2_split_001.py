"""Validate group disjointness and split invariants for P2-SPLIT-001."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    config = json.loads((ROOT / "configs" / "split_P2-SPLIT-001.json").read_text(encoding="utf-8"))
    groups = json.loads((ROOT / "项目治理" / "split_groups_P2-SPLIT-001.json").read_text(encoding="utf-8"))["groups"]
    assigned: dict[str, str] = {}
    for split, group_ids in config["assignments"].items():
        for group_id in group_ids:
            if group_id in assigned:
                raise SystemExit(f"group appears in multiple splits: {group_id}")
            assigned[group_id] = split
    known = {group["group_id"] for group in groups}
    if set(assigned) != known:
        raise SystemExit(f"assignment/group mismatch: assigned={sorted(assigned)} known={sorted(known)}")
    for group in groups:
        if group["assigned_split"] != assigned[group["group_id"]]:
            raise SystemExit(f"manifest split mismatch: {group['group_id']}")
    case_keys = {}
    for group in groups:
        for case_key in group["case_keys"]:
            if case_key in case_keys:
                raise SystemExit(f"case appears in multiple groups: {case_key}")
            case_keys[case_key] = group["group_id"]
    print(json.dumps({"groups": len(groups), "case_keys": len(case_keys), "splits": config["assignments"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
