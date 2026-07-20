"""Generate deterministic FDS pilot inputs; execution is a separate step."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


EVENT_CLASSES = ("fire",) * 14 + ("no_fire_normal",) * 2 + ("ventilation_disturbance",) * 2 + ("non_fire_disturbance",) * 2
GEOMETRIES = (
    ("tunnel_a", "tunnel", (20.0, 10.0, 5.0)),
    ("tunnel_b", "tunnel", (24.0, 10.0, 5.0)),
    ("room_a", "room", (20.0, 10.0, 5.0)),
    ("room_b", "room", (24.0, 12.0, 5.0)),
)
HRR = (120.0, 250.0, 400.0)
VENT = ("still", "longitudinal", "extraction")


def event_id(index: int) -> str:
    return "FWE-" + hashlib.sha256(f"pilot-{index:02d}".encode()).hexdigest()[:12].upper()


def fds_text(index: int, event_class: str) -> tuple[str, dict[str, Any]]:
    geometry_id, scene_type, dims = GEOMETRIES[(index - 1) % len(GEOMETRIES)]
    length, width, height = dims
    hrr = HRR[(index - 1) % len(HRR)] if event_class == "fire" else 0.0
    vent = VENT[(index - 1) % len(VENT)]
    source_region = (index - 1) % 4
    x = 2.0 + source_region * (length - 4.0) / 3.0
    y = width / 2.0
    lines = [
        f"&HEAD CHID='pilot_{index:02d}', TITLE='FireWorldBench v2 pilot {index:02d}'/>",
        f"&MESH IJK={int(length / 0.5)},{int(width / 0.5)},{int(height / 0.5)}, XB=0.0,{length:.2f},0.0,{width:.2f},0.0,{height:.2f}/>",
        "&TIME T_END=90.0/",
        "&DUMP DT_DEVC=1.0, DT_HRR=1.0, DT_SLCF=2.0/",
        "&SPEC ID='PROPANE'/",
        "&REAC FUEL='PROPANE', SOOT_YIELD=0.015, CO_YIELD=0.005/",
        "&MATL ID='CONCRETE', CONDUCTIVITY=1.4, SPECIFIC_HEAT=0.88, DENSITY=2200.0/",
        "&SURF ID='FLOOR', MATL_ID='CONCRETE', THICKNESS=0.1, COLOR='GRAY'/",
        "&SURF ID='OPEN', COLOR='INVISIBLE'/",
        "&SURF ID='BURNER', HRRPUA=%.1f, COLOR='RED'/" % hrr,
        f"&VENT XB=0.0,{length:.2f},0.0,{width:.2f},0.0,0.0, SURF_ID='FLOOR'/",
        f"&VENT XB=0.0,{length:.2f},0.0,{width:.2f},{height:.2f},{height:.2f}, SURF_ID='OPEN'/",
    ]
    if vent in {"longitudinal", "extraction"}:
        lines.append(f"&VENT XB=0.0,0.0,0.0,{width:.2f},0.0,{height:.2f}, SURF_ID='OPEN'/")
    if vent == "extraction":
        lines.append(f"&VENT XB={length * 0.75:.2f},{length * 0.9:.2f},{width * 0.4:.2f},{width * 0.6:.2f},{height:.2f},{height:.2f}, SURF_ID='OPEN'/")
    if event_class == "fire":
        lines.append(f"&OBST XB={x - 0.5:.2f},{x + 0.5:.2f},{y - 0.5:.2f},{y + 0.5:.2f},0.0,0.5, SURF_ID='BURNER'/")
    for region in range(1, 9):
        rx = min(length - 0.5, 1.0 + (region - 1) % 4 * (length - 2.0) / 3.0)
        ry = width * 0.25 if region <= 4 else width * 0.75
        lines.append(f"&DEVC ID='T_R{region}', XYZ={rx:.2f},{ry:.2f},1.5, QUANTITY='TEMPERATURE'/")
        lines.append(f"&DEVC ID='V_R{region}', XYZ={rx:.2f},{ry:.2f},1.5, QUANTITY='VISIBILITY'/")
    lines.append("&TAIL /")
    metadata = {"event_id": event_id(index), "event_class": event_class, "geometry": geometry_id, "scene_type": scene_type, "source_region": f"R{source_region + 1}" if event_class == "fire" else None, "hrr_profile": ["low_growth", "medium_growth", "high_growth"][(index - 1) % 3] if event_class == "fire" else None, "hrrpua": hrr, "ventilation_mode": vent, "random_seed": 20260717 + index, "status": "planned_not_generated"}
    return "\n".join(lines) + "\n", metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, event_class in enumerate(EVENT_CLASSES, 1):
        text, metadata = fds_text(index, event_class)
        case_dir = args.output / f"pilot_{index:02d}"
        case_dir.mkdir(exist_ok=True)
        (case_dir / f"pilot_{index:02d}.fds").write_text(text, encoding="utf-8")
        (case_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        rows.append(metadata)
    (args.output / "pilot_inputs_manifest.json").write_text(json.dumps({"status": "inputs_generated_not_executed", "event_count": len(rows), "events": rows}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
