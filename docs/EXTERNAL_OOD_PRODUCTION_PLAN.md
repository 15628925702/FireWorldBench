# External Real-Data OOD Production Plan

Status: `ACTIVE-RECOVERY-AND-PRODUCTION`

## 2026-07-20 Superseding Status

For the current factual source inventory, use `DATASET_STATUS_2026-07-20.md`.
Detectium archive integrity subsequently passed but its content identity is
wrong or unverified and it is quarantined. FURG has completed raw decode,
dynamic, XML alignment and group-first candidate split audits. Its no-box XML
records are unknown/unscored. DeepQuest is a downloading real-image substitute.
These facts supersede earlier preliminary rows in this plan; this document
remains the production-gate specification.

Last verified: 2026-07-20. This plan applies only to the external OOD track.
The core design authority is `FireWorldBenchv2(1).pdf` with SHA-256
`ba63ab8428d1f759629a89864af7f623589d023dd6d5a29e4940fc6d629a19a6`.
It does not alter FDS Core v3.3.1, whose standalone release remains
`/root/autodl-tmp/FireWorldBench/2/release/fireworldbench_fds_core_v3_3_1`.

## Storage and Evidence Boundaries

- `raw/<source>/`: immutable downloaded or cloned source material. It is never
  a Benchmark Event, QA set, split, or release evidence by itself.
- `external_ood/source_manifests/`: source-level provenance, hashes, inventory,
  license evidence, field inventory, and archive/readability checks.
- `external_ood/events/<source>/`: normalized Fire Events only after source
  inspection and strict validation.
- `external_ood/derived/S`, `external_ood/derived/I`, `external_ood/derived/V`:
  sanitized derived assets, never mixed with raw input or each other.
- `external_ood/qa`, `external_ood/splits`, `external_ood/reports`, and
  `external_ood/quarantine`: respectively QA, group-first splits, acceptance
  evidence, and excluded material with a reproducible reason.
- `release/fireworldbench_fds_core_v3_3_1/` is read-only for this effort.
  External release packages must be separate and may reference its snapshot ID
  only as provenance, never overwrite, repackage, or relabel FDS material.

## Audited Source Matrix

| Source | Official provenance / version evidence | Raw location and audited state | Modality and defensible labels | Intended role and task ceiling | Status / hard gate |
|---|---|---|---|---|---|
| Immersed Tunnel CFD | Repository mirror README describes 192 FDS outcomes for six ignition locations and 32 exhaust configurations. Zenodo `record.json` plus archive hashes must be captured into a new manifest before event construction. | `raw/immersed_tunnel`, 323 files, 13,949,687,672 bytes; 192 CSVs; `01_Setup.zip` and `06_CFD.zip` archive tests passed. `05_CFD.zip` is present and must be separately tested/hashed. | Structured CFD time series. Source/exhaust information may be used only after a deterministic mapping file ties it to repository documentation; no filename is exposed in public Event/QA paths or text. | `External-CFD`; S only. Candidate limited to source/stage recovery and other tasks strictly supported by parsed numerical fields and documented mappings. | `eligible_candidate`, pending complete archive/source manifest, schema mapping, label sufficiency, sanitization, group split and acceptance audits. Visual substitutes are excluded from CFD claims. |
| PolyUFire Tunnel Fire Database | README cites Zhang et al., TUST 2020, DOI `10.1016/j.tust.2020.103691`; field-level workbook provenance still needs manifest capture. | `raw/polyu/repo`, 135 files, 97,585,852 bytes; 80 XLS plus 8 XLSX. | Experimental tabular records for critical velocity, backlayering and thermal topics. No unsourced full-field, CO, soot, camera, or future labels. | `Experiment`; S only. Publish only verified quantitative trend/mechanism subtracks allowed by TASK_PROTOCOL and source fields. | `eligible_candidate`, pending workbook schema extraction, units/row semantics audit, task-rule freeze, group split and acceptance. |
| DetectiumFire | Official dataset attribution, version, license, and usable labels must be read from the source archive/documentation; local filename alone is insufficient. | `raw/detectium/kaggle_detectiumfire/detectiumfire.zip`, 102,564,334,853 bytes; accompanying paper PDF. Archive integrity check was not completed in the initial audit. | Unknown until archive and original annotation metadata are parsed. | Optional `External OOD` I/V only when labels and license permit. | `raw_only`; blocked from Event/QA/release until integrity, provenance, license and annotation scope all pass. |
| FURG fire video dataset | Repository README identifies `furg-fire-dataset`; local CC0 license and per-video OpenCV XML flame boxes are present. It is not Fire360. | `raw/fire360/furg_fire_substitute`, 23 MP4 + 23 XML, 1,240,200,453 bytes. | Real videos with frame-level visible-flame rectangles. No Fire360 360-degree, firefighter-training, HRR, source, or future-state claim. | `Real-Video-OOD-Substitute`; V/I candidates only for visible-fire attribution and temporal coherence supported by XML and decoded frames. | `substitute_only`; source manifest, decode/dynamic/continuity tests, annotation parser, sanitized assets, group split and acceptance required. Never named Fire360 in Events, QA, reports or release. |
| D-Fire | Official repository `gaia-solutions-on-demand/DFireDataset`; README declares more than 21,000 images, YOLO annotations and CC0 collection statement, while warning that underlying image rights need review. | `raw/dfire` has only 66 files / 23,699,471 bytes and six JPG samples; it is not the complete dataset. | Sample-only material cannot represent full D-Fire. Full dataset can support image-level fire/smoke/none only from official YOLO labels. | `Real-Image-OOD`; I only, principally L1-1 with an explicitly reduced label mapping. | `raw_only` for local samples; full official acquisition, checksums, annotation audit and rights review required before formal inclusion. |
| DeepQuest Fire-Smoke Dataset | GitHub release `DeepQuestAI/Fire-Smoke-Dataset`, asset `FIRE-SMOKE-DATASET.zip`; probe on 2026-07-20 reports 320,963,592 bytes. | Target raw path `raw/real_image_substitute/deepquest_fire_smoke/`; download is separately tracked and resumable. | Claimed fire/smoke/neutral image classes; class semantics must be audited after archive validation. | Separate `Real-Image-OOD-Substitute`; never renamed D-Fire. | `downloading_substitute`; archive, image/label inventory, class/path leakage and duplicate audits remain required. |
| Fire360 | Official project: `https://fire360bench.github.io/`; target is the actual 228-video, approximately 50-hour collection and its documented annotations. | No official Fire360 media locally. `raw/fire360/fire360_mirror` was inspected and is unrelated software/data; it is quarantined from this project role. | None locally. | `Real-Video-OOD`; only tasks justified by official visual/video annotations. | `unavailable`; official access, volume, version, license and annotation audit required. FURG is not a substitute for the name or claims. |
| MmodalFire | DOI `10.6084/m9.figshare.28804448`. | Not locally present. | Expected synchronized video, smoke density, temperature and UV/IR only after download and field inspection. | Separate real multimodal early-warning OOD; no automatic nine-task coverage. | `unavailable`; obtain official files and provenance before any claim. |
| FIgLib / SmokeyNet | Paper: `https://arxiv.org/abs/2112.08598`; source access/version/license must be resolved. | Only historical sample material exists elsewhere in the workspace, not in `raw/` as a verified official acquisition. | Unknown until official labels are verified. | Low-priority fixed-camera smoke OOD. | `unavailable`. |
| Fire-D | Zenodo record `11479478`. | Not locally present. | Satellite/remote-sensing labels only after record inspection. | Low-priority, separately reported remote-sensing extension. | `unavailable`; it must not determine primary indoor/tunnel/video OOD conclusions. |

