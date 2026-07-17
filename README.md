# FireWorldBench

FireWorldBench 是一个 simulation-grounded 火灾物理世界理解 benchmark，评估多模态基础模型能否从有限观测中依次完成动态感知、当前状态恢复和未来演化推理。

## 当前状态

项目正在按 `FireWorldBenchv2(1).pdf` 重构。该 PDF 是唯一核心设计来源。2026-07-17 之前的 T1/T2/T3 任务、旧 Schema、旧 P0-P7 冻结链、正式/准实验产物和 `src/fireworldbench/` 实现均为 `LEGACY-NONCOMPARABLE`，不能作为当前 benchmark 或论文结果。

当前门禁是架构冻结与 20-event pilot 准备；尚未授权生成 180 个事件、进行正式训练或主实验。

## 固定能力体系

```text
L1 Dynamic Perception
  L1-1 Early Signal Attribution
  L1-2 Next-State Selection
  L1-3 Temporal Coherence Verification
        |
L2 State Recovery
  L2-1 Source and Stage Recovery
  L2-2 Current Risk Region Recovery
  L2-3 Dominant Mechanism Recognition
        |
L3 Evolution Reasoning
  L3-1 Future Trend Prediction
  L3-2 Future Risk Region Prediction
  L3-3 Counterfactual Comparison
```

输入轨道为 `S` Structured、`I` Image、`V` Video。来源先标准化为 Fire Event，再构建任务 QA；不同来源不直接随机混合。

## 文档入口

| 文件 | 用途 |
|---|---|
| `PROJECT_CHARTER.md` | 当前研究边界和成功标准 |
| `ROADMAP.md` | pilot-first 实施门禁 |
| `docs/ARCHITECTURE_FREEZE.md` | 不可变架构、Schema、split、指标和 QC |
| `docs/TASK_PROTOCOL.md` | 九任务逐项协议 |
| `docs/SOURCE_ROLE_MATRIX.md` | 数据源准入与报告角色 |
| `docs/CONFLICT_AUDIT_2026-07-17.md` | 旧项目冲突、保留与迁移清单 |
| `schemas/fire_event.schema.json` | Fire Event 机器契约 |
| `schemas/qa.schema.json` | QA 机器契约 |
| `migration/README_SERVER_MIGRATION.md` | 服务器迁移、传输、重建和验收 |
| `migration/SERVER_HANDOFF_PROMPT.md` | 新服务器接手项目的首轮提示词 |

## 新工程入口

```powershell
python -m fireworld.ingest --help
python -m fireworld.generate_fds --help
python -m fireworld.build_events --help
python -m fireworld.build_tasks --help
python -m fireworld.make_splits --help
python -m fireworld.validate_dataset --help
python -m fireworld.run_model --help
python -m fireworld.score --help
```

新主线代码位于 `src/fireworld/`。旧 `fwb` CLI 保留用于历史产物审计，不代表新架构兼容。

## 数据目录

```text
data/raw/      # 原始来源，只读
data/events/   # 统一 Fire Events
data/qa/       # 九任务 QA
data/splits/   # event_group-first split 清单
```

论文和数据报告必须同时列出独立 Fire Event、QA、各任务、各轨道、各来源和各 split 数量。

迁移服务器时只执行 `git clone` 不够：`data/raw/` 与 `artifacts/` 未被 Git 跟踪，核心 PDF 和参考文献也位于仓库外。应按迁移说明传输包含 `1.参考文献/`、`2.方案研究/`、`3.数据集/` 和 `5.项目实现/` 的整个工作区，并在服务器验证 `migration/transfer_manifest.json`。
