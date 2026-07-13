# P2-EVAL-001 指标与统计规范

## 1. 统计单位

- 普通任务的最小统计单位是 `case`，不是 observation window、视频帧或派生问题。
- T3-B 的最小统计单位是经过 validator 确认的 `pair`；A/B 不能拆成两个独立样本。
- 同一 case 的多个窗口先在 case 内聚合，再进入宏平均或 bootstrap。
- train/calibration 可以估计阈值；dev 只用于选择；test/OOD/external 只在主运行中评测。

## 2. 主指标

| 任务 | 主指标 | 解释 |
|---|---|---|
| T1-A | case-level AUPRC | 早期火灾判别，类别不平衡时优先 precision-recall |
| T1-B | case-level macro-F1 | 火灾、非火、通风扰动、传感器故障和拒答类别平衡 |
| T1-C | budgeted decision utility | 预算内选择观测或停止的效用 |
| T2-A | case-level macro-F1 | 阶段/状态识别 |
| T2-B | mechanism macro-F1 | 多标签机制识别 |
| T2-C | balanced accuracy | 物理一致/不一致/不确定三类 |
| T3-A | trend-direction macro accuracy | 未来趋势方向优先于不必要的精确数值 |
| T3-B | validated-pair ranking accuracy | 合法 A/B pair 的风险方向判断 |
| T3-C | state trace score | 初始状态、机制、转移、结果四部分的结构化得分 |

## 3. 次指标与物理约束

统一报告 `evidence_f1`、uncertainty calibration 和 `physical_violation_rate`。T1 额外报告 miss/false alarm/lead-time/Brier/ECE；T2 额外报告状态、区域、机制层级一致性；T3 额外报告 event-time、区间覆盖、MAE/RMSE、response-order 和 causal-edge F1。

物理违规独立报告，不能被答案准确率抵消。`V_EVIDENCE`、`V_UNIT`、`V_OBSERVABILITY`、`V_PAIR_INVALID` 等结构违规保留原始记录。

## 4. 失败、拒答和超时

- 无效 JSON：保留原文，结构字段按缺失计，不人工修复。
- 超时/API/tool error：达到预注册最大重试后计失败，保留错误类型和成本。
- `insufficient_information`、`underdetermined`、`*_unknown`：当 gold 允许时是合法答案，否则按任务定义计错；不能统一当作负类。
- evidence ID 不存在：evidence 得分为 0，并记 `V_EVIDENCE`。
- 非法单位、ID 或 pair：结构失败；pair 不进入因果方向主指标。

## 5. Bootstrap 与比较

- 对 case 或 validated pair 的逐单位分数做 percentile bootstrap，seed=`20260714`、resamples=`2000`、95% CI。
- 报告差值、95% CI 和实际效应，不以窗口数替代样本量。
- 多模型/多任务比较按预注册 family，必要时报告多重比较控制；不得看过 test 后改指标或筛样本。

## 6. 人工 rubric

人工评测只覆盖自动规则难以处理的开放解释、trace 合理性和证据充分性。校准集不进入 test 主统计；至少两名独立标注者，涉及物理主张时至少一名火灾工程/动力学背景复核者；报告原始一致率和适用的一致性统计。

每项 0-2 分：

1. **事实/方向正确性**：0 错误，1 部分正确，2 正确且无矛盾。
2. **机制链完整性**：0 无链或错误，1 主要节点对但缺边，2 节点/边/顺序完整。
3. **证据可追溯性**：0 无效/不存在，1 部分支持，2 每个关键主张均指向 observation ID。
4. **不确定性与拒答**：0 过度确定或漏报缺失，1 部分说明，2 在证据不足处正确拒答并说明缺口。
5. **物理约束**：0 触发严重 violation，1 有可解释边界问题，2 无已知 violation。

总分不替代任务主指标，也不生成单一排行榜总分。
