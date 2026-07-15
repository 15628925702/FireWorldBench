---
handoff_id: H-20260716-S067-001
handoff_state: READY
session_id: 2026-07-16_S067
task_id: P5-MAIN-001
next_task: P5-MAIN-001
---

# 2026-07-16_S067_P5-MAIN-001 reasoner输出预算与probe门禁

## 1. 本轮目标

继续把 DeepSeek API 链路推进到更接近准实验级别，重点判断：

- `deepseek-reasoner` 是否只是 parser 问题
- 还是即使加预算也仍然不够稳定，因而不应该进入正式第二模型槽

## 2. 本轮完成

- 从真实 provider 返回中定位到关键失败机制：
  - 大量 `deepseek-reasoner` 失败不是普通标签错误
  - 而是 `finish_reason=length` 导致 content JSON 被截断
- 对 adapter 做了两类加固：
  - 从 fenced code / 杂质文本中恢复 JSON object
  - 当 provider `finish_reason != stop` 时显式报错，而不是留下模糊 JSON decode failure
- 在 formal readiness 里新增门禁：
  - 对 `openai_compatible_json` 且 `approval_status=APPROVED` 的模型，必须有 `PROBE_PASSED` 和 `probe_artifact`

## 3. reasoner 的实测结论

### 抽样单条验证

- 在更高输出预算下，某些失败样本可以从 `length` 转为 `stop`
- 说明它不是完全不可用，而是强依赖更大的输出预算

### 全 18 条 guarded probe

- 即便把 `deepseek-reasoner` 的 `max_tokens` 提高到 `1024`
- 全量 18 条 guarded formal probe 仍然失败
- 最新失败主要仍然是：
  - `provider finish_reason is not safe for formal execution: length`

所以当前更准确的结论是：

- `deepseek-reasoner` 不是完全坏掉
- 但它在当前 prompt / task / budget 约束下，仍然不够稳定，不适合作为“现在就能放心花钱”的正式第二槽

## 4. 当前建议

- 保留 `deepseek-chat` 作为已验证 API 模型位
- 暂时不要把 `deepseek-reasoner` 升级为 approved formal slot
- 第二模型位后续应优先：
  - 换一个更稳的模型并重复同样 probe，或
  - 在明确可接受的更高输出预算下继续单独攻 `deepseek-reasoner`

## 5. 关键文件

- `artifacts/p5_formal_main_probe_deepseek_S066.json`
- `artifacts/p5_formal_main_probe_deepseek_reasoner_S069.json`
- `configs/model_matrix_P5-MAIN-001.json`
- `项目治理/p5_formal_readiness_P5-MAIN-001.json`

