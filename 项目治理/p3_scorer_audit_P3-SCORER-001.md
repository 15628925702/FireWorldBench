# P3-SCORER-001 参考评分器审计

日期：2026-07-14  
任务状态：DONE_WITH_BLOCKED_EXTERNAL_DATA

## 实现内容

- `src/fireworldbench/scorer.py` 对 T1-A/B/C、T2-A/B/C、T3-A/B/C 提供统一样本评分入口。
- 保留 sample-level 原始分数、case 聚合和 validated pair 聚合；窗口不作为独立统计单位。
- 失败记录不删除：missing prediction、invalid prediction、unknown evidence 均有明确状态；unknown evidence 计 `V_EVIDENCE` 且 evidence score 为 0。
- T3-C 使用 trace 组件评分，T3-B 使用 pair ranking，T1-C 保留 query cost 的预算效用扣减；所有任务分别报告指标，composite score 禁用。
- CLI 新增 `fwb score --samples ... --predictions ... --output ...`。

## 边界与验证

本轮只评分显式传入的样本和预测 fixture，没有读取 test gold/private mapping，没有生成模型预测或正式测试结果。9 个任务覆盖、case/pair 聚合、失败计分和 golden tests 通过。

下一任务：`P3-EXPERT-001`。
