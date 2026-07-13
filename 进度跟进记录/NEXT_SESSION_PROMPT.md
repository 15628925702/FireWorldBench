---
handoff_id: H-20260714-S006-001
handoff_state: READY
source_session: 2026-07-14_S006_P1-DATA-002字段单位标准化契约.md
current_task: P1-DATA-003
---

# 下一任务增量

- 任务 ID：`P1-DATA-002`
- 目标：统计缺失、异常、零字节、重复、标签问题和采样特征，确认 case/family/sequence/near-duplicate/template 泄漏键，并验证 Immersed 配置 pair 语义。
- 第一动作：创建本轮 `IN_PROGRESS` 草稿，复用 P1-DATA-001 manifest、P1-DATA-002 字段契约和只读探查脚本。
- 输入：`configs/data_sources.toml`、`项目治理/数据资产登记.md`、仓库外 `../../3.数据集`、各来源官方许可证据。
- 交付：质量报告、case/family 注册表、潜在泄漏键、pair 参数 diff、修复/排除策略。
- 门禁：质量问题均有 disposition，split group 可执行；视觉空标签语义明确或阻塞；下一任务只能是 `P1-RESEARCH-001`。
- 当前限制：空 Conda 环境；不得安装/下载；不得修改仓库外 `../../3.数据集` 原始文件；不得读取仓库外 `../../4.升级拓展`；任务验收通过后必须执行任务级 `commit + push origin main`。
