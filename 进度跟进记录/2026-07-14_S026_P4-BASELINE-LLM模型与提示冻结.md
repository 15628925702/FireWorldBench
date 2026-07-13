---
handoff_id: H-20260714-S026-001
handoff_state: READY
task_status: READY
session_id: 2026-07-14_S026
task_id: P4-BASELINE-LLM
next_task: P4-TOOL-001
started_at: 2026-07-14 Asia/Shanghai
---

# P4-BASELINE-LLM session record

## Git baseline before edits

- branch: `main`
- HEAD: `e49ecac87df3896e5e963a79006b1c8ac329bb6d`
- remote: `origin https://github.com/15628925702/FireWorldBench.git`
- staged: none
- unstaged: none
- untracked: none
- existing changes: none; previous task is cleanly committed and pushed.

## Objective

Freeze text-only/table and compliant multimodal adapter contracts, including
model identity, prompt, few-shot, sampling, retries, parser, budget, and
train/dev-only pilot boundaries. The current environment has no approved model
ID or API budget, so no model result may be fabricated.

## Constraints

- Do not read test input, test gold, private mapping, or `../../4.升级拓展`.
- Do not modify `../../3.数据集`; do not install or download packages, models, or data.
- No test-based prompt/model selection and no mixing of information budgets.

## Delivery

- Added `src/fireworldbench/llm_baseline.py`, frozen prompt/model registries, deterministic config hashing, adapter boundary, and train/dev-only pilot reporting.
- Added separate `text_only_table` and `multimodal` tracks with explicit token, sampling, retry, timeout, and cost fields.
- Current result is formally `BLOCKED` because no approved model ID, API budget, or reproducible runtime is available. No model result was fabricated.
- Added the frozen config, governance audit, CLI command, and three contract tests.
- Verification: `pytest` 56 passed; `mypy` passed; source-path `llm-pilot` CLI returned `BLOCKED`; project check is required before commit.

## Closing Git snapshot

- local commit before amendment: `cd85927486d7aad7cc4a3a50dde4ec766433d912`
- branch: `main`
- post-commit staged / unstaged / untracked: `0 / 0 / 0`
- push verification was initially blocked by GitHub port 443; resolved when the later task chain pushed through `96ece1811e0c9dfabfce580eeb0f308ddea862e7`.

## Push block

- Local implementation commit: `f0a25ceecc07fa7cc4de7051d71ddc9b92838618`.
- The task was locally complete at `f0a25ceecc07fa7cc4de7051d71ddc9b92838618` and is now included in the verified remote chain.

## Next task

`P4-TOOL-001`: freeze retrieval, plot, formula/FDS proxy, and tool-use tracks as separate information budgets with a whitelist, call limits, replayable traces, dev ablations, and cost/failure reporting.
