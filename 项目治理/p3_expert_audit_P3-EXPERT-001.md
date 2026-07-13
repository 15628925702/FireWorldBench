# P3-EXPERT-001 专家校准与双人标注审计

日期：2026-07-14  
任务状态：DONE_WITH_EXPERT_GATE_BLOCKED

## 实现内容

- `expert_rubric_P3-EXPERT-001.json` 固定 T1/T2/T3 九个任务的判定标准、拒答边界、证据要求和物理约束检查项。
- `expert_calibration_set_P3-EXPERT-001.json` 提供脱敏合成校准模板，不包含 test gold 或真实专家结论。
- `src/fireworldbench/expert.py` 校验标注记录、计算 label Cohen kappa、evidence Jaccard、列出分歧并生成 adjudication queue。
- 专家不足时不伪造标签；按任务收缩或删除不可靠 gold，专家门保持 `BLOCKED_UNTIL_TWO_DOMAIN_RATERS`。

## 验收边界

本轮未读取 test input/gold/private mapping，未修改 `../../3.数据集`，未生成真实专家标签。双人分歧、非法 annotator、非法 label 和一致性报告测试通过。

下一任务：`P3-MVP-RC1-001`。
