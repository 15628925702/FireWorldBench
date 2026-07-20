"""Generate targeted ceiling-jet and extraction calibration FDS cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

CASES: dict[str, dict[str, Any]] = {
    "ceiling_jet": {"source_x": 3.0, "hrr": 8000.0, "exhaust": None},
    "extraction_dominated": {"source_x": 10.0, "hrr": 2400.0, "exhaust": -12.0},
}


def device(name: str, x: float, z: float, quantity: str) -> str:
    return f"&DEVC ID='{name}', XYZ={x:.2f},5.00,{z:.2f}, QUANTITY='{quantity}'/"


def input_text(chid: str, case: dict[str, float | None]) -> str:
    source_x = cast(float, case["source_x"])
    hrr = cast(float, case["hrr"])
    exhaust = case["exhaust"]
    vents = [
        "&VENT XB=0.0,20.0,0.0,10.0,0.0,0.0, SURF_ID='INERT'/",
        "&VENT XB=0.0,0.0,0.0,10.0,0.0,5.0, SURF_ID='OPEN'/",
        "&VENT XB=20.0,20.0,0.0,10.0,0.0,5.0, SURF_ID='OPEN'/",
    ]
    if exhaust is not None:
        vents.extend(
            (
                f"&SURF ID='EXHAUST', VEL={float(exhaust):.2f}/",
                "&VENT XB=8.0,12.0,3.0,7.0,5.0,5.0, SURF_ID='EXHAUST'/",
            )
        )
    devices: list[str] = []
    for name, x, z in (
        ("PLUME", source_x, 2.0),
        ("JET_2M", source_x + 2.0, 4.5),
        ("JET_5M", source_x + 5.0, 4.5),
        ("JET_8M", source_x + 8.0, 4.5),
        ("EXHAUST_BELOW", 10.0, 4.0),
        ("REMOTE_LAYER", 17.0, 4.0),
    ):
        devices.extend(
            (
                device(f"T_{name}", x, z, "TEMPERATURE"),
                device(f"V_{name}", x, z, "VISIBILITY"),
                device(f"U_{name}", x, min(z, 2.5), "U-VELOCITY"),
            )
        )
    return (
        "\n".join(
            (
                f"&HEAD CHID='{chid}', TITLE='FireWorldBench mechanism calibration v4'/",
                "&MESH IJK=40,20,10, XB=0.0,20.0,0.0,10.0,0.0,5.0/",
                "&TIME T_END=120.0/",
                "&DUMP DT_DEVC=1.0, DT_SLCF=2.0, DT_SMOKE3D=2.0, SMOKE3D=.TRUE./",
                "&SPEC ID='PROPANE'/",
                "&REAC FUEL='PROPANE', SOOT_YIELD=0.12, CO_YIELD=0.02/",
                "&RAMP ID='FIRE_RAMP', T=0.0, F=0.0/",
                "&RAMP ID='FIRE_RAMP', T=10.0, F=0.25/",
                "&RAMP ID='FIRE_RAMP', T=30.0, F=1.0/",
                f"&SURF ID='BURNER', HRRPUA={hrr:.1f}, RAMP_Q='FIRE_RAMP'/",
                *vents,
                f"&OBST XB={source_x - 0.5:.2f},{source_x + 0.5:.2f},4.5,5.5,0.0,0.5, SURF_ID='BURNER'/",
                "&SLCF PBZ=4.5, QUANTITY='TEMPERATURE'/",
                "&SLCF PBZ=4.5, QUANTITY='VISIBILITY'/",
                "&SLCF PBZ=4.5, QUANTITY='U-VELOCITY'/",
                "&SLCF PBZ=4.5, QUANTITY='DENSITY', SPEC_ID='SOOT'/",
                "&SM3D QUANTITY='DENSITY', SPEC_ID='SOOT'/",
                "&SM3D QUANTITY='TEMPERATURE'/",
                *devices,
                "&TAIL /",
            )
        )
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    output = args.root.resolve() / "fds_runs" / "mechanism_calibration_v4"
    output.mkdir(parents=True, exist_ok=True)
    runs = []
    for index, (mechanism, case) in enumerate(CASES.items(), 1):
        key = f"MC4_{index:02d}_{mechanism}"
        run = output / key
        run.mkdir(exist_ok=True)
        (run / f"{key}.fds").write_text(input_text(key, case), encoding="utf-8")
        runs.append({"run_key": key, "mechanism": mechanism, "boundary_conditions": case})
    (output / "input_manifest.json").write_text(json.dumps({"runs": runs}, indent=2) + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