## Production Sequence and Acceptance

1. Record a source manifest before extraction or conversion: official URL/DOI,
   acquisition time, immutable raw relative path, every-file SHA-256, raw file
   count/bytes, archive result, license evidence, original label fields and
   exact parser version. Failed archives, duplicate payloads and wrong-source
   mirrors go to `external_ood/quarantine` by manifest reference; raw files are
   not deleted in this phase.
2. Build sources independently in priority order: Immersed Tunnel, PolyUFire,
   DetectiumFire, then FURG substitute. An Event has random public IDs and
   sanitized derived paths. `event_group` is the original CFD case, experiment
   series, image identity, or complete video identity, never an arbitrary frame.
3. Generate QA only where a source field or documented deterministic rule proves
   the answer. Unsupported source/task/track combinations are reported as
   `unsupported`, not filled with placeholders. Public test questions remain
   separate from private gold answers.
4. Audit every candidate for schema/semantic validity, reference resolution,
   SHA-256, duplicate and near-duplicate leakage, event/source-group split
   leakage, option-position balance, filename/path/EXIF leakage, answer
   stability and ambiguity. For video also require decoder success, fps and PTS
   continuity, non-black frames and measured temporal change; I and V cannot
   reuse one still image as dynamic evidence.
5. Admit a source only if its source-level acceptance report records zero split
   and near-duplicate leaks, resolvable assets/hashes, real-label provenance,
   all passing validators, and all task-specific gates. Build a separate,
   self-contained external release only after the global audit passes.

## Current Gap Matrix

| Need | Current evidence | Gap | Release treatment |
|---|---|---|---|
| External CFD | Immersed raw archive/CSV present | parse and map documented controls without path leakage | candidate, not yet formal |
| Experimental bridge | PolyU workbooks present | extract units/series semantics and task eligibility | candidate, not yet formal |
| Optional visual supplement | Detectium zip present | integrity, provenance, license, annotations and extraction | raw-only |
| Real image OOD | D-Fire samples only | complete official dataset and labels | unavailable for formal release |
| Real video OOD | FURG substitute only | official Fire360 acquisition | unavailable; substitute separately reported |
| Real multimodal OOD | none | MmodalFire acquisition and modality synchronization audit | unavailable |
| Remote-sensing extension | none | Fire-D acquisition and role-specific protocol | unavailable |

## Reporting Contract

Every progress update reports: FDS Core strict-qualified count; raw count per
external source; formal qualified Events; candidates; failed/quarantined count;
the active hard gate; and the next executable step. Until a source acceptance
report passes, its formal Event and QA count is zero.
