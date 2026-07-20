# FireWorldBench FDS Core Final Repair and Acceptance Plan

Status: `FROZEN-FOR-EXECUTION`

Version: `3.1.0`

Scope: the 180-event FDS Core release only

Authoritative design: `/root/autodl-tmp/FireWorldBench/2/2.方案研究/FireWorldBenchv2(1).pdf`

Required design SHA-256: `ba63ab8428d1f759629a89864af7f623589d023dd6d5a29e4940fc6d629a19a6`

## 1. Objective

Produce one immutable FireWorldBench FDS Core release that satisfies the complete design and engineering requirements, with exactly one declared exception:

- independent fire-engineering expert review of L2-3 is deferred by user instruction;
- the release must record `expert_review_status: deferred_by_user` and must never claim that expert review occurred;
- every other scientific, data, packaging, audit, scoring, licensing, and engineering gate remains mandatory.

No partial audit, earlier acceptance report, historical artifact, or builder-written status field may substitute for the final snapshot audit.

## 2. Current Candidate and Known Defects

Current candidate: `release/fireworldbench_v3_provisional`

Current useful evidence:

- 180 independent matrix events;
- class matrix: 126 fire, 18 no-fire, 18 ventilation disturbance, 18 non-fire disturbance;
- split matrix: 96 train, 20 dev, 20 test IID, 16 geometry OOD, 14 condition OOD, 14 view/sensor OOD;
- 4,305 packaged QA: 4,071 S and 234 I;
- 117 events with dynamic I assets and 15 events with decodable V assets;
- 23 accepted L3-3 counterfactual questions;
- package-local QA and Event references currently resolve;
- public test questions hide answers.

The current candidate is not the final release because:

1. L1-1 has a time shortcut: all 72 `sensor_fault` samples use the 20-second window.
2. V assets exist but V has zero task QA and is omitted from track reporting.
3. The final 4,305-QA snapshot has no single unified fail-closed audit; the protocol audit covers the earlier 4,071-QA S snapshot.
4. Threshold stability covers only L2-2, not every thresholded task.
5. Shortcut auditing is incomplete for temporal position, option text, perceptual duplicates, visual dynamics, and hard negatives.
6. The package does not include the active schemas, frozen configs, deterministic scorer, chance/majority/rule baselines, audit reports, or reproducibility metadata.
7. The active v3 baseline report has not been generated; the existing `baselines.v2.1.json` is historical.
8. All 180 Event records currently declare `redistribution: unknown` and `NIST-generated-output-review-pending`.
9. Full `src/fireworld` engineering gates fail: Ruff, strict mypy, and three pytest tests.
10. Two deferred L2-3 items occur in test partitions and require an explicit deferred-review scoring policy.

## 3. Immutable Final Snapshot Rule

The next release is built once at:

`release/fireworldbench_fds_core_v3_1`

The builder must fail if this directory already exists. Failed partial builds are deleted only after confirming the resolved path is exactly inside `release/`.

The final audit computes a SHA-256 snapshot ID from:

- all 180 Fire Event JSON files;
- public train/dev QA;
- public hidden-answer test questions;
- private test gold;
- split manifest;
- schemas and frozen task configuration;
- scorer and baseline configuration;
- all published S/I/V assets;
- all final audit reports.

Any change to a file above invalidates acceptance. Every report must contain the same snapshot ID. Reports from a different snapshot ID are stale and cannot be used.

## 4. Repair Stages

### Stage A: Freeze Inputs and Canonical Events

1. Re-verify the core PDF SHA-256.
2. Freeze the 180-row matrix as `production_matrix.v3.1.json` without changing event count, split, or event_group.
3. Canonicalize repair provenance for all eight repaired counterfactual families.
4. Ensure one event ID maps to exactly one FDS input SHA-256 and one canonical physical trajectory.
5. Rebuild 180 Fire Event records under `fire_events/fds_core_v3_1/`.
6. Validate 100% of Event records against the v2 Fire Event schema.
7. Verify FDS 6.11.1, Smokeview 6.11.2, Python 3.11, and actual FD-Gen usage/provenance. Record `not_used` only when true.

Hard gates:

- exactly 180 Event records;
- event ID and input SHA-256 one-to-one;
- event_group split leakage zero;
- no source, HRR, ventilation, split, or answer semantics in public IDs or filenames;
- all raw/log/provenance references resolve in the controlled data root.

### Stage B: Rebuild L1-1 Without Time Shortcut

