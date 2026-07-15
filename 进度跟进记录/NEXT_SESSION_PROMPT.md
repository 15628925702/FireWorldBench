---
handoff_id: H-20260716-S067-001
handoff_state: READY
task_status: BLOCKED
source_session: 2026-07-16_S067_P5-MAIN-001_reasoner输出预算与probe门禁.md
current_task: P5-MAIN-001
---

## Authoritative next window: P5-MAIN-001

The project is now closer to quasi-experimental readiness than before, but the next window must preserve a crucial distinction:

- `deepseek-chat` is a validated API-backed formal probe candidate
- `deepseek-reasoner` is still not safe for formal paid use, even after parser hardening and a larger output budget

The next window should read:

1. `AGENTS.md`
2. `进度跟进记录/CURRENT_STATUS.md`
3. `进度跟进记录/2026-07-16_S067_P5-MAIN-001_reasoner输出预算与probe门禁.md`
4. `项目治理/p5_formal_readiness_P5-MAIN-001.json`
5. `configs/model_matrix_P5-MAIN-001.json`
6. `artifacts/p5_formal_main_probe_deepseek_S066.json`
7. `artifacts/p5_formal_main_probe_deepseek_reasoner_S069.json`

Priority order:

1. Commit and push the latest reasoner-budget / probe-gate updates.
2. Continue closing `P5-MAIN-001` blockers that are still inside repository scope.
3. For the second formal model slot, prefer one of these two paths:
   - replace `deepseek-reasoner` with another model and force it through the same guarded probe chain
   - only keep `deepseek-reasoner` if it can eventually achieve `PROBE_PASSED` under a bounded and acceptable output budget

Do not:

- start `formal-main-run` while readiness is still blocked
- treat `deepseek-reasoner` as an approved slot based on partial probe success
- rerun old research scripts
- access hidden test/private assets

