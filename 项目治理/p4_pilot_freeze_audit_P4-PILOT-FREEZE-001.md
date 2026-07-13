# P4-PILOT-FREEZE-001 audit

## Decision

The pilot matrix and its guardrails are frozen before any paper-ready
generation. The plan is formally `BLOCKED_PENDING_APPROVAL` because complete
model IDs, runtime/API budget, and a frozen train/dev sample manifest are not
available. This is a planning block, not a model-performance result.

The main matrix contains `text_only_table` and `retrieval`. The exploratory
matrix contains `multimodal`, `plot`, `formula_fds_proxy`, and `tool_use`.
The two matrices are disjoint and retain separate information budgets.

## Frozen rules

- Only `train_id` and `dev_id` may be used.
- Repetitions are one for both primary and exploratory tracks until approval.
- Sample counts and monetary cap remain `null` rather than invented numbers.
- Input/output token caps, retry count, wall-time cap, and failure rules are explicit.
- Model and prompt selection is frozen without test performance; no post-freeze selection is allowed.
- Test access ledger is `NO_ACCESS_CONFIRMED`; test assets were not read.

## Next gate

P5-FDGEN-001 may only generate controlled scenes after the P4 plan blockers are
resolved or formally accepted by governance. Any change to this matrix must
invalidate the downstream pilot freeze and create a new version.
