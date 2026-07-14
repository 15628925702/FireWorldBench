---
handoff_id: H-20260714-S055-001
handoff_state: READY
task_status: READY
session_id: 2026-07-14_S055
task_id: P4-PILOT-RUN
next_task: P5-STATISTICS
started_at: 2026-07-14 Asia/Shanghai
---

# P4-PILOT-RUN DeepSeek local smoke test

## Initial repository state

- Branch: `main`
- HEAD: `4b02d93`
- Scope: local planning D01 only, dev_id only, no test/private access.

## Objective and budget

Run a minimal end-to-end chain from raw FDS CSV to canonical planning records, T1 samples, DeepSeek predictions, and reference scores. The API key is process-only and is never written to a file. Limit the final run to four requests with a 180-token output cap per request.

## Completion

- Built 12 canonical planning records from two D01 CSV cases, then created four `dev_id` samples for T1-A/T1-B.
- DeepSeek `deepseek-chat` completed 4/4 capped requests; aggregate provider usage was 10,714 input and 503 output tokens.
- Reference scoring: T1-A = 1.0 over 2 samples; T1-B = 1.0 over 2 samples; no parse failures or evidence violations.
- T1-C was excluded because a full-context prompt cannot fairly evaluate its interactive next-observation action.
- The key was process-only; raw files/test-private assets were untouched. Full local artifacts remain under ignored `artifacts/planning_pilot/` and their hashes are in the governance report.
- Next task: `P5-STATISTICS` for the local smoke-test outputs only.
