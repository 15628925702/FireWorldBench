"""Generate a one-variable HRRPUA A/B pair from the audited explicit template."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def normalized(text: str) -> str:
    text = re.sub(r"CHID='[^']+'", "CHID='CASE'", text)
    return re.sub(r"HRRPUA=[0-9.]+", "HRRPUA=VALUE", text)


def build(root: Path) -> Path:
    template = root / "fds_runs" / "explicit_observation_batch_01" / "obs_002" / "obs_002.fds"
    destination = root / "fds_runs" / "explicit_counterfactual_01"
    destination.mkdir(parents=True, exist_ok=True)
    source = template.read_text(encoding="utf-8")
    variants = {"cf_hrr_a": 900.0, "cf_hrr_b": 1500.0}
    normalized_inputs: list[str] = []
    for key, hrrpua in variants.items():
        text = source.replace("CHID='obs_002'", f"CHID='{key}'")
        text = re.sub(r"HRRPUA=[0-9.]+", f"HRRPUA={hrrpua:.1f}", text)
        run = destination / key
        run.mkdir(exist_ok=True)
        (run / f"{key}.fds").write_text(text, encoding="utf-8")
        normalized_inputs.append(normalized(text))
    if normalized_inputs[0] != normalized_inputs[1]:
        raise ValueError("counterfactual inputs differ outside HRRPUA")
    manifest = {
        "family": "explicit_counterfactual_01",
        "intervention_variable": "hrrpua",
        "values": variants,
        "normalized_input_sha256": hashlib.sha256(normalized_inputs[0].encode()).hexdigest(),
        "status": "inputs_validated_pending_fds",
    }
    output = destination / "input_manifest.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.root.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
