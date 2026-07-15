---
handoff_id: H-20260716-S066-001
handoff_state: READY
task_status: BLOCKED
source_session: 2026-07-16_S066_P5-MAIN-001_DeepSeek双模型formal探测.md
current_task: P5-MAIN-001
---

## Authoritative next window: P5-MAIN-001

The formal execution chain is now materially stronger than before:

- a guarded `formal-main-probe` command exists
- a guarded `formal-main-run` command exists
- `deepseek-chat` has passed the real formal probe chain
- `deepseek-reasoner` has failed the same probe due repeated non-JSON / malformed-JSON outputs

This means the next window must treat `deepseek-chat` as the currently validated API-backed formal probe candidate, and treat `deepseek-reasoner` as still unstable until a stronger JSON-enforcement / parser / provider-side strategy is proven.

Read, in order:

1. `AGENTS.md`
2. `进度跟进记录/CURRENT_STATUS.md`
3. `进度跟进记录/2026-07-16_S066_P5-MAIN-001_DeepSeek双模型formal探测.md`
4. `项目治理/p5_formal_input_audit_P5-MAIN-001.json`
5. `项目治理/p5_formal_readiness_P5-MAIN-001.json`
6. `configs/model_matrix_P5-MAIN-001.json`
7. `configs/runtime_P5-MAIN-001.json`
8. `configs/calibration_P5-MAIN-001.json`
9. `configs/prereg_P5-MAIN-001.json`
10. `configs/formal_run_P5-MAIN-001.json`

Next priority order:

1. Retry `git push origin main` until the already-validated local delivery is on remote.
2. Continue `P5-MAIN-001` by closing or reconfirming the remaining formal preflight blockers.
3. If a second paid model slot is still desired, either:
   - harden `deepseek-reasoner` further until probe passes, or
   - switch the second slot to another model that can satisfy the same guarded probe contract.

Do not:

- rerun `scripts/run_research_deepseek.ps1`
- start `formal-main-run` while readiness is still blocked
- access hidden test/private assets
- download new data/models or install new packages without explicit authorization

Current future full-run command shape:

`python -m fireworldbench.cli formal-main-run --root <repo_root> --samples <paper_ready_inputs.json> --model-matrix configs/model_matrix_P5-MAIN-001.json --readiness 项目治理/p5_formal_readiness_P5-MAIN-001.json --model-id <approved_model_id> --output-root artifacts/formal_runs/<run_id>`

