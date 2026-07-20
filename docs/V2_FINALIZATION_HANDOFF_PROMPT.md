# V2 Finalization Handoff Prompt

Use the following prompt in a new Codex task.

```text
Take over FireWorldBench v2 finalization in the existing server workspace.

Server root: /root/autodl-tmp/FireWorldBench/2
Project: /root/autodl-tmp/FireWorldBench/2/5.项目实现/v1
Core design PDF: /root/autodl-tmp/FireWorldBench/2/2.方案研究/FireWorldBenchv2(1).pdf
Required PDF SHA-256: ba63ab8428d1f759629a89864af7f623589d023dd6d5a29e4940fc6d629a19a6

First read in full:
- AGENTS.md, PROJECT_CHARTER.md, README.md, ROADMAP.md
- docs/ARCHITECTURE_FREEZE.md, docs/TASK_PROTOCOL.md, docs/IDEAL_DATASET_CONFIGURATION.md
- docs/SOURCE_ROLE_MATRIX.md, docs/DATASET_STATUS_2026-07-20.md
- docs/EXTERNAL_OOD_PRODUCTION_PLAN.md
- 进度跟进记录/CURRENT_STATUS.md
- FDS Core v3.3.1 release manifest and acceptance reports under
  /root/autodl-tmp/FireWorldBench/2/release/fireworldbench_fds_core_v3_3_1

Authority and non-negotiable constraints:
1. The v2 PDF is the sole design authority. Use only src/fireworld/ for active
   implementation; src/fireworldbench/ and old T1/T2/T3 artifacts are legacy.
2. Preserve FDS Core v3.3.1 unchanged and read-only. It is formally accepted:
   180/180 strict qualified Events and 4,039 QA. It is the only main Overall
   leaderboard package.
3. Never turn raw assets into formal Events/QA without Event, assets, QA,
   split, audit and source-level acceptance. Never fabricate labels, versions,
   provenance, expert review, physical checks, or license confirmation.
4. External sources are isolated packages and separate reports; never enter FDS
   Overall. Substitutes keep their own names and cannot be called D-Fire,
   Fire360, MmodalFire, FIgLib/SmokeyNet, or Fire-D.
5. Raw/external raw/formal Events/derived S-I-V/QA/splits/reports/release must
   remain separate. Test answers remain private. Do not leak labels via paths,
   filenames, EXIF, public IDs, options, or fixed answers.

Current data truth is exactly docs/DATASET_STATUS_2026-07-20.md:
- Immersed: 192 structured CSV candidates; no formal QA.
- PolyU: seven XLSX workbooks and row audit; no formal Event/QA.
- FURG: 23 MP4 + 23 XML, video-level group split. XML rectangle = positive
  visible-flame evidence. No rectangle = unknown/unscored, never no_fire.
- Kaggle supplement: only three MP4 plus markup JSON, not 85 videos.
- DeepQuest substitute download may still be in progress; validate it before use.
- Detectium and wrong Fire360 mirror are quarantined. Fire360 official, full
  D-Fire, MmodalFire body, complete FIgLib/SmokeyNet and Fire-D are gaps.

Implement the remaining benchmark work without waiting for further user input:
1. Audit the working tree and server data first. Do not delete existing raw.
2. Complete v2 code and tests for fail-closed external source handling in
   src/fireworld/: source manifests, candidate/formal Event state transitions,
   derived asset manifests, schema/semantic/path/hash validators, group-first
   split/leak/near-duplicate checks, source-separated reporting and data cards.
3. Build FURG candidate derived clips and assets under isolated derived/V and
   derived/I directories. Preserve complete-video event_group. Implement L1-3
   temporal coherence only: intact clips are consistent; reverse/jump/reordered
   clips are deterministic inconsistent labels. Do not use no-box frames as
   no_fire. Keep formal QA at zero until all task/source acceptance checks pass.
4. For Immersed and PolyU, improve parser/field/unit/provenance audits and
   candidate assets only. Do not infer unsupported physical labels. Keep private
   case mappings private and public references opaque.
5. When DeepQuest download is complete, audit archive integrity, class inventory,
   image readability, hashes, EXIF/path leakage and duplicates under its own
   substitute name. Do not call it D-Fire.
6. Build deterministic scorer/baseline/release scaffolding that keeps external
   results separate from FDS. Create source-level acceptance reports that fail
   closed when evidence is missing.
7. Update management documents after every material stage. Every status report
   must give FDS strict count, raw counts per source, formal Event count,
   candidates, quarantined/failed count, active hard gate and next step.

Completion standard for this task is not pretending the entire external track is
formally accepted. It is a coherent, tested, v2-compliant final benchmark
implementation and release framework that honestly packages FDS Core and only
admits external sources that actually pass their source-level gates.
```
