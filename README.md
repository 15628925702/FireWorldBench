# FireWorldBench v1

FireWorldBench 是面向 LLM / multimodal agent 的火灾物理世界理解 benchmark。它不把问题简化为“图中是否有火”或“传感器是否越阈值”，而是评估模型能否依据多模态证据恢复受火灾动力学约束的状态、机制、因果链和干预后果。

v1 以 T1 预警、T2 状态/机制、T3 演化/反事实作为统一能力轴，把仿真、受控实验、传感器时序和视觉数据作为不同证据来源映射到同一协议。它不是“一数据集一个小问答任务”的集合，也不在 v1 扩展到火灾以外的物理领域。

## 当前状态

- 阶段：P0 文档/治理初始化完成，等待建立首个本地源码 commit 基线；尚未进入 P1。
- 当前可执行任务：见 `进度跟进记录/CURRENT_STATUS.md`。
- 当前不做：`4.升级拓展` 中的进阶方向、完整模型训练、论文结果宣称。
- 研究概念基线：`开发要求约束/FireWorldBench_Benchmark_Design_v2.pdf`。

## 文档地图

| 入口 | 职责 |
|---|---|
| `AGENTS.md` | 新对话/新开发者的强制入口 |
| `PROJECT_CHARTER.md` | 目标、非目标、成功标准与责任边界 |
| `ROADMAP.md` | 阶段、依赖与出口门禁 |
| `详细设计规划/` | 数据、任务、系统、实验和论文的可执行设计 |
| `开发要求约束/` | MUST/SHOULD 规则、完成定义与变更控制 |
| `进度跟进记录/` | 当前状态、会话证据、交接模板和下一轮提示词 |
| `项目治理/` | 决策、风险、开放问题、数据资产和论文证据台账 |
| `configs/` | 可版本化的项目、数据、划分和评测配置 |
| `schemas/` | benchmark 样本和预测的机器可检验契约 |
| `src/`、`tests/`、`scripts/` | 最小实现骨架、测试和项目检查工具 |

长期多窗口推进从 `进度跟进记录/多窗口开发执行手册.md` 开始；全部 43 个剩余任务在 `进度跟进记录/任务指令库_从P0到论文数据导出.md`。

## 数据边界

- 原始/抽样数据：仓库外只读目录 `../../3.数据集`。
- 仓库内 `data/`：只保存说明、清单、哈希和可再生成的小型派生物，不保存受限原始数据。
- 运行产物：`artifacts/`，默认不进 Git；需要发布的冻结结果以清单和哈希登记。
- 当前资产能否进入实验，以 `项目治理/数据资产登记.md` 的 `eligible` 状态为准。

## 最小开发流程

```text
需求/假设 -> 数据许可与完整性门禁 -> 样本契约 -> group split
         -> benchmark 构建与校验 -> baseline -> 冻结评测
         -> 统计分析/误差分析 -> 论文证据矩阵 -> 发布审计
```

首次创建项目环境：

```powershell
conda create -n fireworldbench-v1 --offline --no-default-packages -y
```

当前按项目初始化要求只创建空 Conda 环境，不安装任何包。`environment.yml` 记录空环境名称；待进入实现阶段后，再依据 `pyproject.toml` 经明确确认安装 Python 和开发依赖。

本地检查统一在该环境中执行：

```powershell
conda run -n fireworldbench-v1 python scripts/check_project.py
conda run -n fireworldbench-v1 python -m pytest
conda run -n fireworldbench-v1 python -m ruff check .
conda run -n fireworldbench-v1 python -m mypy src
```

## 事实源优先级

用户最新明确指令 > 已批准的决策记录 > 开发约束 > 详细设计 > 核心 PDF > 会话记录。发现冲突不得自行折中，必须登记并请求决策。
