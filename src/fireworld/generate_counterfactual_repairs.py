"""Materialize stronger, provenance-preserving counterfactual repair pairs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from fireworld.generate_production_batch import input_text
from fireworld.mini_pilot import write_json

VERSION = "counterfactual-repair-v3.0.0"


def repaired_row(row: dict[str, Any]) -> dict[str, Any]:
    """Keep every frozen control except the declared A/B intervention magnitude."""
    result = json.loads(json.dumps(row))
    intervention = result["intervention"]
    if intervention["variable"] != "hrrpua":
        raise ValueError(f"unsupported repair variable: {intervention['variable']}")
    value = 300.0 if intervention["side"] == "A" else 2500.0
    result["hrrpua"] = value
    intervention["value"] = value
    return cast(dict[str, Any], result)


def build(root: Path) -> Path:
    matrix = json.loads((root / "splits" / "production_matrix.v2.1.json").read_text())
    repair = json.loads(
        (root / "reports" / "protocol_rebuild_v3_counterfactual_repair_queue.json").read_text()
    )
    queued = {event_id for item in repair["items"] for event_id in item["event_ids"]}
    rows = [row for row in matrix["rows"] if row["event_id"] in queued]
    if len(rows) != 16:
        raise ValueError(f"expected 16 repair rows, found {len(rows)}")
    output = root / "fds_runs" / "counterfactual_repair_v3"
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"repair directory already populated: {output}")
    output.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for _ordinal, original in enumerate(sorted(rows, key=lambda row: row["event_id"]), 1):
        row = repaired_row(original)
        family = row["counterfactual_family"].replace("FWCF-", "").lower()
        side = row["intervention"]["side"].lower()
        run_key = f"repair_{family}_{side}"
        run = output / run_key
        run.mkdir()
        (run / f"{run_key}.fds").write_text(input_text(row, run_key), encoding="utf-8")
        manifest.append(
            {
                "run_key": run_key,
                "event_id": row["event_id"],
                "event_group": row["event_group"],
                "split": row["split"],
                "counterfactual_family": row["counterfactual_family"],
                "matrix_row": row,
                "replaces": {
                    "matrix_version": "production_matrix.v2.1.json",
                    "reason": "counterfactual difference below frozen minimum",
                    "previous_intervention_value": original["intervention"]["value"],
                },
            }
        )
    path = output / "input_manifest.json"
    write_json(
        path,
        {
            "schema_version": "3.0.0",
            "builder_version": VERSION,
            "batch": "counterfactual_repair_v3",
            "fds_version": "6.11.1",
            "runs": manifest,
        },
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.root.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
