---
handoff_id: H-20260717-V2-ALIGN-001
handoff_state: READY
task_status: IN_PROGRESS
source_session: 2026-07-17_V2方案对齐与第一阶段重构.md
current_task: V2-A2-PILOT-PREP
---

## 2026-07-20 v2 finalization handoff

The active status is `FDS_CORE_FORMAL_EXTERNAL_OOD_PARTIAL_CANDIDATE`.
`docs/DATASET_STATUS_2026-07-20.md` is the factual external-data authority and
`docs/V2_FINALIZATION_HANDOFF_PROMPT.md` is the task handoff for remaining
non-data benchmark finalization.

- FDS Core v3.3.1 is unchanged and formally accepted: 180/180 strict Events,
  4,039 QA, isolated main leaderboard release.
- External formal Events/QA remain zero. Immersed has 192 candidates; FURG has
  23 candidate video groups; PolyU is audited raw/candidate evidence.
- FURG no-box XML frames are unknown/unscored, not no-fire.
- Detectium and the wrong Fire360 mirror are quarantined. DeepQuest is a
  downloading image substitute; never call it D-Fire.
- External confirmations/licensing are `deferred_external_confirmation`, not
  fabricated acceptance. All external packages remain separate from Overall.

## 2026-07-20 external OOD production baseline

The authoritative v2 PDF hash was reverified on the server. FDS Core v3.3.1
is unchanged and formally accepted: `180/180` strict-qualified Events and
`4,039` QA in `/root/autodl-tmp/FireWorldBench/2/release/fireworldbench_fds_core_v3_3_1`.

External OOD work is separate from the FDS release. Current factual state:

- Immersed Tunnel: 192 parseable structured CSV candidates; no formal QA.
- PolyUFire: seven XLSX workbooks and row-level audit; no formal Events/QA.
- FURG: 23 MP4 + 23 XML, group-first `real_video_ood` split; 14,413 annotated
  flame-frame records and 13,636 unboxed records, which are unknown/unscored.
- Kaggle video supplement: three MP4 + markup JSON, not 85 videos.
- DeepQuest real-image substitute: official 306 MB release found; resumable raw
  download in progress, not yet validated.
- Detectium: 96 GB archive integrity passed but content identity is wrong or
  unverified; quarantined. Fire360, complete D-Fire, MmodalFire, complete
  FIgLib/SmokeyNet and Fire-D remain gaps.

`docs/DATASET_STATUS_2026-07-20.md` and
`docs/EXTERNAL_OOD_PRODUCTION_PLAN.md` are the active external-data handoff.
No raw or substitute source may be renamed as a target dataset or enter FDS
Overall. Use only `src/fireworld/` for subsequent v2 implementation.

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

## 2026-07-17 server pilot-prep continuation

- Verified transfer manifest: `3350 files / 5525112267 bytes`; core PDF SHA-256 matches.
- Rebuilt isolated `fireworldbench-v1` Conda environment with Python 3.11.15.
- Server gates: `159 passed`; Ruff and strict mypy pass for the pilot additions.
- Added dry-run-only 20-event manifest generator and stored an 8,383-byte manifest under the data disk `events/manifests/`; no FDS simulation started.
- Added fail-closed L1-2, L2-1 and L3-3 pilot builders with provenance and schema/semantic tests.
- Installed `/usr/bin/ffmpeg` 4.4.2-0ubuntu0.22.04.1; FDS and Smokeview remain uninstalled. Official candidate is FDS-6.11.1 with SMV-6.11.2, pending verified installer transfer and license record.
- Server quota is 1 vCPU / 2 GiB RAM / no GPU despite larger host visibility; pilot runtime and storage remain measured-cost blockers.

Remaining blockers: exact FDS/Smokeview/FD-Gen binaries and hashes; mesh/boundary freeze; expert stage/risk/dead-band/tie/same thresholds; domain review of difficult negatives; API provider and budget approval.

2026-07-18 continuation: calibration-only geometry catalog, mesh, boundary, output variables, and resource budget were added to `configs/fds_prototype.v2.json`. Mesh and boundary are explicitly frozen only for calibration; full-pilot values remain pending measured calibration. Official FDS installer download is running as a resumable data-disk background job; no executable has been installed or used yet. External sources remain license/access audit items and are not downloaded into the release set.

