# FireWorldBench v2 Finalization Acceptance

Status: `IN_PROGRESS_FAIL_CLOSED`

## Immutable FDS Core

- Release: `fireworldbench_fds_core_v3_3_1`
- Snapshot: `496f2aeb9deefd6bc51c9b56546519addfb87b22e5bc7b1775c1f865c8e63f39`
- Strict-qualified Events: `180/180`
- QA: `4,039`
- Read-only verifier: `8,209` manifest files checked, all hashes matched.
- Public test answers: `1,438/1,438` records are redacted.

## Current Gates

| Gate | State | Evidence |
|---|---|---|
| Source/task/track eligibility | pass | `fireworld.coverage` reports 270 combinations; only FDS is formal. |
| Prediction/gold binding | pass | semantic validator and scorer reject unknown or mismatched predictions. |
| Deterministic scoring | pass | task/layer/track/source/split breakdowns are reproducible. |
| Model runner dry-run | pass | `openai/gpt-4o-mini`, 1,360 public S rows, manifest recorded. |
| API smoke run | blocked | OpenRouter-compatible request returned HTTP 403; no prediction/result admitted. |
| External formal package | blocked | formal Events/QA remain zero by frozen data status. |
| FDS overall | pass | external rows are never averaged into Overall. |

## Final Acceptance Requirements

1. Run full suite, lint and static checks in the server environment.
