# P3-MVP-RC1-001 可重建 MVP 审计

日期：2026-07-14  
任务状态：DONE_WITH_BLOCKED_EXTERNAL_DATA

## 实现内容

- `src/fireworldbench/release.py` 从显式冻结 sample 输入生成 `public/` 和 `private/` 两个包。
- public 包移除 `scoring_metadata`，并明确排除 test gold、private ID mapping 和 model rankings。
- private 包只保留输入中显式存在的 scoring metadata；本轮不包含 test gold 或 private mapping。
- 两个包都有 benchmark card、manifest 和 checksums；manifest 不自哈希，checksums 覆盖 manifest。
- 相同输入连续构建两次，逐文件内容和 checksum 必须一致；只做 benchmark smoke，不做模型排名。

## 边界与验证

本轮没有读取 test input/gold/private mapping，没有修改 `../../3.数据集`，没有生成模型结果。双构建一致性、公开包私有字段排除、错误输入拒绝和全量检查通过。

下一任务：`P4-HARNESS-001`。
