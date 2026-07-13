---
handoff_id: H-20260714-S009-001
handoff_state: READY
source_session: 2026-07-14_S009_P1-FREEZE-001阶段冻结审计.md
current_task: P2-ONTOLOGY-001
---

# 下一任务增量

- 任务 ID：`P2-ONTOLOGY-001`
- 目标：冻结 9 个子任务的标签空间、机制层级、风险状态、缺失/拒答、证据和 physical violation taxonomy；标明可观测性与 gold origin。
- 第一动作：创建本轮 `IN_PROGRESS` 草稿，读取 P1 freeze manifest、P1 审计报告和核心任务定义证据。
- 输入：`configs/data_sources.toml`、`项目治理/数据资产登记.md`、仓库外 `../../3.数据集`、各来源官方许可证据。
- 交付：ontology 文件、标签定义/例子/反例、任务输入输出矩阵、专家待确认项。
- 门禁：同名标签无歧义；不从视觉数据推断不可观测 CFD 真值；下一任务只能是 `P2-SCHEMA-001`。
- 当前限制：空 Conda 环境；不得安装/下载；不得修改仓库外 `../../3.数据集` 原始文件；不得读取仓库外 `../../4.升级拓展`；任务验收通过后必须执行任务级 `commit + push origin main`。
