# P1-PLANNING download and staging audit

Date: 2026-07-14 Asia/Shanghai

This is planning-stage staging only. Original files under `../../3.数据集` were not modified. No files under `../../4.升级拓展` were read or used.

Staged datasets: D01, D02, D03, D04, D05, and D10. Each dataset was copied byte-for-byte into `data/raw`, then listed and hashed with SHA-256. The staged files match the existing P1 source manifest for all six datasets. No staging file was marked eligible for formal training, testing, publication, or redistribution.

Not downloaded: D06 DetectiumFire due to the requested storage/license gate; D07 Fire360, D08 MS-FSDB, D09 DFS, and D11 Boreal-Forest-Fire because they remain placeholders or incomplete resources.

All staging manifests retain `license_status=UNKNOWN`, `redistribution_status=UNKNOWN`, `formal_benchmark_eligible=false`, and `note=planning-stage staging only`. Upstream version/commit remains UNKNOWN pending final source verification.

Checks:

- `python scripts/check_project.py`: passed.
- `PYTHONPATH=.;src python -m pytest -q`: 120 passed.
- `mypy src`: passed.
- `PYTHONPATH=.;src python -m fireworldbench doctor`: passed.
- `PYTHONPATH=.;src python -m fireworldbench pipeline-inventory --root data/raw --output <temp>`: 196 files inventoried.
- `python scripts/probe_data_contract_p1_data_002.py`: read-only probe completed for one D01 CSV and one D03 CSV.

This audit does not constitute license approval, formal benchmark approval, or model experiment evidence.