External-source license screening completed: D-Fire is conditionally usable for internal Real-Image OOD under its repository CC0 collection statement, but underlying-image rights still require review before redistribution. Immersed Tunnel, PolyUFire, Fire360, and DetectiumFire remain held because explicit dataset access/redistribution terms were not verifiable.

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

## 2026-07-21 Benchmark Finalization

- FDS Core v3.3.1: 180/180 strict Events and 4,039 QA; 8,209 manifest hashes verified.
- External formal/candidate/quarantine: 0 formal Events/QA; Immersed 192 candidates,
  FURG 23 candidate groups, Detectium and wrong Fire360 mirror quarantined.
- Current hard gate: authorized OpenAI-compatible model smoke run returned HTTP 403;
  no model prediction or score is admitted.
- Current engineering state: source eligibility, prediction binding, deterministic
  breakdown scorer, coverage matrix, release verifier and public runner dry-run exist.
- Next: complete baseline/report/evidence generators and resolve API authorization.

## 2026-07-21 Runner and Reporting Update

FDS Core v3.3.1 remains immutable and accepted: 180/180 strict Events and
4,039 QA. External formal Events/QA remain zero; candidate, substitute and
quarantine states are unchanged and excluded from FDS Overall. The fixed
OpenAI-compatible runner model is `openai/gpt-4o-mini`; a proxy-backed API
smoke test succeeded and an S-track full run is in progress. The active hard
gate is now completion of that run followed by private deterministic scoring,
not dataset work. Track-aware scoring, release verification, evidence matrix,
CSV task tables and source/task/track coverage reporting write only to
`artifacts/`; no LLM judge or unsupported calibration metric enters the main
result.
## 2026-07-21 S-Track Evaluation Update

FDS Core v3.3.1 remains immutable and accepted: 180/180 strict Events and
4,039 QA. External formal Events/QA remain zero; candidate, substitute,
quarantine, and gap states are unchanged and remain outside FDS Overall.

The fixed OpenAI-compatible model openai/gpt-4o-mini completed the FDS public
S track after a nine-task structured-output preflight. All 1,360 predictions
passed schema and semantic validation after retrying 14 transient proxy TLS
failures. The private deterministic FDS S-track macro is 56.194247062475384;
this is not FDS Overall and must not be presented as such. No LLM judge was
used. The active hard gate is independent I/V-track runner support and their
separate protocol-qualified evaluation; no external source processing is
authorized.
## 2026-07-21 Multimodal Evaluation Update

FDS Core v3.3.1 remains immutable and accepted: 180/180 strict Events and
4,039 QA. External formal Events/QA remain zero; candidate, substitute,
quarantine, and gap states are unchanged and remain outside FDS Overall.

The previous S diagnostic run is superseded because its L1-2 candidate assets
were not supplied to the model. The corrected public-asset S run uses
structured_json_and_candidate_hydration_v1 and has 1,360/1,360 valid
predictions, zero missing predictions, and deterministic FDS S-track macro
57.50100292190619. This is a track result, not FDS Overall.

The image adapter openai_image_url_data_v1 has completed the released I track:
66/66 valid predictions, zero missing, with L1-3 score 68.93939393939394.
Only L1-3 is published for I, so I Overall is null. The fixed model declares
text/image/file inputs but no video input; V is explicitly unsupported and no
frame-proxy result is reported. No LLM judge was used.
## 2026-07-21 Strict Baseline Update

Release-native strict baselines were regenerated from frozen public train/test
inputs under the current prediction contract. No API model or dataset processing
was used. On the FDS S track, seeded_chance is 21.03476689780523,
train_majority is 32.50098405595995, and physical_rule is
53.46437556768639; the compliant fixed-model S result is 57.50100292190619.
All four are track-level nine-task macros, not FDS Overall.

On I (L1-3 only), seeded_chance is 34.09090909090909, train_majority is 50.0,
and the fixed model is 68.93939393939394. physical_rule is unsupported for I
because it has no structured physical input. V remains unsupported for the
fixed model. Result tables are generated under artifacts/results/fds_core_v3_3_1.