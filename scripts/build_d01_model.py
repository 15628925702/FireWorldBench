"""Build a provenance-first D01 planning model from the staged FDS device CSVs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

SOURCE_URL = "https://github.com/babeteax/Immersed-Tunnel-Fire-Location-Detection-Data"
UPSTREAM_COMMIT = "00a81959b792fe013e2ac0468758b5fbedf3e68f"
BUILDER_VERSION = "D01-FOUR-DIMENSIONAL-PROTOTYPE-1"
NAME_RE = re.compile(r"^(70|100|130)(M|U)(\d{2})_devc\.csv$")

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def parse_file(path: Path, root: Path) -> tuple[dict, dict]:
    match = NAME_RE.match(path.name)
    if not match:
        raise ValueError(f"unsupported D01 filename: {path.name}")
    location, lane, vent = match.groups()
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        units = next(reader)
        headers = next(reader)
        first = next(reader)
        last = first
        rows = 1
        interval = None
        for row in reader:
            rows += 1
            if interval is None:
                interval = float(row[0]) - float(last[0])
            last = row
    variables = []
    for name, unit in zip(headers[1:], units[1:]):
        kind = "temperature" if name.startswith("T-") else "species_or_flow" if name.startswith(("C-", "MASS FLOW")) else "unknown"
        variables.append({"name": name, "raw_unit": unit, "canonical_unit": unit, "data_type": "float", "kind": kind, "origin": "simulator_state"})
    rel = path.relative_to(root).as_posix()
    case_uid = f"D01_case_{location}{lane}{vent}"
    file_item = {"relative_path": rel, "size_bytes": path.stat().st_size, "sha256": sha256(path), "kind": "raw", "source_url": SOURCE_URL, "upstream_commit": UPSTREAM_COMMIT, "acquired_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(), "license_status": "planning_only_unresolved", "redistribution_status": "blocked"}
    case = {"case_uid": case_uid, "source_id": "D01", "source_version": UPSTREAM_COMMIT, "gold_origin": "simulator_derived", "geometry": {"geometry_id": "UNKNOWN", "coordinate_system": "UNKNOWN", "spatial_precision": "spatial_unknown", "evidence": "D01 README describes a tunnel scenario but provides no geometry/grid in staging"}, "fire_source": {"location": {"tunnel_longitudinal_m": float(location), "lane": lane, "origin": "filename_encoded"}, "hrr": "UNKNOWN", "start_time": 0.0, "evidence": "filename and D01 README; HRR absent"}, "ventilation": {"direction": "UNKNOWN", "velocity": "UNKNOWN", "extraction_config": int(vent), "origin": "filename_encoded"}, "sensor_layout": [{"sensor_id": h, "location": "UNKNOWN", "variables": [h], "spatial_precision": "sensor_id_only"} for h in headers[1:]], "time_axis": {"t0_definition": "first CSV Time value", "unit": units[0], "sampling_interval": interval, "duration": float(last[0]) - float(first[0]), "row_count": rows, "monotonic": True, "evidence": rel}, "available_fields": ["time", "sensor_variables", "filename_case_encoding"], "missing_fields": ["geometry", "mesh", "sensor_coordinates", "hrr", "ventilation_direction", "ventilation_velocity"], "raw_refs": [rel], "alignment_status": "aligned_within_single_file", "group_key": f"D01|{location}|{lane}|{vent}", "field_dictionary": variables}
    return file_item, case

def build(root: Path, output: Path, limit: int) -> dict:
    data_root = root / "CFD-Data"
    files = sorted(data_root.glob("*_devc.csv"))
    file_items, cases = [], []
    for path in files:
        item, case = parse_file(path, data_root)
        file_items.append(item)
        cases.append(case)
    cases = sorted(cases, key=lambda x: x["case_uid"])
    manifest = {"schema_version": 1, "builder_version": BUILDER_VERSION, "dataset_id": "D01", "source_url": SOURCE_URL, "upstream_commit": UPSTREAM_COMMIT, "acquired_at": datetime.now(timezone.utc).isoformat(), "status": "planning_only", "formal_benchmark_eligible": False, "raw_files_unchanged": True, "file_count": len(file_items), "total_bytes": sum(x["size_bytes"] for x in file_items), "files": file_items}
    manifest["manifest_sha256"] = digest(manifest)
    selected = cases[:limit]
    samples = []
    for case in selected:
        base = {"case_uid": case["case_uid"], "source_id": "D01", "task_id": None, "observation_budget_id": "D01_sparse_sensor_budget_v1", "time_window": {"relative_to": "case_t0", "start_s": 0.0, "end_s": case["time_axis"]["duration"]}, "spatial_scope": "sensor_points_only; spatial_unknown", "intervention_id": None, "gold_origin": "simulator_derived", "input_refs": case["raw_refs"], "gold_refs": [], "scoring_metadata": {"visibility": "private", "status": "research_only", "thresholds": "not frozen"}}
        for task in ("T1", "T2", "T3"):
            sample = dict(base); sample["task_id"] = task; sample["sample_uid"] = f"D01-{task}-{case['case_uid']}"; samples.append(sample)
    result = {"schema_version": 1, "status": "research_only", "case_count": len(selected), "t1_count": len(selected), "t2_count": len(selected), "t3_count": len(selected), "samples": samples, "source_manifest_sha256": manifest["manifest_sha256"], "deterministic_hash": digest(samples)}
    output.mkdir(parents=True, exist_ok=True)
    for name, value in (("d01_complete_manifest.json", manifest), ("d01_canonical_cases.json", {"schema_version": 1, "dataset_id": "D01", "status": "research_only", "space_capability": "Level_1_sensor_points_only", "cases": cases}), ("d01_prototype_samples.json", result)):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"files": len(files), "cases": len(cases), "prototype_cases": len(selected), "manifest_sha256": manifest["manifest_sha256"], "sample_hash": result["deterministic_hash"]}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("data/raw/D01_Immersed-Tunnel-CFD"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/d01"))
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(build(args.root, args.output, args.limit), indent=2))
