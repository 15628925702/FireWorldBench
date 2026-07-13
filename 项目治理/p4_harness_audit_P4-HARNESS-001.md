# P4-HARNESS-001 统一运行器审计

日期：2026-07-14  
任务状态：DONE_WITH_BLOCKED_EXTERNAL_DATA

## 实现内容

- `src/fireworldbench/harness.py` 提供 train/dev-only adapter runner、prompt/config SHA-256、run ID、超时、重试、invalid JSON/tool error/refusal 状态、延迟和 raw response。
- public run manifest 只保留可审计元数据；raw response 写入 private 目录并通过引用关联，普通流程拒绝挂载 `FIREWORLDBENCH_PRIVATE_ROOT`。
- 已有 run 输出目录拒绝覆盖，失败样本和失败 raw response 均保留。
- CLI 新增 `fwb harness-run --samples ... --output ...`。

## 边界与验证

本轮仅使用仓库 fixture，没有读取 test input/gold/private mapping，没有修改 `../../3.数据集`，没有调用真实模型或生成正式测试结果。成功、重试、raw 隔离、test split 拒绝和覆盖保护测试通过。

下一任务：`P4-BASELINE-NUM`。
