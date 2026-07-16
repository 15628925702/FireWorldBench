"""Generate deterministic FDS input fixtures and manifests; never runs FDS."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def fds(case: dict, cfg: dict) -> str:
    lines = [f"&HEAD CHID='{case['case_uid']}', TITLE='FireWorldBench synthetic core fixture'/", "&TIME T_END=30.0/", "&MESH IJK=60,6,4, XB=0.0,60.0,0.0,6.0,0.0,4.0/", "&SURF ID='WALL', COLOR='GRAY', DEFAULT=.TRUE./", "&OBST XB=0.0,60.0,0.0,6.0,0.0,0.2, SURF_ID='WALL'/", "&OBST XB=0.0,60.0,0.0,0.2,0.0,4.0, SURF_ID='WALL'/", "&OBST XB=0.0,60.0,5.8,6.0,0.0,4.0, SURF_ID='WALL'/", f"&VENT XB=0.0,0.0,0.0,6.0,0.0,4.0, SURF_ID='OPEN'/", f"&VENT XB=60.0,60.0,0.0,6.0,0.0,4.0, SURF_ID='OPEN'/", f"&MISC GVEC=1.0,0.0,0.0/", f"! FWB_CASE_JSON {json.dumps(case, sort_keys=True)}"]
    if case["fire"]:
        x, y, z = case["source_xyz_m"]
        lines += [f"&SURF ID='FIRE', HRRPUA={case['hrr_peak_kw'] / 1.0:.3f}, COLOR='RED'/", f"&OBST XB={x-0.5:.2f},{x+0.5:.2f},{y-0.5:.2f},{y+0.5:.2f},{z:.2f},{z+0.2:.2f}, SURF_ID='FIRE'/"]
    for i, (x, y, z) in enumerate(cfg["sensor_layouts"][case["sensor_layout_id"]], 1):
        lines += [f"&DEVC ID='T_{i:02d}', XYZ={x},{y},{z}, QUANTITY='TEMPERATURE'/", f"&DEVC ID='CO_{i:02d}', XYZ={x},{y},{z}, QUANTITY='VOLUME FRACTION', SPEC_ID='CARBON MONOXIDE'/", f"&DEVC ID='SOOT_{i:02d}', XYZ={x},{y},{z}, QUANTITY='EXTINCTION COEFFICIENT'/", f"&DEVC ID='U_{i:02d}', XYZ={x},{y},{z}, QUANTITY='VELOCITY'/"]
    lines += ["&DUMP DT_DEVC=1.0, DT_SLCF=1.0, QUANTITIES='TEMPERATURE','VELOCITY','VOLUME FRACTION','PRESSURE'/", "&TAIL /"]
    return "\n".join(lines) + "\n"

def build(config: Path, output: Path) -> dict:
    cfg = json.loads(config.read_text(encoding="utf-8")); out = output.resolve(); out.mkdir(parents=True, exist_ok=True)
    cases = []
    for case in cfg["cases"]:
        case_dir = out / case["case_uid"]; case_dir.mkdir(exist_ok=True)
        text = fds(case, cfg); (case_dir / f"{case['case_uid']}.fds").write_text(text, encoding="utf-8")
        cases.append({"case_uid": case["case_uid"], "split": case["split"], "input_ref": str((case_dir / f"{case['case_uid']}.fds").relative_to(out)), "input_sha256": hashlib.sha256(text.encode()).hexdigest(), "status": "fds_input_generated", "field_output_status": "blocked_fds_not_available", "gold_origin": "simulator_state_pending"})
    result = {"schema_version": 1, "status": "BLOCKED_FDS_RUNTIME", "generator": cfg["generator"], "fds": cfg["fds"], "config_sha256": digest(cfg), "case_count": len(cases), "cases": cases, "generated_data_written": False, "field_manifest": [], "sensor_projection_manifest": [], "event_label_manifest": [], "failure_log": [{"code": "FDS_RUNTIME_NOT_AVAILABLE", "message": "FDS executable was not found on PATH; no physical field was generated"}]}
    result["manifest_sha256"] = digest(result); (out / "synthetic_core_generation_manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); return result

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--config", type=Path, default=Path("configs/synthetic_core_v1.json")); p.add_argument("--output", type=Path, default=Path("artifacts/synthetic_core_fixture")); args = p.parse_args(); print(json.dumps(build(args.config, args.output), ensure_ascii=False, indent=2))
