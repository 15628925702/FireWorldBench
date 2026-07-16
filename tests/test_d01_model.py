import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_d01_model_is_deterministic_and_explicitly_sparse(tmp_path):
    out = tmp_path / "out"
    command = [sys.executable, "scripts/build_d01_model.py", "--root", "data/raw/D01_Immersed-Tunnel-CFD", "--output", str(out), "--limit", "5"]
    first = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    second = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    assert json.loads(first.stdout)["sample_hash"] == json.loads(second.stdout)["sample_hash"]
    manifest = json.loads((out / "d01_complete_manifest.json").read_text(encoding="utf-8"))
    cases = json.loads((out / "d01_canonical_cases.json").read_text(encoding="utf-8"))["cases"]
    samples = json.loads((out / "d01_prototype_samples.json").read_text(encoding="utf-8"))
    assert manifest["file_count"] == 192
    assert len(cases) == 192
    assert samples["case_count"] == 5
    assert samples["t1_count"] == samples["t2_count"] == samples["t3_count"] == 5
    assert all(case["geometry"]["spatial_precision"] == "spatial_unknown" for case in cases)
    assert all(case["gold_origin"] == "simulator_derived" for case in cases)
    assert all(item["redistribution_status"] == "blocked" for item in manifest["files"])
