"""Freeze six calibration-run replacements without increasing the 180-event matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

MECHANISMS = (
    ("buoyant_plume", "mechanism_calibration_v3", "MC3_01_buoyant_plume"),
    ("ceiling_jet", "mechanism_calibration_v4", "MC4_01_ceiling_jet"),
    ("smoke_layer", "mechanism_calibration_v3", "MC3_03_smoke_layer"),
    ("longitudinal_ventilation", "mechanism_calibration_v3", "MC3_04_longitudinal_ventilation"),
    ("backlayering", "mechanism_calibration_v3", "MC3_05_backlayering"),
    ("extraction_dominated", "mechanism_calibration_v4", "MC4_02_extraction_dominated"),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    matrix = json.loads((root / "splits" / "production_matrix.v2.1.json").read_text())
    candidates = [
        row
        for row in matrix["rows"]
        if row["status"] == "planned"
        and row["event_class"] == "fire"
        and row["split"] == "train"
        and not row.get("counterfactual_family")
    ]
    if len(candidates) < len(MECHANISMS):
        raise ValueError("insufficient standalone train fire rows for mechanism replacements")
    replacements = []
    for target, (mechanism, calibration_batch, run_key) in zip(
        candidates[: len(MECHANISMS)], MECHANISMS, strict=True
    ):
        replacements.append(
            {
                "target_event_id": target["event_id"],
                "target_event_group": target["event_group"],
                "split": target["split"],
                "replaces_source": f"fire_events/{target['production_batch']}/{target['event_id']}.json",
                "mechanism": mechanism,
                "calibration_fds_run": f"fds_runs/{calibration_batch}/{run_key}",
                "status": "planned_rebuild_not_integrated",
            }
        )
    output = root / "splits" / "mechanism_replacements.v1.json"
    output.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "target_event_count": 180,
                "replacement_count": len(replacements),
                "rule_ref": "reports/mechanism_rule_calibration.v1.json",
                "replacements": replacements,
            },
            indent=2,
        )
        + "\n"
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
