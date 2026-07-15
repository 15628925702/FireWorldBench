---
handoff_id: H-20260716-S065-001
handoff_state: READY
task_status: BLOCKED
source_session: 2026-07-16_S065_P5-MAIN-001正式runner与DeepSeek探测.md
current_task: P5-MAIN-001
---

## Authoritative next window: P5-MAIN-001

The formal execution chain is no longer just a blocker report. A guarded CLI path now exists:

- `formal-main-probe`
- `formal-main-run`

and `deepseek-chat` has already passed the real guarded probe path on 18 visible dev samples via `artifacts/p5_formal_main_probe_deepseek_S066.json`.

The next window must continue `P5-MAIN-001` by closing or precisely reconfirming the remaining formal preflight blockers, not by rerunning old research scripts. Read, in order:

1. `AGENTS.md`
2. `进度跟进记录/CURRENT_STATUS.md`
3. `进度跟进记录/2026-07-16_S065_P5-MAIN-001正式runner与DeepSeek探测.md`
4. `项目治理/p5_formal_input_audit_P5-MAIN-001.json`
5. `项目治理/p5_formal_readiness_P5-MAIN-001.json`
6. `configs/model_matrix_P5-MAIN-001.json`
7. `configs/runtime_P5-MAIN-001.json`
8. `configs/calibration_P5-MAIN-001.json`
9. `configs/prereg_P5-MAIN-001.json`
10. `configs/formal_run_P5-MAIN-001.json`

The current engineering state is:

- real formal probe path exists and DeepSeek has passed it
- real formal full-run command exists in code, but must not be executed before readiness reaches `READY_FOR_FORMAL_MULTI_MODEL_FULL_RUN`
- remaining blockers are mainly external evidence/approval blockers, plus incomplete approved-model coverage and calibration closure

Do not rerun:

- `scripts/run_research_deepseek.ps1`
- the old research DeepSeek artifacts

Do not:

- download new data or models without explicit authorization
- install new packages
- access hidden test/private assets
- start `formal-main-run` while readiness is still blocked

When readiness is eventually closed, the intended command shape is:

`python -m fireworldbench.cli formal-main-run --root <repo_root> --samples <paper_ready_inputs.json> --model-matrix configs/model_matrix_P5-MAIN-001.json --readiness 项目治理/p5_formal_readiness_P5-MAIN-001.json --model-id <approved_model_id> --output-root artifacts/formal_runs/<run_id>`

Until then, the only valid objective is to improve or verify the frozen evidence chain so that the future formal run is safe, reproducible, and unlikely to waste paid API budget.

