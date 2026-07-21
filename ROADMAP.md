# FireWorldBench v2 Redesign Roadmap

状态：`EXPERIMENTS_PAUSED`
日期：`2026-07-21`

FDS Core v3.3.1 继续保持不可变：180/180 strict Events、4,039 QA。外部 formal Events/QA
仍为零，candidate/substitute/quarantine/gap 状态不变且不进入 FDS Overall。

| 阶段 | 目标 | 输出 | 出口门禁 |
|---|---|---|---|
| R0 证据审计 | 解释旧结果为何难度不均 | support、基线、过易/过难/小样本清单 | 不把单个高分误判为整体过易 |
| R1 任务指标重设计 | 冻结细粒度九任务与主/诊断指标 | 设计稿、任务协议、评估卡 | 用户确认研究目标和答案空间 |
| R2 契约版本化 | 新增联合输出和机器可读 metadata | QA/prediction schema vNext、validators | 旧 release/schema 不被覆盖 |
| R3 Challenge candidate | 从现有 FDS 证据派生独立挑战候选 | subset manifest、support、可回答性报告 | 无新增数据集；event_group 泄漏为 0 |
| R4 Scorer/baseline | 实现完整分母计分和诊断指标 | deterministic scorer、baselines、tests | 两次重算完全一致；missing/malformed 计 0 |
| R5 难度校准 | 仅在冻结 dev challenge 上做代表模型 smoke | 模型群体中位数、专家上限、成本报告 | 目标中位 30--50；专家建议 ≥80 |
| R6 多模型 pilot | 小规模协议验证 | 固定 model IDs、S/I/V 结果、失败率 | schema/模态/预算/support 全部通过 |
| R7 发布决策 | 决定是否形成新版本 benchmark | acceptance、迁移说明、限制 | 不回写 FDS Core v3.3.1 |

当前执行 R1；R2 及以后尚未授权开始。不得调用模型、下载或处理新数据。
