# P4-TOOL-001 audit

## Decision

The retrieval, plot, formula/FDS-proxy, and general tool-use tracks are frozen
as separate information budgets. Each track has an immutable knowledge-base
identity, an explicit tool whitelist, maximum calls, maximum cost units, and a
replayable trace schema.

The current tool ablation is formally `BLOCKED` because no approved model or
tool runtime is available. A local callback is used only in contract tests to
verify sandbox behavior; it is not a model result.

## Track separation

- `retrieval`: only `knowledge_base_lookup`.
- `plot`: only `plot_series`.
- `formula_fds_proxy`: only `formula_eval` and `fds_proxy`.
- `tool_use`: the explicitly frozen four-tool whitelist, with a larger declared budget.

Reports retain one result and one trace per track. They set
`budget_mixing=false` and `joint_ranking=false`; tracks must not be placed on a
single leaderboard. Every accepted or rejected call is recorded, and successful
outputs can be replayed and hash-checked without external calls.

## Boundary

- Only explicit `train_id` and `dev_id` samples are accepted.
- Test input, test gold, private mapping, and `../../3.数据集` are not read or modified.
- No package, model, data, or remote configuration was installed or downloaded.
