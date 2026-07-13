---
handoff_id: H-20260714-S008-001
handoff_state: READY
source_session: 2026-07-14_S008_P1-RESEARCH-001会议相关工作污染审计.md
current_task: P1-FREEZE-001
---

# 下一任务增量

- 任务 ID：`P1-FREEZE-001`
- 目标：不新增数据研究，逐条审计 P1 数据许可、字段、质量、case 语义、ICLR 2027 venue 状态和污染出口，生成 P1 freeze manifest。
- 第一动作：创建本轮 `IN_PROGRESS` 草稿，复用三轮数据证据和本轮 ICLR 2027 研究报告。
- 输入：`configs/data_sources.toml`、`项目治理/数据资产登记.md`、仓库外 `../../3.数据集`、各来源官方许可证据。
- 交付：P1 审计报告、批准/拒绝/修改决策、冻结 manifest/hash、遗留风险与 P2 输入清单。
- 门禁：许可、字段、质量、case 语义和论文可行性均达标或明确收缩范围；下一任务只能是 `P2-ONTOLOGY-001`。
- 当前限制：空 Conda 环境；不得安装/下载；不得修改仓库外 `../../3.数据集` 原始文件；不得读取仓库外 `../../4.升级拓展`；任务验收通过后必须执行任务级 `commit + push origin main`。
