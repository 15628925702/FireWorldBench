# FireWorldBench v2 协作入口

本文件适用于本仓库及全部子目录。

## 1. 唯一设计依据

工作区根目录下 `2.方案研究/FireWorldBenchv2(1).pdf` 是唯一核心设计来源。原 Windows 路径为 `G:/0-newResearch/2/2.方案研究/FireWorldBenchv2(1).pdf`，仅作 provenance。用户最新明确指令优先于该 PDF；除这两者外，任何旧章程、详细设计、冻结记录、Schema、配置、代码或实验产物都不能改变核心方案。

旧 `FireWorldBench_Benchmark_Design_v2.pdf`、T1/T2/T3 方案、v3/融合方案、部分可观测状态诊断收缩方案、DPO、额外 Fire State Representation、tool-use/Agent 主线及旧 P0-P7 冻结链均为历史材料。只有经新协议逐项验证后才能复用实现；“已经实现”不是保留理由。

## 2. 不可变研究定义

- 定位：评估多模态基础模型能否从部分、有限且不同形式的火灾观测中，依次完成动态感知、当前状态恢复与未来演化推理。
- 能力：L1 Dynamic Perception、L2 State Recovery、L3 Evolution Reasoning。
- 任务：固定为 `L1-1` 至 `L3-3` 九个任务，不增加、删除或合并。
- 输入轨道：`S` Structured、`I` Image、`V` Video。轨道是否发布由信息充分性和标签可靠性决定。
- 中间层：所有来源先转换为 Fire Event，再按 `source_domain` 构建 QA 和报告。
- 主数据：FDS / Smokeview / FD-Gen。Immersed Tunnel、PolyUFire、D-Fire、Fire360 和可选 DetectiumFire 按核心 PDF 的外部角色使用。
- 规模：先做 20 个独立 Fire Events pilot，再决定是否扩展到约 180 events 和 4,000-6,000 QA。
- 评分：固定标签/有限候选优先；Accuracy 系主指标；开放解释和 LLM Judge 不进入主排行榜。
- 方法：FireState Card 仅为确定性脚本生成的轻量 proof-of-concept，不扩展为复杂模型或 Agent。

## 3. 当前工作边界

在架构、Schema、九任务协议和 20-event pilot 设计通过前：

- 不批量生成 180 个 FDS 事件，不做大规模下载，不训练正式模型，不运行主实验。
- 不构建多轮 Agent、复杂新模型或九任务之外的新任务。
- 可以审计和修改文档、Schema、配置、测试与最小 fixture；可以准备 pilot。
- `data/raw/` 中已有原始资产保持只读。不得因迁移而移动、重命名、覆盖或删除。
- 旧代码位于 `src/fireworldbench/`，状态为 `LEGACY-NONCOMPARABLE`；新主线位于 `src/fireworld/`。
- 旧结果、旧冻结集和准实验不得作为 v2 结果；必须用新 Fire Event/QA Schema 重建后才有资格。

## 4. 强制工程规则

- split 必须在切片、增强和 QA 派生前按 `event_group` 完成；跨 split 重叠必须为 0。
- 公开 ID、文件名、路径、EXIF 和元数据不得包含火源、HRR、通风、答案或 split 线索。
- 缺失模态显式为 `null`；来源不存在的标签不得人工补造。
- 每个 FDS event 记录 FDS/Smokeview/FD-Gen 版本、网格、边界、配置哈希、随机种子、输入、日志和失败状态。
- 所有样本通过 JSON Schema；候选位置均衡；时间位置、选项长度和视觉外观执行 shortcut audit。
- 许可、引用、获取版本和再发布范围逐来源记录；未确认资产不得进入正式计分或发布。
- 原始模型输出、解析失败、评分配置和逐样本分数必须可重算。

## 5. 新窗口读取顺序

1. 本文件。
2. `PROJECT_CHARTER.md`、`ROADMAP.md`。
3. `docs/ARCHITECTURE_FREEZE.md` 与 `docs/CONFLICT_AUDIT_2026-07-17.md`。
4. `进度跟进记录/CURRENT_STATUS.md`。
5. 当前任务直接涉及的任务协议、Schema、配置和测试。

若旧 handoff、旧冻结或旧配置与以上内容冲突，按历史证据保留，但不得继续执行其指令。
