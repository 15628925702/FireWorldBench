"""Generate discriminative FDS calibration cases for frozen L2-3 mechanisms."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

CASES: dict[str, dict[str, Any]] = {
    "buoyant_plume": {"supply": 0.0, "exhaust": "", "source": (10.0, 5.0)},
    "ceiling_jet": {"supply": 0.0, "exhaust": "", "source": (10.0, 5.0)},
    "smoke_layer": {"supply": 0.0, "exhaust": "", "source": (10.0, 5.0)},
    "longitudinal_ventilation": {"supply": 2.5, "exhaust": "", "source": (10.0, 5.0)},
    "backlayering": {"supply": 0.2, "exhaust": "", "source": (10.0, 5.0)},
    "extraction_dominated": {
        "supply": 0.0,
        "exhaust": "&VENT XB=8.5,11.5,3.5,6.5,5.0,5.0, SURF_ID='EXHAUST'/",
        "source": (10.0, 5.0),
    },
}


def device(name: str, x: float, y: float, z: float, quantity: str) -> str:
    return f"&DEVC ID='{name}', XYZ={x:.2f},{y:.2f},{z:.2f}, QUANTITY='{quantity}'/"


def input_text(chid: str, case: dict[str, object]) -> str:
    x, y = cast(tuple[float, float], case["source"])
    supply = cast(float, case["supply"])
    exhaust = str(case["exhaust"])
    devices: list[str] = []
    locations = {
        "PLUME": (x, y, 2.0),
        "CEILING_NEAR": (x + 2.0, y, 4.5),
        "CEILING_FAR": (x + 6.0, y, 4.5),
        "LAYER_FAR": (16.0, y, 4.5),
        "UPSTREAM": (5.0, y, 4.5),
        "DOWNSTREAM": (15.0, y, 4.5),
        "EXHAUST_NEAR": (10.0, y, 4.5),
    }
    for name, (dx, dy, dz) in locations.items():
        devices.extend(
            (
                device(f"T_{name}", dx, dy, dz, "TEMPERATURE"),
                device(f"V_{name}", dx, dy, dz, "VISIBILITY"),
                device(f"U_{name}", dx, dy, min(dz, 2.5), "U-VELOCITY"),
            )
        )
    return (
        "\n".join(
            (
                f"&HEAD CHID='{chid}', TITLE='FireWorldBench v2 mechanism calibration'/",
                "&MESH IJK=40,20,10, XB=0.0,20.0,0.0,10.0,0.0,5.0/",
                "&TIME T_END=120.0/",
                "&DUMP DT_DEVC=1.0, DT_SLCF=2.0, DT_SMOKE3D=2.0, SMOKE3D=.TRUE./",
                "&SPEC ID='PROPANE'/",
                "&REAC FUEL='PROPANE', SOOT_YIELD=0.08, CO_YIELD=0.02/",
                "&RAMP ID='FIRE_RAMP', T=0.0, F=0.0/",
                "&RAMP ID='FIRE_RAMP', T=20.0, F=0.25/",
                "&RAMP ID='FIRE_RAMP', T=50.0, F=1.0/",
                "&SURF ID='BURNER', HRRPUA=1200.0, RAMP_Q='FIRE_RAMP'/",
                f"&SURF ID='SUPPLY', VEL={supply:.2f}/",
                "&SURF ID='EXHAUST', VEL=-5.00/",
                "&VENT XB=0.0,20.0,0.0,10.0,0.0,0.0, SURF_ID='INERT'/",
                "&VENT XB=0.0,20.0,0.0,10.0,5.0,5.0, SURF_ID='OPEN'/",
                "&VENT XB=0.0,0.0,0.0,10.0,0.0,5.0, SURF_ID='SUPPLY'/",
                "&VENT XB=20.0,20.0,0.0,10.0,0.0,5.0, SURF_ID='OPEN'/",
                exhaust,
                f"&OBST XB={x - 0.5:.2f},{x + 0.5:.2f},{y - 0.5:.2f},{y + 0.5:.2f},0.0,0.5, SURF_ID='BURNER'/",
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
    output = args.root.resolve() / "fds_runs" / "mechanism_calibration_v2"
    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for index, (mechanism, case) in enumerate(CASES.items(), 1):
        run_key = f"MC2_{index:02d}_{mechanism}"
        run = output / run_key
        run.mkdir(exist_ok=True)
        (run / f"{run_key}.fds").write_text(input_text(run_key, case), encoding="utf-8")
        manifest.append({"run_key": run_key, "mechanism": mechanism, "frozen_case": case})
    (output / "input_manifest.json").write_text(json.dumps({"runs": manifest}, indent=2) + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
