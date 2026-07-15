---
handoff_id: H-20260716-S069-001
handoff_state: READY
task_status: BLOCKED
source_session: 2026-07-16_S069_P5-MAIN-001_准实验交付固化.md
current_task: P5-MAIN-001
---

## Authoritative next window: P5-MAIN-001

The project has crossed into quasi-experiment readiness, but formal full-run is still blocked.

Validated API slots:

- `deepseek-chat`
- `deepseek-v4-pro` with `thinking.type=disabled`

Rejected current slot:

- `deepseek-reasoner`

Read:

1. `AGENTS.md`
2. `进度跟进记录/CURRENT_STATUS.md`
3. `进度跟进记录/2026-07-16_S069_P5-MAIN-001_准实验交付固化.md`
4. `项目治理/p5_quasi_experiment_readiness_P5-MAIN-001.json`
5. `项目治理/p5_formal_readiness_P5-MAIN-001.json`
6. `configs/model_matrix_P5-MAIN-001.json`

Next priorities:

1. Continue formal input freeze and paper-ready input closure.
2. Continue calibration closure.
3. Continue runtime / cost-ceiling approval-pack preparation.
4. Continue shrinking model-matrix blockers until only explicit external approvals remain.

Do not:

- start `formal-main-run` while readiness is blocked
- reintroduce `deepseek-reasoner` without a future passing probe
- go back to research-script validation instead of formal blockers

