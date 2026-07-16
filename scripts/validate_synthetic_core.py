"""Validate synthetic-core case configuration and strict one-variable pair claims."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def validate(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8")); errors=[]; cases=cfg.get("cases", [])
    ids=[c.get("case_uid") for c in cases]
    if len(ids) != len(set(ids)): errors.append("duplicate_case_uid")
    bounds=cfg["geometry"]["bounds_m"]
    for c in cases:
        point=c.get("source_xyz_m")
        if point and not (bounds[0] <= point[0] <= bounds[1] and bounds[2] <= point[1] <= bounds[3] and bounds[4] <= point[2] <= bounds[5]): errors.append(f"source_out_of_bounds:{c['case_uid']}")
    by_pair={}
    for c in cases:
        if c.get("pair_id"): by_pair.setdefault(c["pair_id"], []).append(c)
    pair_results=[]
    for pair_id, pair in by_pair.items():
        if len(pair) != 2: pair_results.append({"pair_id": pair_id, "pair_type": "configuration_comparison", "status": "invalid_pair_size"}); continue
        keys={"source_xyz_m","hrr_peak_kw","hrr_curve","ventilation_velocity_mps","extraction","sensor_layout_id","seed"}
        changed=[k for k in keys if pair[0].get(k) != pair[1].get(k)]
        pair_results.append({"pair_id": pair_id, "pair_type": "counterfactual" if len(changed)==1 else "configuration_comparison", "changed_axes": changed, "status": "PASS" if changed else "invalid_no_change"})
    result={"schema_version":1,"status":"PASS" if not errors else "FAIL","case_count":len(cases),"errors":errors,"pair_audit":pair_results,"formal_eligible":False,"reason":"FDS outputs and license/approval gates are not closed"}; path.with_name("synthetic_core_validation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); return result
if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,default=Path("configs/synthetic_core_v1.json")); print(json.dumps(validate(p.parse_args().config),ensure_ascii=False,indent=2))
