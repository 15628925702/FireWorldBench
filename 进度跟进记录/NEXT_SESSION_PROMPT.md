---
handoff_id: H-20260714-S012-001
handoff_state: READY
source_session: 2026-07-14_S012_P2-SPLIT-001groupfirst与OOD划分.md
current_task: P2-LEAK-001
---

# 下一任务增量

- 任务 ID：`P2-LEAK-001`
- 目标：实现公开 opaque ID/私有映射，扫描精确/感知重复、视频邻帧、family、模板、文件名、路径和元数据答案线索。
- 第一动作：创建本轮 `IN_PROGRESS` 草稿，复用 split group 清单、v2 Schema/validator、ontology 和 P1 freeze manifest。
- 输入：`configs/data_sources.toml`、`项目治理/数据资产登记.md`、仓库外 `../../3.数据集`、各来源官方许可证据。
- 交付：匿名化工具、私有映射策略、泄漏报告、失败 fixtures 和 release 扫描规则。
- 门禁：已知泄漏为零；公开输入不能从名称直接推答案；下一任务只能是 `P2-EVAL-001`。
- 当前限制：空 Conda 环境；不得安装/下载；不得修改仓库外 `../../3.数据集` 原始文件；不得读取仓库外 `../../4.升级拓展`；任务验收通过后必须执行任务级 `commit + push origin main`。
