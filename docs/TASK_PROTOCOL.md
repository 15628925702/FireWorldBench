# FireWorldBench Fine-Grained Nine-Task Protocol

状态：`USER-DIRECTED-REDESIGN-DRAFT`
版本：`FWB-FINEGRAIN-v1`
日期：`2026-07-21`

本文件取代旧九任务的现行实验资格。旧协议仅用于解释不可变 FDS Core v3.3.1 和历史结果，
不得继续生成新的模型排名。详细设计、答案空间、指标和难度门禁见
`docs/FINE_GRAINED_TASK_METRIC_REDESIGN.md`。

## Active tasks

| ID | Task | Required output | Primary metric |
|---|---|---|---|
| L1-1 | Multi-signal Early Event Attribution | event_class | Macro-F1 |
| L1-2 | Causal Next-State Discrimination | choice | horizon-macro Accuracy |
| L1-3 | Temporal Violation Localization and Typing | consistency, first_violation_bin, violation_type | Hierarchical Joint Exact Match |
| L2-1 | Joint Source-Stage Recovery | source_region, stage | Joint Exact Match |
| L2-2 | Hazard Region-Severity-Driver Recovery | risk_region, risk_level, risk_driver | Joint Exact Match |
| L2-3 | Mechanism-Flow-Regime Diagnosis | mechanism, flow_direction, control_regime | Joint Exact Match |
| L3-1 | Multi-Horizon Multivariable Forecasting | 3 horizons × 3 trends | macro of horizon-level Strict Triple Exact Match |
| L3-2 | First Hazard-Crossing Forecast | region, time_bin, trigger_variable | Joint Exact Match |
| L3-3 | Counterfactual Effect Decomposition | direction, magnitude_bin, earliest_affected_target | Joint Exact Match |

## Track ceiling

- S/I/V 是三个独立评测套件，可以分别选择文本、图像/VL 和 direct-video 模型。同一模型不必
  支持三轨；未参评轨道不计 missing，也不影响其已参加轨道的排名。
- 不同轨道使用不同模型时，每轨分别冻结并记录 exact model ID、catalog metadata 和请求参数。
- 模型只在同一轨道、同一任务矩阵、同一 subset 和同一协议版本内比较；禁止跨轨直接排名。
- S：九任务可在 metadata、support 和可回答性门禁通过后发布。
- I/V：L1-2、L1-3 可发布；L2-1、L2-3、L3-3 仅在视觉证据充分时 conditional。
- L1-1、L2-2、L3-1、L3-2 的完整新答案空间包含普通 RGB 不可可靠观测的信息，I/V 为 unsupported。
- 视觉专用简化任务必须使用新 subtrack/task ID，不得把温度、CO 或传感器状态从 RGB 补造。
- V 必须是 direct-video input；帧转文字、抽帧描述或 I 轨代理均不构成 V 结果。
- S 可在九任务通过门禁后报告 S Overall；I/V 只报告各自冻结任务集合的 suite macro，不生成
  跨 S/I/V Overall。

## Publication gates

- 新 prediction contract/schema 必须版本化；现有 v2 contract 不足以承载新增字段。
- 新 metadata 必须机器可读且冻结，不得从问题文本临时正则推断。
- 每任务推荐至少 100 个计分 QA；每个分类至少 20 条并跨至少 3 个 event_group。
- 不满足 support 的任务只报告诊断，状态为 `not_ranked_insufficient_support`。
- missing/malformed/schema-invalid 在完整分母中计 0；不以 valid-only 分数作为排行榜分数。
- S/I/V 必须真实使用对应输入适配器；V 不允许文本或抽帧代理冒充。
- 外部来源独立报告，不进入 FDS Overall；禁止 LLM judge。
- 正式模型实验保持暂停，直至 schema、validators、scorer、challenge subset 和基线验收完成。

## Difficulty calibration

30--50 是冻结开发挑战集上代表模型群体的目标中位区间，不是人为缩放目标。若多个不同模型
家族在某任务均超过 65，审计候选过易、泄漏和 shortcut；若专家低于 70，审计可回答性和
标签质量。任何正式测试结果不得用于反向调题。
