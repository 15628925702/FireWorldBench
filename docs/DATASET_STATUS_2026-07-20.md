# Dataset Status 2026-07-20

Status: `FDS_CORE_FORMAL_EXTERNAL_OOD_PARTIAL_CANDIDATE`

This document is the factual dataset handoff for v2 finalization work. The
sole design authority is `FireWorldBenchv2(1).pdf`, SHA-256
`ba63ab8428d1f759629a89864af7f623589d023dd6d5a29e4940fc6d629a19a6`.
It supersedes only external-data status statements that conflict with it.

## Formal Core

`/root/autodl-tmp/FireWorldBench/2/release/fireworldbench_fds_core_v3_3_1`
is read-only for all later work. It is formally accepted with 180/180 strict
qualified FDS Events and 4,039 QA. It remains the sole main leaderboard and
Overall evidence package.

## External Inventory

| Package/source | State | Audited body | Permitted role now | Not permitted |
|---|---|---|---|---|
| Immersed Tunnel CFD | candidate | 192 parseable structured CSV cases, about 13 GB | External-CFD candidate S assets and private provenance mapping | Formal QA/release until source/task rules and acceptance pass |
| PolyUFire | candidate | seven XLSX workbooks, about 94 MB; workbook and database-row audit | Experimental candidate S evidence | Treating cross-study/range rows as Event truth or full-field labels |
| FURG fire videos | candidate substitute | 23 MP4 + 23 XML, about 1.2 GB; all decode, all XML align, dynamic samples pass | `Real-Video-OOD-Substitute`, video-level group-first split, future L1-3 and positive-box evidence | Naming it Fire360; treating no-box XML frames as no-fire |
| Kaggle video supplement | candidate substitute | ZIP integrity passes; `markup.json` plus three MP4, not 85 videos | Small video substitute supplement after source manifest | Claiming it contains 85 videos |
| Synthetic smoke supplement | raw substitute | small repository with at least one AVI and one no-fire image | Pipeline/negative-control supplement only | Calling it a broad real-video OOD set |
| DeepQuest Fire-Smoke | downloading substitute | official GitHub release confirmed at 320,963,592 bytes; server direct download in progress | Future `Real-Image-OOD-Substitute` after completed archive audit | Naming it D-Fire or using before full download/audit |
| D-Fire | raw sample only | repository metadata and six local sample images | Provenance reference only | Full D-Fire claim or formal image OOD |
| Detectium archive | quarantined | 96 GB archive integrity passed; central directory includes unverified/wrong `preference_dataset` and `synthetic_images` trees | Retained forensic raw only | Extracting or using for Events/QA/release |
| Fire360 official | unavailable | no official media locally | Honest gap | Replacing with FURG under Fire360 name |
| MmodalFire | metadata confirmed, body unavailable | official DOI, Spring Nature Figshare, CC BY 4.0; article API returned 403 | Honest multimodal gap | Claiming synchronized modalities are available |
| FIgLib/SmokeyNet | sample only | local sample only | Honest fixed-camera gap | Full-source or formal OOD claim |
| Fire-D | unavailable | no local body | Low-priority honest gap | Affecting primary indoor/tunnel/video conclusion |

## FURG Annotation Rule

FURG has 23 XML files, 28,049 frame records, 14,413 records with rectangle
content, 13,636 records without rectangle content, zero duplicate frame
records, and zero missing XML files. A rectangle is positive visible-flame
evidence. No rectangle means `unknown/unscored`, not `no_fire`. It may remain
in video context and temporal-coherence inputs but cannot contribute a
fire-versus-no-fire negative label, false-positive count, or precision score.

## External Production Counts

- Formal external Events: 0
- Formal external QA: 0
- Immersed structured candidates: 192
- FURG candidate video groups: 23
- Known quarantined sources: 2 (`fire360_mirror`, Detectium archive)
- FDS Core strict-qualified Events: 180/180

## Finalization Rules

1. Continue only in `src/fireworld/`; `src/fireworldbench/` is legacy.
2. Raw, candidates, derived S/I/V, Events, QA, splits, reports, quarantine and
   releases remain separate. A raw asset is never a formal Event or QA.
3. External sources are separately reported and never enter FDS Overall.
4. A substitute resolves engineering coverage only under its own source name.
   It cannot be renamed as D-Fire, Fire360, MmodalFire, FIgLib, or Fire-D.
5. Deferred license/contact confirmation is not a passing acceptance result.
   Record it as `deferred_external_confirmation` and preserve evidence.
6. Do not generate QA when the answer is not supported by source annotation or
   a documented deterministic transform. Unsupported combinations remain zero.

## Next Non-Data Work

Build the v2 finalization around the accepted FDS Core plus isolated external
candidate packages: finish validators, builders, split/leak checks, scorer
separation, reports, data cards, and release scaffolding. The first eligible
external QA should be FURG L1-3 temporal coherence, where the label comes from
the deterministic intact/reordered/reversed clip transform, not no-box frames.
