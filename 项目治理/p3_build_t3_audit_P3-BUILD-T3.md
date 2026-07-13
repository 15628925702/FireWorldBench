# P3-BUILD-T3 趋势与反事实样本审计

日期：2026-07-14  
任务状态：DONE_WITH_BLOCKED_EXTERNAL_DATA

## 实现内容

- `src/fireworldbench/t3_builder.py` 生成 T3-A 趋势、T3-B 单变量反事实和 T3-C 状态转移 trace 样本。
- T3-A 只有同时存在 target variable、正 horizon 和明确趋势标签时才生成正向 gold；不使用未来观测偷看当前输入。
- T3-B 只有 `pair_valid=true` 且 `single_variable=true` 才允许因果标签；其他 pair 输出 `pair_invalid` 或 `underdetermined`。
- T3-C 要求 initial state、mechanism chain、transitions 和 outcome 完整；证据不足输出 `trace_unknown`。
- builder 只接受 `train_id` 或 `dev_id`，禁止构造 test/OOD 样本。

## 边界与验证

本轮未读取 test input/gold/private mapping，未修改 `../../3.数据集`，未生成模型结果。正常趋势、有效 pair、完整 trace、缺 horizon、无效 pair、缺失 trace、test split 拒绝和 Schema 校验均通过。

下一任务：`P3-SCORER-001`。
