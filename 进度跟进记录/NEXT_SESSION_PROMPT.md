---
handoff_id: H-20260714-S013-001
handoff_state: READY
source_session: 2026-07-14_S013_P2-LEAK-001匿名ID与泄漏审计.md
current_task: P2-EVAL-001
---

# 下一任务增量

- 任务 ID：`P2-EVAL-001`
- 目标：冻结各子任务主/次指标、case/pair 分析单位、失败计分、校准、bootstrap CI、人工评测 rubric 和综合分限制。
- 第一动作：创建本轮 `IN_PROGRESS` 草稿，复用 ontology、v2 Schema/validator、split、leak policy 和 P1 freeze manifest。
- 输入：`configs/data_sources.toml`、`项目治理/数据资产登记.md`、仓库外 `../../3.数据集`、各来源官方许可证据。
- 交付：evaluation 配置、指标规范、评分器原型、统计预案、人工 rubric 草案。
- 门禁：不得以窗口为独立统计单位；无效输出/超时/拒答规则明确；下一任务只能是 `P2-FREEZE-001`。
- 当前限制：空 Conda 环境；不得安装/下载；不得修改仓库外 `../../3.数据集` 原始文件；不得读取仓库外 `../../4.升级拓展`；任务验收通过后必须执行任务级 `commit + push origin main`。
