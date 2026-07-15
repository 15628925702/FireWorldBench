---
handoff_id: H-20260716-S068-001
handoff_state: READY
task_status: BLOCKED
source_session: 2026-07-16_S068_P5-MAIN-001_准实验就绪判定.md
current_task: P5-MAIN-001
---

## Authoritative next window: P5-MAIN-001

The project should now be treated as quasi-experiment ready but not formal-full-run ready.

Validated API slots:

- `deepseek-chat` → guarded probe passed
- `deepseek-v4-pro` with `thinking.type=disabled` → guarded probe passed

Rejected for current paid formal use:

- `deepseek-reasoner` → repeated `finish_reason=length`

Read:

1. `AGENTS.md`
2. `进度跟进记录/CURRENT_STATUS.md`
3. `进度跟进记录/2026-07-16_S068_P5-MAIN-001_准实验就绪判定.md`
4. `项目治理/p5_quasi_experiment_readiness_P5-MAIN-001.json`
5. `项目治理/p5_formal_readiness_P5-MAIN-001.json`
6. `configs/model_matrix_P5-MAIN-001.json`

Next priorities:

1. Commit and push this quasi-readiness consolidation.
2. Continue eliminating `P5-MAIN-001` blockers that remain inside repository scope.
3. Treat the next real transition point as:
   - formal inputs become paper-ready
   - calibration completes
   - runtime and cost ceiling are approved/frozen
   - matrix status can move from blocked to approved without violating probe-gate rules

Do not:

- start `formal-main-run` while readiness is still blocked
- reintroduce `deepseek-reasoner` as a paid formal slot without a passing probe
- rerun research scripts instead of formal blockers

