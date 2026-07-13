---
handoff_id: H-20260714-S010-001
handoff_state: READY
source_session: 2026-07-14_S010_P2-ONTOLOGY-001任务与物理机制ontology.md
current_task: P2-SCHEMA-001
---

# 下一任务增量

- 任务 ID：`P2-SCHEMA-001`
- 目标：把 ontology 落到版本化 sample/prediction Schema，覆盖 T1/T2/T3 条件字段、ID、provenance、trace、评分私有字段；实现正向/负向/边界测试和跨字段语义校验。
- 第一动作：创建本轮 `IN_PROGRESS` 草稿，读取 `ontology_P2-ONTOLOGY-001.json/.md` 和 P1 freeze manifest。
- 输入：`configs/data_sources.toml`、`项目治理/数据资产登记.md`、仓库外 `../../3.数据集`、各来源官方许可证据。
- 交付：sample/prediction Schema、validator、正负边界 fixtures、迁移/版本规则和测试。
- 门禁：9 个子任务可机检；私有 gold 不进入公开 prediction；非法单位/ID/证据引用被拒；下一任务只能是 `P2-SPLIT-001`。
- 当前限制：空 Conda 环境；不得安装/下载；不得修改仓库外 `../../3.数据集` 原始文件；不得读取仓库外 `../../4.升级拓展`；任务验收通过后必须执行任务级 `commit + push origin main`。
