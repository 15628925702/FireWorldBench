"""Generate FDS inputs with physically observable thermal, smoke and flow signals."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunSpec:
    key: str
    event_class: str
    hrrpua: float
    source_x: float
    source_y: float
    supply_velocity: float
    source_region: str | None
    ventilation_mode: str


SPECS = (
    RunSpec("obs_001", "fire", 800.0, 5.0, 2.5, 0.0, "R1", "still"),
    RunSpec("obs_002", "fire", 1200.0, 10.0, 2.5, 0.0, "R2", "still"),
    RunSpec("obs_003", "fire", 1800.0, 15.0, 2.5, 0.0, "R3", "still"),
    RunSpec("obs_004", "fire", 1200.0, 5.0, 7.5, 1.5, "R4", "longitudinal"),
    RunSpec("obs_005", "fire", 1800.0, 10.0, 7.5, 1.5, "R5", "longitudinal"),
    RunSpec("obs_006", "fire", 2400.0, 15.0, 7.5, 2.0, "R6", "longitudinal"),
    RunSpec("obs_007", "no_fire", 0.0, 10.0, 5.0, 0.0, None, "still"),
    RunSpec("obs_008", "ventilation_disturbance", 0.0, 10.0, 5.0, 2.5, None, "longitudinal"),
    RunSpec("obs_009", "no_fire", 0.0, 10.0, 5.0, 1.5, None, "longitudinal"),
    RunSpec("obs_010", "fire", 1500.0, 15.0, 5.0, 2.5, "R7", "longitudinal"),
)


def device_lines(spec: RunSpec) -> list[str]:
    lines: list[str] = []
    locations = (
        ("R1", 3.0, 2.5),
        ("R2", 10.0, 2.5),
        ("R3", 17.0, 2.5),
        ("R4", 3.0, 7.5),
        ("R5", 10.0, 7.5),
        ("R6", 17.0, 7.5),
    )
    for region, x, y in locations:
        lines += [
            f"&DEVC ID='T_{region}_CEILING', XYZ={x:.1f},{y:.1f},4.5, QUANTITY='TEMPERATURE'/",
            f"&DEVC ID='V_{region}_CEILING', XYZ={x:.1f},{y:.1f},4.5, QUANTITY='VISIBILITY'/",
            f"&DEVC ID='U_{region}_CEILING', XYZ={x:.1f},{y:.1f},4.5, QUANTITY='U-VELOCITY'/",
        ]
    lines += [
        f"&DEVC ID='T_SOURCE_NEAR', XYZ={spec.source_x:.1f},{spec.source_y:.1f},1.0, QUANTITY='TEMPERATURE'/",
        f"&DEVC ID='V_SOURCE_CEILING', XYZ={spec.source_x:.1f},{spec.source_y:.1f},4.5, QUANTITY='VISIBILITY'/",
        "&DEVC ID='U_INLET', XYZ=0.5,5.0,2.5, QUANTITY='U-VELOCITY'/",
        "&DEVC ID='U_OUTLET', XYZ=19.5,5.0,2.5, QUANTITY='U-VELOCITY'/",
    ]
    return lines


def input_text(spec: RunSpec) -> str:
    fire_surface = f"&SURF ID='BURNER', HRRPUA={spec.hrrpua:.1f}, RAMP_Q='FIRE_RAMP', COLOR='RED'/"
    burner = (
        f"&OBST XB={spec.source_x - 0.5:.1f},{spec.source_x + 0.5:.1f},{spec.source_y - 0.5:.1f},{spec.source_y + 0.5:.1f},0.0,0.5, SURF_ID='BURNER'/"
        if spec.hrrpua > 0
        else ""
    )
    inlet = (
        "&VENT XB=0.0,0.0,0.0,10.0,0.0,5.0, SURF_ID='OPEN'/"
        if spec.supply_velocity == 0
        else "&VENT XB=0.0,0.0,0.0,10.0,0.0,5.0, SURF_ID='SUPPLY'/"
    )
    lines = [
        f"&HEAD CHID='{spec.key}', TITLE='FireWorldBench explicit-observation {spec.key}'/",
        "&MESH IJK=40,20,10, XB=0.0,20.0,0.0,10.0,0.0,5.0/",
        "&TIME T_END=120.0/",
        "&DUMP DT_DEVC=1.0, DT_HRR=1.0, DT_SLCF=2.0, DT_SMOKE3D=2.0, SMOKE3D=.TRUE./",
        "&SPEC ID='PROPANE'/",
        "&REAC FUEL='PROPANE', SOOT_YIELD=0.08, CO_YIELD=0.02/",
        "&RAMP ID='FIRE_RAMP', T=0.0, F=0.0/",
        "&RAMP ID='FIRE_RAMP', T=20.0, F=0.25/",
        "&RAMP ID='FIRE_RAMP', T=50.0, F=1.0/",
        "&MATL ID='CONCRETE', CONDUCTIVITY=1.4, SPECIFIC_HEAT=0.88, DENSITY=2200.0/",
        "&SURF ID='FLOOR', MATL_ID='CONCRETE', THICKNESS=0.1, COLOR='GRAY'/",
        "&SURF ID='OPEN', COLOR='INVISIBLE'/",
        f"&SURF ID='SUPPLY', VEL={spec.supply_velocity:.2f}, COLOR='INVISIBLE'/",
        fire_surface,
        "&VENT XB=0.0,20.0,0.0,10.0,0.0,0.0, SURF_ID='FLOOR'/",
        "&VENT XB=0.0,20.0,0.0,10.0,5.0,5.0, SURF_ID='OPEN'/",
        inlet,
        "&VENT XB=20.0,20.0,0.0,10.0,0.0,5.0, SURF_ID='OPEN'/",
        burner,
        "&SLCF PBZ=4.5, QUANTITY='TEMPERATURE'/",
        "&SLCF PBZ=4.5, QUANTITY='VISIBILITY'/",
        "&SLCF PBZ=4.5, QUANTITY='DENSITY', SPEC_ID='SOOT'/",
        "&SLCF PBZ=4.5, QUANTITY='U-VELOCITY'/",
        "&SM3D QUANTITY='DENSITY', SPEC_ID='SOOT'/",
        "&SM3D QUANTITY='TEMPERATURE'/",
        *device_lines(spec),
        "&TAIL /",
    ]
    return "\n".join(line for line in lines if line) + "\n"


def build(root: Path) -> Path:
    batch = root / "fds_runs" / "explicit_observation_batch_01"
    batch.mkdir(parents=True, exist_ok=True)
    for spec in SPECS:
        run = batch / spec.key
        run.mkdir(exist_ok=True)
        (run / f"{spec.key}.fds").write_text(input_text(spec), encoding="utf-8")
    manifest = {
        "schema_version": "2.1.0",
        "batch": "explicit_observation_batch_01",
        "purpose": "replacement pilot with explicit thermal, visibility, smoke and ventilation observations",
        "fds_version": "6.11.1",
        "runs": [asdict(spec) for spec in SPECS],
    }
    path = batch / "input_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.root.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
