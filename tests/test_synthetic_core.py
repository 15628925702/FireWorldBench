import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).parents[1]
def test_fixture_generation_and_pair_audit(tmp_path):
    cfg=ROOT/"configs/synthetic_core_v1.json"
    result=subprocess.run([sys.executable,"scripts/validate_synthetic_core.py","--config",str(cfg)],cwd=ROOT,check=True,capture_output=True,text=True)
    validation = json.loads(result.stdout)
    assert validation["status"] == "PASS"
    assert validation["pair_audit"][0]["pair_type"] == "counterfactual"
    assert validation["pair_audit"][0]["status"] == "PASS"
    out=tmp_path/"fixture"
    first=subprocess.run([sys.executable,"scripts/generate_synthetic_core.py","--config",str(cfg),"--output",str(out)],cwd=ROOT,check=True,capture_output=True,text=True)
    second=subprocess.run([sys.executable,"scripts/generate_synthetic_core.py","--config",str(cfg),"--output",str(out),],cwd=ROOT,check=True,capture_output=True,text=True)
    assert json.loads(first.stdout)["manifest_sha256"] == json.loads(second.stdout)["manifest_sha256"]
    manifest=json.loads((out/"synthetic_core_generation_manifest.json").read_text())
    assert manifest["case_count"] == 6 and manifest["generated_data_written"] is False
    assert len(list(out.rglob("*.fds"))) == 6
