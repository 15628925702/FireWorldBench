---
handoff_id: H-20260714-S011-001
handoff_state: READY
source_session: 2026-07-14_S011_P2-SCHEMA-001样本预测Schema与语义validator.md
current_task: P2-SPLIT-001
---

# 下一任务增量

- 任务 ID：`P2-SPLIT-001`
- 目标：先按 case/family/sequence/重复组划分，再切窗/派生；构造 ID、火源/通风/HRR/布局 OOD 和 external partitions。
- 第一动作：创建本轮 `IN_PROGRESS` 草稿，复用 ontology、v2 Schema/validator 和 P1 freeze manifest。
- 输入：`configs/data_sources.toml`、`项目治理/数据资产登记.md`、仓库外 `../../3.数据集`、各来源官方许可证据。
- 交付：split 配置、group 清单、分层统计、混杂报告、稳定 seed/hash。
- 门禁：group 交集为零；OOD 轴可解释且样本量足够；测试标签隔离；下一任务只能是 `P2-LEAK-001`。
- 当前限制：空 Conda 环境；不得安装/下载；不得修改仓库外 `../../3.数据集` 原始文件；不得读取仓库外 `../../4.升级拓展`；任务验收通过后必须执行任务级 `commit + push origin main`。
