# P5-MAIN-001 formal preflight audit

## Decision

The formal main run remains `BLOCKED_FORMAL_PREFLIGHT`. The repository now has
an executable evidence gate and a complete blocked-state declaration chain, but
the evidence does not support `READY_FOR_FORMAL_MULTI_MODEL_FULL_RUN`.

No formal model run was started, no formal result or paper number was generated,
and no planning result was promoted to formal evidence.

## Data evidence

- D01 upstream tree declares 192 CSV files (1,703,976,822 bytes); 9 are locally
  staged and 183 are missing. Every staged file has a relative path, byte size,
  and SHA-256 in `p5_formal_input_audit_P5-MAIN-001.json`.
- D02 format integration is closed: 8 XLSX and all 80 legacy XLS files enter the
  canonical probe. The fresh build produced 82,444 records and retained 17
  unsupported-file failures.
- Fresh canonical results are D01 5,409 records / 4 failures, D02 82,444 / 17,
  and D03 932 / 2. These are data-processing results, not model results.
- D04 has no approved generator runtime; D05 and D10 remain visual auxiliary
  sources; D06-D09 and D11 have no staged formal inputs.
- D01-D11 all remain formally ineligible because license/source-version evidence
  is blocked. No paper-ready case manifest, group-first split audit, leak audit,
  or uniqueness audit exists. Formal input file count is therefore zero.

## Model and runtime evidence

- Five candidate rows now expose every required model/runtime/budget/capability
  field. None is approved: exact immutable versions, tokenizer versions, pricing,
  budgets, prompt hashes, and verified nine-task support are absent.
- No supported API credential environment variable is present. No candidate
  Qwen/Llama checkpoint is present in the local model cache.
- The observed GPU is an RTX 4050 Laptop GPU with 6,141 MiB. The formal
  `fireworldbench-v1` Conda environment exists but is empty; verification used
  base Python 3.13.5 and is not formal runtime acceptance.

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
  `aaf86dba8465ff8878cf948a453873120b1a428c6f2482b2446784a99b8c4d11`.
- Frozen input audit file hash:
  `a93028ac8f1729244d2c4b03832cd8cdf648d0f9f5b94e04356c408a0261d67e`.
- Model matrix hash:
  `71a65e93f2cf9e5b2c4c44b0ff1c3a05a4f6eeb77e851ff9e9240d05d111230f`.
- Calibration declaration hash:
  `67eeb278592669967de4a780f390e4281fbc5af1d2638f982f3d429847ad5fd6`.
- Preregistration hash:
  `a56972d41541c213e1238157ab79a5c9a0c76c9b59cc7671ce621c40bf09a6d7`.
- Runtime declaration hash:
  `cfbf417decc0a599c24ca2f247a8ae3ac102cb58230c631da8ab3b0bcb4040bd`.
- Run contract hash:
  `aa2c0dfb1e53b7fd87af29b0ed96e7dc31d88dcd06b0b82c4f4acfbe7729dab3`.
- Readiness manifest hash:
  `2dbdb7c35890c36c9bbd32c64596ebda9181fa05647e88a3aaa7fa1681e22fbf`.

## Safety boundary

- Formal full-run command: not issued; `command_status = BLOCKED_DO_NOT_EXECUTE`.
- API calls and budget use this session: none / USD 0.
- Test/private access: none.
- Raw data outside the repository modified: no.
- Formal run directories, raw responses, model results, and paper numbers: none.
