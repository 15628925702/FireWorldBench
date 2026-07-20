"""Generate the frozen, non-executing 20-event pilot manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SEED = 20260717
CLASSES = (
    ("fire",) * 14
    + ("no_fire_normal",) * 2
    + ("ventilation_disturbance",) * 2
    + ("non_fire_disturbance",) * 2
)


def opaque(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode()).hexdigest()[:12].upper()
    return f"{prefix}-{digest}"


def build() -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    for index, event_class in enumerate(CLASSES, 1):
        base = f"pilot-{index:02d}"
        cf_index = (index - 17) // 2 + 1 if index > 16 else None
        group = opaque("FWG", base if cf_index is None else f"pilot-cf-{cf_index}")
        events.append(
            {
                "event_id": opaque("FWE", base),
                "event_group": group,
                "event_class": event_class,
                "counterfactual_family": None if cf_index is None else f"cf-{cf_index:02d}",
                "geometry": "tunnel_a" if index % 2 else "room_a",
                "source_region": f"R{(index - 1) % 4 + 1}" if event_class == "fire" else None,
                "hrr_profile": ("low_growth", "medium_growth", "high_growth")[(index - 1) % 3]
                if event_class == "fire"
                else None,
                "ventilation_mode": ("still", "longitudinal", "extraction")[(index - 1) % 3],
                "random_seed": SEED + index,
                "status": "planned_not_generated",
            }
        )
    return {
        "schema_version": "2.0.0",
        "status": "dry_run_only",
        "seed": SEED,
        "event_count": len(events),
        "event_group_split_required": True,
        "counterfactual_family_split_required": True,
        "fds": {
            "version": "TBD_PILOT (official candidate FDS-6.11.1)",
            "smokeview_version": "TBD_PILOT (official candidate SMV-6.11.2)",
            "fdgen_version": "TBD_PILOT",
            "mesh": "TBD_PILOT",
            "boundary_conditions": "TBD_PILOT",
            "simulation_duration_s": [90, 120],
            "device_output_interval_s": 1,
            "region_slice_interval_s": 2,
        },
        "tracks": {"required": ["S", "I"], "video": "optional_cost_probe"},
        "expert_blockers": [
            "stage_boundary_buffer",
            "risk_thresholds",
            "trend_dead_band",
            "event_time_tie_tolerance",
            "counterfactual_same_tolerance",
        ],
        "resource_budget": {
            "cpu_quota": "1 vCPU",
            "pilot_wall_time": "TBD after one measured FDS run",
            "raw_storage_gb": "0.5-20 (TBD after one measured FDS run)",
            "derived_storage_gb": "0.1-2 (TBD after one measured FDS run)",
        },
        "events": events,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote dry-run manifest: {args.output} ({len(CLASSES)} events; no simulation started)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
