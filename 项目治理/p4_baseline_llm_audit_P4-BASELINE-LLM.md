# P4-BASELINE-LLM audit

## Decision

The LLM baseline contract is implemented, but the current pilot is formally
`BLOCKED`: no approved complete model ID, API budget, or reproducible model
runtime is available. The repository therefore contains configuration and
adapter contracts, not fabricated model results.

Two separate tracks are frozen in the registry:

- `text_only_table`: text/table input, no visual asset dependency.
- `multimodal`: requires approved visual assets and a multimodal model.

Both tracks freeze prompt ID, few-shot list, temperature, top-p, input/output
token budgets, retries, timeout, cost fields, and a deterministic config hash.
The pilot report has explicit variance, cost, and failure fields.

## Boundary and claims

- Only explicit `train_id` and `dev_id` samples are accepted.
- Test input, test gold, private mapping, and test-based prompt/model selection
  are not available to the adapter.
- `BLOCKED` is a resource/approval state, not an accuracy result.
- A future approved run must report text/table and multimodal tracks separately;
  their information budgets must not be mixed or jointly ranked.

## Verification

Contract tests exercise deterministic freezing, blocked behavior, train/dev
boundary refusal, and a local callback-only mock for variance/cost reporting.
The mock is a unit-test adapter and is not a model result.