Publish exactly 72 examples for each class:

- `fire`;
- `no_fire`;
- `ventilation_disturbance`;
- `sensor_fault`.

For every class, publish exactly 18 examples at each observation endpoint: 3, 6, 10, and 20 seconds.

Sensor faults use versioned drift/stuck/spike injection. Fault type, magnitude, seed, affected channel, and source clean observation are private provenance. Public paths remain opaque.

Hard gates:

- class counts are `72/72/72/72`;
- per-class endpoint counts are `18/18/18/18`;
- endpoint and window length cannot predict class above chance beyond a documented tolerance;
- every sensor-fault payload differs from its clean source and contains no post-window samples.

### Stage C: Complete S/I/V Task Publication

S remains the principal track. I and V are published only when information is sufficient.

I:

- retain only image events with at least two distinct frame hashes and measured pixel motion;
- create balanced consistent/inconsistent L1-3 I examples from actual ordering transformations;
- maintain 2-4 time-ordered frames and opaque filenames.

V:

- use the 15 currently decodable 4-12 second videos only if motion and continuity audits pass;
- generate a consistent V example and a real transformed inconsistent V example for each eligible event;
- transformations must materialize a new video payload using local reverse, segment swap, or same-scene splice;
- publish V QA only after ffprobe decode, duration, frame-count, motion, and transformation audits pass;
- explicitly report `V: 0` for unsupported tasks instead of omitting the track.

Hard gates:

- S, I, and V all appear in coverage reporting;
- every published I/V QA references package-local assets;
- frame hashes are not all identical;
- V decodes completely and has nonzero motion;
- consistent/inconsistent distributions are balanced within each published visual task.

### Stage D: Rebuild and Stabilize All Nine Tasks

Rebuild all QA from canonical Events. Do not copy answers from the previous QA file.

Task rules remain exactly those in `docs/TASK_PROTOCOL.md`:

- L1-1: four balanced attribution classes and 3/6/10/20 second reporting;
- L1-2: real A/B/C/D candidate states from the same event and true `t + delta_t`;
- L1-3: materialized temporal transformations, 50% negative;
- L2-1: source region plus HRR-derived stage, excluding boundary samples;
- L2-2: risk region plus risk level, excluding region ties;
- L2-3: six mechanisms from frozen deterministic engineering rules, with expert review marked deferred;
- L3-1: temperature/smoke/visibility trends at 10/30/60 seconds;
- L3-2: first high-risk threshold crossing, excluding near-ties;
- L3-3: unique-variable A/B comparison with `A/B/same`, excluding small deltas.

Dataset target:

- 4,000-6,000 total QA;
- average 22-30 QA per event;
- all nine tasks represented in train/dev/test where physically supported;
- counterfactual families remain in one event_group and one split;
- test answers are private.

### Stage E: Full Stability and Ambiguity Audit

Run perturbation audits for every thresholded task:

- L2-1 stage boundaries and HRR slope buffers;
- L2-2 temperature, visibility, risk aggregation, and region tie tolerance;
- L3-1 temperature/smoke/visibility dead-bands at all horizons;
- L3-2 high-risk threshold and crossing-time tie tolerance;
- L3-3 A/B/same minimum-difference threshold.

For each task report:

- sample count;
- baseline threshold;
- lower and upper perturbations;
- flip count and flip rate;
- excluded boundary count;
- per-split flip rate.

No `ambiguous` or `excluded` sample may enter public train/dev or hidden-answer test scoring. L2-3 expert-deferred samples use a separate `eligible_expert_review_deferred` status and explicit scorer policy; they are not mislabeled as ambiguity.

### Stage F: Comprehensive Shortcut and Leakage Audit

Required checks:

1. event_group cross-split leakage;
2. exact file duplicate leakage;
3. perceptual image duplicate leakage using pHash/SSIM;
4. video near-duplicate and adjacent-segment leakage;
5. counterfactual family leakage;
6. filename, path, metadata, EXIF, codec tag, and context leakage;
7. L1-1 endpoint and window-length label predictability;
8. L1-2 answer-position balance, option text length, style, and candidate-time balance;
9. L1-3 transformation artifact balance;
10. label versus observation-time shortcut;
11. visual brightness, smoke amount, and background shortcut;
12. hard-negative physical distinguishability and visual similarity;
13. train-only threshold/config fitting;
14. test answer and gold-reference absence from the public package.

Hard gates:

