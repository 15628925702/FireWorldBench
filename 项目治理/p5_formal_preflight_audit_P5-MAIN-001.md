# P5-MAIN-001 formal preflight audit

## Decision

The formal main run remains `BLOCKED_FORMAL_PREFLIGHT`. The repository now has
an executable evidence gate and a complete blocked-state declaration chain, but
the evidence does not support `READY_FOR_FORMAL_MULTI_MODEL_FULL_RUN`.

No formal model run was started, no formal result or paper number was generated,
and no planning result was promoted to formal evidence.

## Data evidence

- D01 upstream tree declares 192 CSV files (1,703,976,822 bytes); all 192 are
  locally staged and verified by byte size plus upstream Git blob SHA. Every
  staged file has a relative path, byte size, and SHA-256 in
  `p5_formal_input_audit_P5-MAIN-001.json`.
- D02 format integration is closed: 8 XLSX and all 80 legacy XLS files enter the
  canonical probe. The fresh build produced 82,444 records and retained 17
  unsupported-file failures.
- Fresh canonical results are D01 5,409 records / 4 failures, D02 82,444 / 17,
  and D03 932 / 2. These are data-processing results, not model results.
- D04 has no approved generator runtime; D05 and D10 remain visual auxiliary
  sources; D06-D09 and D11 have no staged formal inputs.
- D01-D11 all remain formally ineligible (`eligible=false`). D01/D02 still lack
  authoritative dataset licenses; D03 data-license scope is unresolved; and
  D01-D05/D10 still lack exact local-snapshot binding. D04/D05/D10 now have
  stronger official use/license evidence, but no source has been approved for
  the formal benchmark. No paper-ready case manifest, group-first split audit,
  leak audit, or uniqueness audit exists. Formal input file count is zero.

## Model and runtime evidence

- Five candidate rows now expose every required model/runtime/budget/capability
  field. None is approved: exact immutable versions, tokenizer versions, pricing,
  budgets, prompt hashes, and verified nine-task support are absent.
- No supported API credential environment variable is present. No candidate
  Qwen/Llama checkpoint is present in the local model cache.
- The observed GPU is an RTX 4050 Laptop GPU with 6,141 MiB. The
  `fireworldbench-v1` Conda environment now has Python 3.11.15, the project,
  jsonschema, xlrd, pytest, mypy, and Ruff installed; `pip check` passes.

## Calibration and preregistration

- The calibration protocol freezes structured JSON, prediction Schema v2,
  parser version, train/dev-only threshold policy, unknown handling, and failure
  rules. Calibration was not executed because paper-ready train/dev inputs,
  approved models, and an approved runtime are absent; results and config hash
  remain empty.
- Preregistration v1 freezes hypotheses, all nine primary metrics, secondary
  metrics, track separation, repetitions, seeds, aggregation, exclusions,
  stopping/failure rules, robustness, ablations, embargo, immutable run paths,
  and paper-number provenance. The formal cost ceiling is intentionally unset
  pending approval.

## Hash chain

- Formal input audit canonical hash:
  `42c9952b29d179524d356b9812e4a7af10b577f984c2f18c57e7699765719912`.
- Frozen input audit file hash:
  `8ae6484d599d4fdd2e37738b902892962aaccd6a2d66daccbd2952ea82f02573`.
- Model matrix hash:
  `69b9751d466b26e309d6de61d5b37999b15cc1ca98c64240db8f2e79cce4c7bf`.
- Calibration declaration hash:
  `67eeb278592669967de4a780f390e4281fbc5af1d2638f982f3d429847ad5fd6`.
- Preregistration hash:
  `a56972d41541c213e1238157ab79a5c9a0c76c9b59cc7671ce621c40bf09a6d7`.
- Runtime declaration hash:
  `1436ebc9d2f84c03d16e7e1d1aa5ee9e3e13632ab357da886c6abb1a976ff99b`.
- Run contract hash:
  `aa2c0dfb1e53b7fd87af29b0ed96e7dc31d88dcd06b0b82c4f4acfbe7729dab3`.
- Readiness manifest hash:
  `5a05ff3465788249fef17ec6045ce46a967952172549d68bcc7e5116539ced73`.

## Safety boundary

- Formal full-run command: not issued; `command_status = BLOCKED_DO_NOT_EXECUTE`.
- API calls and budget use this session: none / USD 0.
- Test/private access: none.
- Raw data outside the repository modified: no.
- Formal run directories, raw responses, model results, and paper numbers: none.

## S072 evidence update (2026-07-16)

- Downloaded and verified 28 additional open-access papers/official technical
  documents. The complete local collection now contains 44 PDFs with 44 unique
  SHA-256 values; see `literature_manifest_S072.json`.
- Verified official remote heads for D01-D05 and captured commit-pinned source
  or license evidence for D01-D05 plus the official D10 HPWREN use terms.
- D01/D02 still have no authoritative dataset license. D03 has a NIST software
  license whose applicability to experiment data remains unresolved. D04
  software use, D05's official CC0 collection notice and D10 attribution terms
  now have stronger evidence, but no raw source was promoted to formal input.
- Regenerated the formal input audit: detailed blockers decreased from 43 to 39,
  but `formal_input_file_count` remains 0 and status remains
  `BLOCKED_NO_PAPER_READY_FORMAL_INPUTS`.
- Regenerated formal preflight: status remains `BLOCKED_FORMAL_PREFLIGHT` with
  26 blockers. Readiness manifest hash is
  `5a05ff3465788249fef17ec6045ce46a967952172549d68bcc7e5116539ced73`.
- No API credential is present in the current environment. No paid call or
  formal run was started.
