# P3-BUILD-T2 状态与机制样本审计

日期：2026-07-14  
任务状态：DONE_WITH_BLOCKED_EXTERNAL_DATA

## 实现内容

- `src/fireworldbench/t2_builder.py` 生成 T2-A 火灾状态、T2-B 主导机制和 T2-C 物理一致性样本。
- 所有正向状态、机制和一致性判断都链接 observation ID；没有有效证据时使用 ontology 的 unknown/underdetermined 标签。
- T2-B 保留 mechanism family 标签，不把任务实现成通用 detection；T2-C 的 `inconsistent` 必须有合法 violation code，否则降级为 `underdetermined`。
- builder 只接受 `train_id` 或 `dev_id`，禁止构造 test/OOD 样本。

## 边界与验证

本轮未读取 test input/gold/private mapping，未修改 `../../3.数据集`，未生成模型结果。正常、未知状态/机制、无 violation 的一致性边界、test split 拒绝和 Schema 校验均通过。

下一任务：`P3-BUILD-T3`。