- cross-split event_group overlap zero;
- public test answer leakage zero;
- forbidden filename/path/EXIF leakage zero;
- A/B/C/D position spread at most 2%;
- exact duplicate cross-split leakage zero;
- every detected shortcut is either repaired or the affected QA is removed.

### Stage G: Baselines, Scorer, and Reproducibility

Generate v3.1 results for:

- chance baseline;
- train-split majority baseline;
- frozen deterministic rule baseline;
- oracle self-check, clearly marked and excluded from benchmark results.

Package the deterministic scorer and configuration. Verify:

- all nine task scores;
- L1/L2/L3 macro averages;
- Overall nine-task macro average;
- Component Accuracy for L2-1/L2-2;
- Mean Accuracy for L3-1;
- no LLM Judge;
- scores reproduce from raw predictions.

### Stage H: Licensing and Redistribution Evidence

Resolve the current `redistribution: unknown` state using authoritative NIST/FDS licensing evidence and generated-output redistribution scope.

Hard gates:

- all 180 Event records use a non-placeholder license ID;
- evidence file and citation resolve inside the package;
- allowed uses and redistribution status are explicit;
- if public redistribution cannot be established, the release is marked internal-only and cannot be described as a public dataset release.

This gate is not covered by the expert-review exception.

### Stage I: Engineering Gates

Run against the complete active implementation, not only newly added files:

```bash
ruff check src/fireworld tests
mypy --strict src/fireworld
pytest -q
```

Hard gates:

- Ruff exit code 0;
- strict mypy exit code 0;
- pytest exit code 0;
- no skipped final-release contract test;
- release builder is idempotent in content and fails safely on an existing immutable target directory.

Legacy `src/fireworldbench/` is excluded by project authority. Active `src/fireworld/` is not excluded.

### Stage J: Self-Contained Package and Final Audit

The final package must include:

```text
release/fireworldbench_fds_core_v3_1/
  release_manifest.json
  public/
    fire_events/
    derived/S/
    derived/I/
    derived/V/
    qa_train_dev.json
    qa_test_questions.json
    production_matrix.v3.1.json
    schemas/
    configs/
    scorer/
    baselines/
    reports/
    LICENSE_EVIDENCE.md
  private/
    qa_test_gold.json
    scoring_config.json
```

Final audit reads only this package. It must not resolve a path through the workspace root.

Final audit checks:

- package-local reference resolution;
- Event and QA schema/semantic validation;
- exact counts by event, class, task, track, split, and source;
- all Stage A-I hard gates;
- manifest hashes for every package file;
- public/private separation;
- scorer replay and baseline replay;
- report snapshot IDs match the final snapshot ID.

## 5. Acceptance Semantics

Only the final audit may set release status.

Allowed statuses:

- `blocked_by_final_audit`;
- `provisionally_accepted_expert_review_deferred`;
- `formally_accepted` after independent expert review is later completed.

`provisionally_accepted_expert_review_deferred` is allowed only when:

- every non-expert hard gate in this document is true;
- the only false gate is `mechanism_independent_review_complete`;
- L2-3 records explicitly carry the deferred status;
- no other pending, unknown, placeholder, stale, ambiguous, failed, or missing item remains.

The phrases “complete except expert review” and “all other design goals achieved” are prohibited unless the final package audit produces this exact status for the same snapshot ID.

## 6. Execution Order and Stop Rules

Execute strictly in this order:

1. Stage A canonical snapshot;
2. Stage B time-shortcut repair;
3. Stage C I/V rebuild;
4. Stage D nine-task rebuild;
5. Stage E stability/ambiguity;
6. Stage F shortcut/leakage;
7. Stage G scorer/baselines;
8. Stage H licensing;
9. Stage I full engineering gates;
10. Stage J packaging and final audit.

Any failed hard gate stops progression to final packaging. Repair the cause, rebuild the candidate from canonical inputs, invalidate stale reports, and rerun all downstream stages. Do not patch an acceptance JSON manually.

## 7. Required Final Report

The final handoff must state:

- snapshot ID;
- release status;
- strict/provisional qualified event count;
- physical candidate count;
- failed and quarantined run count;
- QA counts by task/track/split;
- I/V eligibility and dynamic audit counts;
- counterfactual family count;
- stability and ambiguity rates;
- shortcut/leakage results;
- baseline results;
- scorer replay result;
- license status;
- Ruff/mypy/pytest results;
- expert-review deferred count;
- exact release path.

No completion claim is valid without this report and a matching final audit snapshot ID.
