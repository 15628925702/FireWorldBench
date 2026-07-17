# FireWorldBench v2 Conflict Audit

审计日期：`2026-07-17`
核心依据：`FireWorldBenchv2(1).pdf` 18 页，已完成文本提取及关键页视觉核验。

## 1. 总结

现有项目是围绕旧 T1/T2/T3 ontology、旧 sample/physical-trace 协议、Immersed 主数据和 tool-use/agent 实验链实现的。它与新 PDF 在研究任务、输入轨道、来源角色、主指标、排行榜和方法边界上存在结构性冲突，不能通过名称映射视为兼容。

## 2. 冲突清单

| 现有内容 | 冲突 | 处置 |
|---|---|---|
| `AGENTS.md` 指向旧 PDF | 错误事实源 | 已替换为核心 PDF 唯一权威 |
| `PROJECT_CHARTER.md` T1/T2/T3 | 任务语义与九任务不一致 | 已替换 |
| `README.md/ROADMAP.md` 旧 P0-P7 | 把旧冻结和主实验当作当前状态 | 已替换；旧记录历史化 |
| `详细设计规划/02` | T1-A 判别、T1-B 归因、T1-C 信息选择等与 L1-1/2/3 不同 | 旧文档标记废弃，新协议独立建立 |
| `schemas/benchmark_sample*` | 强制 `physical_trace`，没有 Fire Event、S/I/V 单轨契约 | 只保留 legacy；新增 Event/QA Schema |
| `configs/evaluation.toml` | AUPRC、trace score、tool tracks 为主，拒绝单一总分 | 只保留 legacy；新增 v2 task/leaderboard 配置 |
| `configs/data_sources.toml` | Immersed 为 T1/T2 主体，包含 FDS-exp/FIgLib 等非核心来源 | 新矩阵改为 FDS 主榜；未指定来源不进入 v2 |
| `src/fireworldbench/t1_builder.py` 等 | 构建旧 T1/T2/T3 | 不迁移到 v2 主入口；仅历史审计 |
| `src/fireworldbench/tool_tracks.py` | 工具/Agent 是主要比较轨道 | 与 S/I/V 输入轨道混淆；退出主设计 |
| P4-P7 baseline/formal/quasi/paper artifacts | 使用旧任务和样本空间 | 标记 `LEGACY-NONCOMPARABLE`，不得引用为 v2 结果 |
| v3/融合/DPO/额外 FSR 文档 | 改变或扩张核心 PDF | 保留为历史资料，不纳入实现 |

## 3. 可直接保留的原则

- 原始数据只读、内容哈希、许可与 provenance 登记。
- group-first split、公开/私有隔离、测试标签 embargo、防泄漏扫描。
- JSON Schema、Python 3.11、pytest、ruff、mypy 技术栈。
- 不可覆盖 run、失败留痕、配置快照、逐样本可重算评分。
- 外部数据缺失字段显式为空，不猜测单位或标签。

这些原则保留不等于旧实现自动合格；必须由新契约测试验证。

## 4. 修改与新增

- 修改最高层事实源、章程、路线图、开发约束、决策和状态入口。
- 新增 Fire Event/QA Schema、S/I/V 协议、九任务协议、来源矩阵、split、metrics、QC 和 pilot 配置。
- 新增 `src/fireworld/` 的八个 `python -m` 接口。
- 新增新 Schema fixture、语义校验、split 泄漏和评分聚合测试。

## 5. 删除或归档策略

本轮不破坏用户原始资料，不批量删除旧代码、历史文档、原始数据或产物。旧入口统一加废弃声明并从新 README/CLI 隔离。完成新 pilot 且迁移审计通过后，再决定将旧实现移动到 `legacy/`；移动前必须保留 Git 历史和 manifest 引用。

## 6. 缺失与阻塞

- FDS/Smokeview 可执行版本、单机 CPU/内存/存储实测尚未完成。
- 四种 pilot 几何中的具体参数、网格收敛与边界条件待 pilot 冻结。
- stage、risk、dead-band、tie tolerance、机制判定规则需领域复核。
- Fire360、DetectiumFire 的实际可访问内容、版本、许可和再发布范围未确认。
- PolyUFire 只允许基于确实存在字段构建任务；字段字典仍需核验。
- 两名非作者标注者和领域审核者尚未落实。

## 7. 重构风险

1. 旧实验结果被误认为 v2 结果：通过包名、配置版本、README 和报告状态隔离。
2. 旧 builder 被“字段改名”复用：新测试必须断言固定答案空间和任务语义。
3. 时间切片夸大规模：同时报告独立 event 与 QA 数，且 event ID 生成在切片前。
4. 外部来源标签越权：Schema 的 ground truth 要求逐字段 origin；来源矩阵限制任务。
5. FDS 成本过高或标签不稳定：20-event pilot 是 180-event 扩展的硬门禁。
6. 新旧测试同时存在造成失败噪声：新测试以 `test_v2_*` 标识；旧失败不通过篡改期望来掩盖。

## 8. 核心 PDF 内部细节的优先级处理

核心 PDF 第 5 页和用户固定定义规定 I 为单图或 2-4 张关键帧，但第 8 页 L1-3 细则写 4-6 张。按用户最新明确的固定轨道定义，v2 Schema 和任务协议采用最多 4 张；不得为 L1-3 放宽到 6 张。
