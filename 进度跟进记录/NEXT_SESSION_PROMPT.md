---
handoff_id: H-20260714-S015-001
handoff_state: READY
source_session: 2026-07-14_S015_P2-FREEZE-001契约测试封存.md
current_task: P3-PIPELINE-001
---

# 下一任务增量

- 任务 ID：`P2-FREEZE-001`
- 目标：逐条审计 P2 出口，冻结 Schema、ontology、split、leak 规则、公开/私有边界和评测协议；封存测试资产与 FD-Gen generation plan。
- 第一动作：创建本轮 `IN_PROGRESS` 草稿，复用 P2 ontology、Schema、split、leak policy、evaluation spec 和 P1 freeze manifest。
- 输入：`configs/data_sources.toml`、`项目治理/数据资产登记.md`、仓库外 `../../3.数据集`、各来源官方许可证据。
- 交付：P2 freeze manifest、test embargo/private manifest、无访问确认、FD-Gen generation plan/hash、批准决策、迁移规则和 P3 输入清单。
- 门禁：全部机器测试通过；D-005/D-007 等决策获批或明确阻塞；测试资产不可达；下一任务只能是 `P3-PIPELINE-001`。
- 当前限制：空 Conda 环境；不得安装/下载；不得修改仓库外 `../../3.数据集` 原始文件；不得读取仓库外 `../../4.升级拓展`；任务验收通过后必须执行任务级 `commit + push origin main`。
