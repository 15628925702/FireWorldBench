---
handoff_id: H-20260714-S007-001
handoff_state: READY
source_session: 2026-07-14_S007_P1-DATA-003数据质量case泄漏审计.md
current_task: P1-RESEARCH-001
---

# 下一任务增量

- 任务 ID：`P1-RESEARCH-001`
- 目标：基于用户/导师给定目标会议或最多两个候选会议，核验最新官方投稿/双盲/数据/artifact 政策，系统检索相关 benchmark/论文，形成贡献差异矩阵并评估污染风险。
- 第一动作：创建本轮 `IN_PROGRESS` 草稿，复用 P1-DATA-001 manifest、P1-DATA-002 字段契约和 P1-DATA-003 质量报告。
- 输入：`configs/data_sources.toml`、`项目治理/数据资产登记.md`、仓库外 `../../3.数据集`、各来源官方许可证据。
- 交付：venue policy 表、deadline/页数/匿名约束、相关工作矩阵、可证实贡献、污染探针与缓解、论文证据矩阵。
- 门禁：主贡献没有明显重复；会议约束不会推翻数据/发布设计；未证实的“首个”等措辞禁止；下一任务只能是 `P1-FREEZE-001`。
- 当前限制：空 Conda 环境；不得安装/下载；不得修改仓库外 `../../3.数据集` 原始文件；不得读取仓库外 `../../4.升级拓展`；任务验收通过后必须执行任务级 `commit + push origin main`。
