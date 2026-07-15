---
handoff_id: H-20260716-S067-001
handoff_state: READY
task_status: BLOCKED
source_session: 2026-07-16_S067_P5-MAIN-001_reasoner输出预算与probe门禁.md
current_task: P5-MAIN-001
---

# Current Status

## 2026-07-16 P5-MAIN-001 reasoner output-budget diagnosis

- `deepseek-chat` remains the only DeepSeek model that has passed the real guarded formal probe chain.
- `deepseek-reasoner` was probed again after two hardening changes:
  - parser recovery for fenced / noisy JSON
  - larger `max_tokens` in the formal model matrix
- Even after increasing the reasoner slot to `max_tokens=1024`, the full 18-sample guarded probe still fails on many samples because the provider keeps returning `finish_reason=length`.
- This means the current risk is no longer “mysterious JSON parsing,” but a clearer engineering fact: the reasoner slot is still too output-hungry / unstable for safe quasi-experimental paid execution.
- Current reasoner probe artifacts:
  - `artifacts/p5_formal_main_probe_deepseek_reasoner_S067.json`
  - `artifacts/p5_formal_main_probe_deepseek_reasoner_S068.json`
  - `artifacts/p5_formal_main_probe_deepseek_reasoner_S069.json`

## 2026-07-16 P5-MAIN-001 API probe gate

- Formal readiness now includes an extra rule for approved OpenAI-compatible API slots:
  - an approved API model must have a recorded `PROBE_PASSED` status and a non-empty probe artifact path
- This guard is designed to prevent someone from manually marking an API model `APPROVED` and accidentally burning money on an unproven slot.
- In the current model matrix:
  - `deepseek-chat` probe status is recorded as `PROBE_PASSED`
  - `deepseek-reasoner` probe status is recorded as `PROBE_FAILED`

## 2026-07-16 formal readiness snapshot

- Latest formal readiness file: `项目治理/p5_formal_readiness_P5-MAIN-001.json`
- Latest readiness hash: `f0315c6573905b35568d6842698e0b07d2aedd932d8b2a89ce85e481a7eecb8a`
- State remains `BLOCKED_FORMAL_PREFLIGHT`
- Remaining blockers are still mainly:
  - paper-ready formal inputs
  - split / leak / uniqueness formal audits
  - approved frozen multi-model matrix
  - calibration completion
  - approved runtime and cost ceiling

## 2026-07-16 delivery state

- Core runner / probe chain has already been pushed to `origin/main`.
- Current remote HEAD is `47b5567d88ce0b9643bbac9465d4bb0ade94e919`.
- This newest reasoner-budget diagnostic step is still local until committed and pushed.
