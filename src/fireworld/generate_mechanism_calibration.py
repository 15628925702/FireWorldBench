"""Generate explicit FDS calibration runs for the six L2-3 mechanisms."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

MODES = {
    "buoyant_plume": ("OPEN", 0.0, ""),
    "ceiling_jet": ("OPEN", 0.0, ""),
    "smoke_layer": ("OPEN", 0.0, ""),
    "longitudinal_ventilation": ("SUPPLY", 1.5, ""),
    "backlayering": ("SUPPLY", 0.2, ""),
    "extraction_dominated": (
        "OPEN",
        0.0,
        "&VENT XB=8.0,12.0,3.0,7.0,5.0,5.0, SURF_ID='EXHAUST'/",
    ),
}


def input_text(chid: str, mechanism: str) -> str:
    inlet, velocity, exhaust = MODES[mechanism]
    return (
        "\n".join(
            (
                f"&HEAD CHID='{chid}', TITLE='FireWorldBench mechanism calibration'/",
                "&MESH IJK=40,20,10, XB=0.0,20.0,0.0,10.0,0.0,5.0/",
                "&TIME T_END=120.0/",
                "&DUMP DT_DEVC=1.0, DT_SLCF=2.0, DT_SMOKE3D=2.0, SMOKE3D=.TRUE./",
                "&SPEC ID='PROPANE'/",
                "&REAC FUEL='PROPANE', SOOT_YIELD=0.08, CO_YIELD=0.02/",
                "&RAMP ID='FIRE_RAMP', T=0.0, F=0.0/",
                "&RAMP ID='FIRE_RAMP', T=20.0, F=0.25/",
                "&RAMP ID='FIRE_RAMP', T=50.0, F=1.0/",
                "&SURF ID='BURNER', HRRPUA=900.0, RAMP_Q='FIRE_RAMP'/",
                f"&SURF ID='SUPPLY', VEL={velocity:.2f}/",
                "&SURF ID='EXHAUST', VEL=-2.00/",
                "&VENT XB=0.0,20.0,0.0,10.0,0.0,0.0, SURF_ID='INERT'/",
                "&VENT XB=0.0,20.0,0.0,10.0,5.0,5.0, SURF_ID='OPEN'/",
                f"&VENT XB=0.0,0.0,0.0,10.0,0.0,5.0, SURF_ID='{inlet}'/",
                "&VENT XB=20.0,20.0,0.0,10.0,0.0,5.0, SURF_ID='OPEN'/",
                exhaust,
                "&OBST XB=4.5,5.5,4.5,5.5,0.0,0.5, SURF_ID='BURNER'/",
                "&SLCF PBZ=4.5, QUANTITY='TEMPERATURE'/",
                "&SLCF PBZ=4.5, QUANTITY='VISIBILITY'/",
                "&SLCF PBZ=4.5, QUANTITY='U-VELOCITY'/",
                "&SLCF PBZ=4.5, QUANTITY='DENSITY', SPEC_ID='SOOT'/",
                "&SM3D QUANTITY='DENSITY', SPEC_ID='SOOT'/",
                "&SM3D QUANTITY='TEMPERATURE'/",
                "&DEVC ID='T_UPSTREAM', XYZ=2.5,5.0,4.5, QUANTITY='TEMPERATURE'/",
                "&DEVC ID='V_UPSTREAM', XYZ=2.5,5.0,4.5, QUANTITY='VISIBILITY'/",
                "&DEVC ID='U_UPSTREAM', XYZ=2.5,5.0,2.5, QUANTITY='U-VELOCITY'/",
                "&DEVC ID='T_DOWNSTREAM', XYZ=15.0,5.0,4.5, QUANTITY='TEMPERATURE'/",
                "&DEVC ID='V_DOWNSTREAM', XYZ=15.0,5.0,4.5, QUANTITY='VISIBILITY'/",
                "&DEVC ID='U_DOWNSTREAM', XYZ=15.0,5.0,2.5, QUANTITY='U-VELOCITY'/",
                "&TAIL /",
            )
        )
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    output = args.root.resolve() / "fds_runs" / "mechanism_calibration_v1"
    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for index, mechanism in enumerate(MODES, 1):
        run_key = f"MC_{index:02d}_{mechanism}"
        run = output / run_key
        run.mkdir(exist_ok=True)
        (run / f"{run_key}.fds").write_text(input_text(run_key, mechanism), encoding="utf-8")
        manifest.append({"run_key": run_key, "mechanism": mechanism})
    (output / "input_manifest.json").write_text(json.dumps({"runs": manifest}, indent=2) + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
