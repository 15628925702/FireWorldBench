# P3-BUILD-T1 火灾预警样本审计

日期：2026-07-14  
任务状态：DONE_WITH_BLOCKED_EXTERNAL_DATA

## 实现内容

- `src/fireworldbench/t1_builder.py` 生成 T1-A early-fire discrimination、T1-B anomaly attribution、T1-C information-need selection。
- builder 只接受 `train_id` 或 `dev_id`；任何 test/OOD split 直接拒绝。
- T1-A/B 只有在 canonical record 中出现明确、唯一的显式标签时才生成正向 gold，否则生成 ontology 规定的 `insufficient_information`。
- T1-C 只从冻结的 observation 集合中按确定性顺序选择 query；不从文件名或 query 名称泄漏答案。
- threshold 参数只能声明来自 `train` 或 `calibration`；禁止 test 阈值调参。
- 每个样本包含 observation IDs、time range、evidence、gold origin、private scoring metadata 和完整 provenance。

## 边界与验证

本轮未读取 test input/gold/private mapping，未修改 `../../3.数据集`，未生成正式 test 样本或模型结果。正常、未知信号、拒绝 test split、拒绝未批准 threshold 和 Schema 校验均通过。

下一任务：`P3-BUILD-T2`。
