---
handoff_id: H-20260716-S066-001
handoff_state: READY
session_id: 2026-07-16_S066
task_id: P5-MAIN-001
next_task: P5-MAIN-001
---

# 2026-07-16_S066_P5-MAIN-001 DeepSeek双模型formal探测

## 1. 会话目标

在上一轮已经让 `deepseek-chat` 通过真实 formal probe 之后，本轮继续验证第二个 DeepSeek 候选是否也足够稳，避免把“第二个模型位”直接带进正式付费 full-run 后才暴露接口问题。

## 2. 本轮完成

- 对 `src/fireworldbench/deepseek.py` 增加了更稳健的 JSON 提取逻辑：
  - 允许从 fenced code block 中恢复 JSON
  - 允许从包含额外文本的回复里提取首个 JSON object
- 为该行为补了测试，并通过：
  - `tests/test_p4_deepseek_pilot_contracts.py`
  - `tests/test_p5_formal_runner_contracts.py`
- 重新对 `deepseek-reasoner` 执行真实 formal probe：
  - 输出：`artifacts/p5_formal_main_probe_deepseek_reasoner_S067.json`

## 3. 探测结果

### deepseek-chat

- 维持 `PROBE_PASSED`
- 可视作当前已验证的 API-backed formal probe candidate

### deepseek-reasoner

- 结果仍为 `PROBE_FAILED`
- `18/18` 调用已执行，但失败主要集中在：
  - `provider response has no JSON object content`
  - 以及少量 `JSONDecodeError`
- 即使在 adapter 解析加固后，reasoner 仍然没有达到“可放心进入正式付费 full-run”的稳定度

## 4. 当前判断

- 工程上，formal runner 与 probe 护栏已经足够强，能够在真实 paid path 上提前识别模型接口不稳的问题
- `deepseek-chat` 已通过这套护栏
- `deepseek-reasoner` 暂时未通过
- 因此，当前更接近用户目标“补上模型就能安全开跑”，但还差两类事情：
  1. remote push 成功，保证交付闭环
  2. formal preflight 的外部 evidence / approval blockers 被关闭

## 5. 下一步

- 第一优先级：重试 `git push origin main`
- 第二优先级：继续 `P5-MAIN-001`，围绕 formal readiness blocker 清单推进
- 若必须补足第二个正式模型位：
  - 继续加强 `deepseek-reasoner` 的 JSON 稳定性，直到 probe 通过，或
  - 改用另一个能够通过同样 formal probe 的模型替代
