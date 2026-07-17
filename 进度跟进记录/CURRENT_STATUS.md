---
handoff_id: H-20260717-V2-ALIGN-001
handoff_state: READY
task_status: IN_PROGRESS
source_session: 2026-07-17_V2方案对齐与第一阶段重构.md
current_task: V2-A2-PILOT-PREP
---

# Current Status

## 2026-07-17 v2 architecture reset

Workspace-relative `2.方案研究/FireWorldBenchv2(1).pdf` is now the only core design source. The old T1/T2/T3 ontology, old schemas/configs, `src/fireworldbench/`, P0-P7 freeze chain, formal/quasi experiments, and old results are `LEGACY-NONCOMPARABLE`.

Completed in this session:

- Read all 18 PDF pages by text extraction and visually checked key pages covering the task table, source matrix, FDS scale, and CLI.
- Replaced root charter/README/roadmap/agent instructions.
- Added architecture freeze, conflict audit, nine-task protocol, source role matrix, and 20-event pilot plan.
- Added strict Fire Event and QA schemas, v2 task/source/split/evaluation/pilot configs, fixtures, semantic validation, deterministic scoring, and 8 required `python -m fireworld.*` interfaces.
- Rewrote active detailed-design and governance entry points; historical files remain preserved.
- Full legacy + v2 test suite: `154 passed in 54.27s`.
- v2 focused validation: `11 passed`; Ruff passed; strict mypy passed; schema CLI passed.

Current state is architecture/pilot preparation, not a completed data pilot. No FDS event, model inference, API call, data download, or formal result was produced.

Immediate implementation available:

- Fire Event/QA validation and semantic source/task/track checks.
- event_group cross-split leakage check.
- primary task/component scoring with external-domain separation.
- CLI contract and fail-closed FDS/model gates.

Blocked pending evidence or confirmation:

- exact FDS/Smokeview/FD-Gen versions and executable paths;
- pilot mesh, boundary conditions, exact 20-event matrix and measured cost;
- expert-approved stage/risk/dead-band/tie/same thresholds;
- external source access/license/label scope, especially Fire360 and Detectium;
- non-author annotators/domain reviewer and later model/API budget.

## Server migration readiness

- Transfer the entire workspace root, not only this Git repository. Current transferable content is approximately 5.25 GB before compression and cache exclusions.
- Core PDF SHA-256 is `ba63ab8428d1f759629a89864af7f623589d023dd6d5a29e4940fc6d629a19a6`.
- `migration/README_SERVER_MIGRATION.md` and `migration/SERVER_HANDOFF_PROMPT.md` define Linux reconstruction and project takeover.
- `scripts/server_preflight.py` checks workspace layout, PDF, Git, Python, disk, data and external tools.
- `scripts/build_transfer_manifest.py` and `scripts/verify_transfer_manifest.py` provide file-level SHA-256 transfer verification.
- The frozen manifest currently verifies 3,350 files / 5,525,112,267 bytes; the full repository test baseline is `155 passed`.
- No `.env`, private-key file or likely literal API-key pattern was found in the migration audit. Credentials remain environment-variable references only.
- The Windows Conda environment is not transferable. Linux must rebuild from `environment.yml` and install/version FDS, Smokeview and ffmpeg separately.

User-owned untracked files preserved untouched:

- `详细设计规划/07_FireWorldBench_Benchmark_Design_v2_转写批注.md`
- `详细设计规划/07_original_transcription.md`
- `详细设计规划/08_FireWorldBench_ICLR2027_核心方案_v3.md`
