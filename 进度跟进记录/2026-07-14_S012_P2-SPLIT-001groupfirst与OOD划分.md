---
handoff_id: H-20260714-S012-001
handoff_state: READY
session_id: 2026-07-14_S012
task_id: P2-SPLIT-001
next_task: P2-LEAK-001
---

# 2026-07-14_S012_P2-SPLIT-001groupfirst与OOD划分

## 1. 会话元数据

- 任务 ID：`P2-SPLIT-001`
- 状态：`IN_PROGRESS`
- 开始/结束：`2026-07-14T00:00:00+08:00 / 2026-07-14T00:00:00+08:00`
- 执行者：`Codex GPT-5`
- Git branch：`main`
- Git HEAD：`6757950`
- Git remote：`origin fetch/push=https://github.com/15628925702/FireWorldBench.git`
- 基线 staged/unstaged/untracked：`0 / 0 / 0`
- 工作区既有改动：`无`
- 任务交付提交：`96d1a77，已 push origin main`

## 2. 目标与验收

- 本轮目标：`先按 case/family/sequence/重复组定义 split，再定义 ID/OOD/external 分区，不把窗口当独立样本。`
- 明确不做：`不修改 ../../3.数据集；不读取 ../../4.升级拓展；不安装/下载；不把 BLOCKED 数据标为正式可用。`
- 验收标准：
  - [PASS] `group 交集为零，split 配置和 group 清单可机检。`：7 groups/13 case keys，validator 通过。
  - [PASS_WITH_SCOPE] `OOD 轴可解释；样本不足或许可阻塞的分区明确 BLOCKED。`：位置 OOD 为 provisional，其余不足轴明确 BLOCKED。

## 3. 实际完成

- `configs/split_P2-SPLIT-001.json`：group-first、split、OOD 轴、seed 和门禁配置。
- `项目治理/split_groups_P2-SPLIT-001.json`：7 个 group、13 个 case key、分配和排除清单。
- `项目治理/split_report_P2-SPLIT-001.md`：分层统计、混杂风险和正式启用条件。
- `scripts/validate_split_p2_split_001.py` 与 `tests/test_p2_split_contracts.py`：校验 group 不重叠、覆盖完整和 OOD gate。

## 4. 未完成与偏差

- 正式 benchmark split 仍未启用：P1 许可阻塞、D01 位置与 lane/config 混杂、感知重复审计待 P2-LEAK-001。
- ventilation/HRR/geometry OOD 均保持 `BLOCKED`，不伪造样本量或物理解释。

## 5. 验证证据

| 状态 | 检查 | 结果 |
|---|---|---|
| `PASS` | `python scripts/validate_split_p2_split_001.py` | 7 groups，13 case keys，split 无交集 |
| `PASS` | `python -m pytest` | 19 passed |
| `PASS` | `python scripts/check_project.py` | 核心项目检查通过 |
| `PASS` | `python -m mypy src scripts` | no issues found in 9 source files |

## 6. 下一轮交接

- 唯一下一任务：`P2-LEAK-001 - 匿名 ID 与泄漏审计`
- 第一条命令/动作：`创建 IN_PROGRESS 草稿，复用 split group 清单和 v2 Schema/validator。`
- 必须复用：`configs/split_P2-SPLIT-001.json`、`项目治理/split_groups_P2-SPLIT-001.json`、`schemas/*.v2.schema.json`。
- 禁止重复/禁止做：`不得把窗口当独立 case；不得绕过 P1 license gate；不得把 provisional OOD 写成正式结果；不得读取 ../../4.升级拓展。`
- 完成标准：`已知精确/感知/邻帧/family/template/metadata 泄漏有报告和处置；下一任务 P2-EVAL-001。`
