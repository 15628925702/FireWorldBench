# FireWorldBench Server Migration

## Transfer unit

Transfer the entire research workspace rooted at the directory that contains:

```text
1.参考文献/
2.方案研究/
3.数据集/
5.项目实现/v1/
```

On the original workstation this root was `G:/0-newResearch/2`. The server path may be different. All active v2 instructions use workspace-relative paths.

Current approximate transfer size is 5.25 GB:

- `5.项目实现/`: 4.06 GB, including 1.74 GB `data/raw` and 2.29 GB legacy `artifacts`.
- `1.参考文献/`: 0.45 GB.
- `3.数据集/`: 0.38 GB.
- other research/design material: about 0.36 GB.

The Git repository alone is insufficient because `.gitignore` intentionally excludes `data/raw/` and `artifacts/`.

The frozen transfer manifest covers 3,350 files and 5,525,112,267 bytes (about 5.15 GiB) after excluding Git internals, caches and temporary output.

## What is authoritative

- Core design: `2.方案研究/FireWorldBenchv2(1).pdf`.
- Core PDF SHA-256: `ba63ab8428d1f759629a89864af7f623589d023dd6d5a29e4940fc6d629a19a6`.
- Active implementation: `5.项目实现/v1/src/fireworld/`.
- Active status: `5.项目实现/v1/进度跟进记录/CURRENT_STATUS.md`.
- Old `src/fireworldbench/`, old T1/T2/T3 configs and `artifacts/` are `LEGACY-NONCOMPARABLE`.

## Transfer recommendations

Use `rsync` when available because it resumes and verifies partial transfers:

```bash
rsync -aH --info=progress2 \
  --exclude='.mypy_cache/' --exclude='.pytest_cache/' --exclude='.ruff_cache/' \
  --exclude='__pycache__/' --exclude='tmp/' \
  /source/2/ user@server:/srv/fireworldbench/2/
```

If the Windows workstation does not have rsync, create an archive and transfer it with `scp`:

```powershell
tar -czf G:\0-newResearch\FireWorldBench_workspace_20260717.tar.gz `
  --exclude=.mypy_cache --exclude=.pytest_cache --exclude=.ruff_cache `
  --exclude=__pycache__ --exclude=tmp `
  -C G:\0-newResearch 2
scp G:\0-newResearch\FireWorldBench_workspace_20260717.tar.gz user@server:/srv/fireworldbench/
```

The archive must be written outside `G:/0-newResearch/2`; otherwise it may include itself while being created.

Do not place API keys in the archive. Set them on the server using environment variables or a secret manager.

Before transfer, rebuild `migration/transfer_manifest.json` from the repository:

```powershell
python scripts/build_transfer_manifest.py --workspace-root ../.. --output migration/transfer_manifest.json
```

The manifest excludes Git internals, Python/tool caches, temporary render output and itself. It intentionally includes raw source snapshots, legacy artifacts, the core PDF and reference literature so the transferred workspace is auditable.

## Rebuild on Linux

Do not transfer the Windows Conda environment, caches, or installed packages. Rebuild:

```bash
cd /srv/fireworldbench/2/5.项目实现/v1
conda env create -f environment.yml
conda activate fireworldbench-v1
python -m pytest -q
python -m ruff check src/fireworld tests/test_v2_contracts.py
python -m mypy src/fireworld
python scripts/server_preflight.py --workspace-root ../..
```

`data/raw/D04_FD-Gen/FD-Gen-main/FD-Gen.exe` is a Windows executable and is not a Linux FDS runtime. Install and record Linux FDS/Smokeview separately. Do not start simulations until versions, executable hashes, mesh, boundary conditions and the exact 20-event manifest are frozen.

## Storage layout on server

Recommended separation:

```text
/srv/fireworldbench/2/              code, documents, source snapshots
/data/fireworldbench/raw/           immutable source data
/data/fireworldbench/fds_runs/      active FDS output
/data/fireworldbench/events/        normalized Fire Events
/data/fireworldbench/qa/            QA release data
/data/fireworldbench/models/        model cache
/archive/fireworldbench/            immutable raw-run archives
```

Use environment variables or symlinks rather than hard-coded server paths. Keep at least 4 TB available for active work; 8 TB is preferable when model caches and several FDS generations coexist.

## Post-transfer acceptance

1. Verify transfer integrity: `python scripts/verify_transfer_manifest.py --workspace-root ../.. --manifest migration/transfer_manifest.json`.
2. Run `python scripts/server_preflight.py --workspace-root ../..`.
3. Confirm the PDF hash matches.
4. Confirm Git HEAD matches the expected pushed commit.
5. Confirm all tests pass on Linux.
6. Record FDS/Smokeview/FD-Gen versions and SHA-256 values.
7. Generate a dry-run 20-event manifest; do not run 180 events.
8. Verify available disk space and write permissions for active and archive roots.

The workstation validation baseline before migration was `155 passed` for the full pytest suite, with Ruff and strict mypy passing for the v2 and migration code.
