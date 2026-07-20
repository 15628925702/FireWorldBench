"""Materialize a frozen production-matrix batch as explicit-observation FDS runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

GEOMETRIES = {
    "tunnel_a": (20.0, 10.0, 5.0, 40, 20, 10),
    "tunnel_b": (24.0, 8.0, 5.0, 48, 16, 10),
    "room_a": (12.0, 12.0, 4.0, 24, 24, 8),
    "room_b": (16.0, 10.0, 4.0, 32, 20, 8),
    "atrium_ood": (18.0, 18.0, 8.0, 36, 36, 16),
    "corridor_ood": (30.0, 6.0, 4.0, 60, 12, 8),
}


def source_xy(row: dict[str, Any], length: float, width: float) -> tuple[float, float]:
    region = int((row.get("source_region") or "R5")[1:]) - 1
    return ((region % 4 + 0.5) * length / 4, (region // 4 + 0.5) * width / 2)


def input_text(row: dict[str, Any], run_key: str) -> str:
    length, width, height, nx, ny, nz = GEOMETRIES[row["geometry"]]
    x, y = source_xy(row, length, width)
    event_class = row["event_class"]
    hrr = float(row.get("hrrpua", 0.0))
    heater_temperature = float(row.get("heater_temperature_c") or 120.0)
    supply = float(row.get("supply_velocity", 0.0))
    burner = ""
    heater = ""
    if event_class == "fire":
        burner = f"&OBST XB={x - .5:.2f},{x + .5:.2f},{y - .5:.2f},{y + .5:.2f},0.0,0.5, SURF_ID='BURNER'/"
    if event_class == "non_fire_disturbance":
        heater = f"&OBST XB={x - 1:.2f},{x + 1:.2f},{y - 1:.2f},{y + 1:.2f},{height - 1:.2f},{height - .5:.2f}, SURF_ID='HEATER'/"
    inlet_surface = "OPEN" if supply == 0 else "SUPPLY"
    mechanism = str(row.get("mechanism_target") or "")
    extraction = ""
    if mechanism == "extraction_dominated":
        extraction = f"&VENT XB={length * .40:.2f},{length * .60:.2f},{width * .40:.2f},{width * .60:.2f},{height},{height}, SURF_ID='EXHAUST'/"
    top_vent = "" if extraction else f"&VENT XB=0.0,{length},0.0,{width},{height},{height}, SURF_ID='OPEN'/"
    points = [("R1", .125, .25), ("R2", .375, .25), ("R3", .625, .25), ("R4", .875, .25), ("R5", .125, .75), ("R6", .375, .75), ("R7", .625, .75), ("R8", .875, .75)]
    devices: list[str] = []
    for label, px, py in points:
        dx, dy = px * length, py * width
        devices.extend((f"&DEVC ID='T_{label}', XYZ={dx:.2f},{dy:.2f},{height - .5:.2f}, QUANTITY='TEMPERATURE'/", f"&DEVC ID='V_{label}', XYZ={dx:.2f},{dy:.2f},{height - .5:.2f}, QUANTITY='VISIBILITY'/", f"&DEVC ID='U_{label}', XYZ={dx:.2f},{dy:.2f},{height / 2:.2f}, QUANTITY='U-VELOCITY'/", f"&DEVC ID='W_{label}', XYZ={dx:.2f},{dy:.2f},{height / 2:.2f}, QUANTITY='W-VELOCITY'/"))
    return "\n".join(line for line in [
        f"&HEAD CHID='{run_key}', TITLE='FireWorldBench v2.1 production'/",
        f"&MESH IJK={nx},{ny},{nz}, XB=0.0,{length},0.0,{width},0.0,{height}/",
        "&TIME T_END=120.0/", "&DUMP DT_DEVC=1.0, DT_HRR=1.0, DT_SLCF=2.0, DT_SMOKE3D=2.0, SMOKE3D=.TRUE./",
        "&SPEC ID='PROPANE'/", "&REAC FUEL='PROPANE', SOOT_YIELD=0.08, CO_YIELD=0.02/", "&RAMP ID='FIRE_RAMP', T=0.0, F=0.0/", "&RAMP ID='FIRE_RAMP', T=20.0, F=0.25/", "&RAMP ID='FIRE_RAMP', T=50.0, F=1.0/",
        f"&SURF ID='BURNER', HRRPUA={hrr:.1f}, RAMP_Q='FIRE_RAMP', COLOR='RED'/", f"&SURF ID='HEATER', TMP_FRONT={heater_temperature:.1f}, COLOR='YELLOW'/", f"&SURF ID='SUPPLY', VEL={supply:.3f}, COLOR='INVISIBLE'/", "&SURF ID='EXHAUST', VEL=-2.000, COLOR='INVISIBLE'/", "&SURF ID='OPEN', COLOR='INVISIBLE'/",
        f"&VENT XB=0.0,{length},0.0,{width},0.0,0.0, SURF_ID='INERT'/", top_vent, f"&VENT XB=0.0,0.0,0.0,{width},0.0,{height}, SURF_ID='{inlet_surface}'/", f"&VENT XB={length},{length},0.0,{width},0.0,{height}, SURF_ID='OPEN'/", extraction, burner, heater,
        f"&SLCF PBZ={height - .5:.2f}, QUANTITY='TEMPERATURE'/", f"&SLCF PBZ={height - .5:.2f}, QUANTITY='VISIBILITY'/", f"&SLCF PBZ={height - .5:.2f}, QUANTITY='DENSITY', SPEC_ID='SOOT'/", f"&SLCF PBZ={height - .5:.2f}, QUANTITY='U-VELOCITY'/", f"&SLCF PBZ={height - .5:.2f}, QUANTITY='W-VELOCITY'/", "&SM3D QUANTITY='DENSITY', SPEC_ID='SOOT'/", "&SM3D QUANTITY='TEMPERATURE'/", *devices, "&TAIL /",
    ] if line) + "\n"


def build(root: Path, batch: str) -> Path:
    matrix = json.loads((root / "splits" / "production_matrix.v2.1.json").read_text())
    rows = [row for row in matrix["rows"] if row.get("production_batch") == batch]
    if not rows:
        raise ValueError(f"unknown or empty batch: {batch}")
    output = root / "fds_runs" / batch
    output.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        run_key = f"{batch[-2:]}_{index:03d}"
        run = output / run_key
        run.mkdir(exist_ok=True)
        (run / f"{run_key}.fds").write_text(input_text(row, run_key), encoding="utf-8")
        manifest.append({"run_key": run_key, "event_id": row["event_id"], "matrix_row": row})
    path = output / "input_manifest.json"
    path.write_text(json.dumps({"schema_version": "2.1.0", "batch": batch, "fds_version": "6.11.1", "runs": manifest}, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    print(build(args.root.resolve(), args.batch))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
