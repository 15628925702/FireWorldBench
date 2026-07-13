---
handoff_id: H-20260714-S024-001
handoff_state: READY
task_status: READY
session_id: 2026-07-14_S024
task_id: P4-BASELINE-NUM
next_task: P4-BASELINE-VISION
started_at: 2026-07-14 Asia/Shanghai
---

# P4-BASELINE-NUM 会话记录

## Git 基线

- branch: `main`
- HEAD: `3fe652c878a2664c0903eeecd26a6cfd1d02f56f`
- remote: `origin https://github.com/15628925702/FireWorldBench.git`
- staged: none
- unstaged: none
- untracked: none

## 本轮目标

实现 chance、majority、domain threshold、传统 ML baseline 接口和预注册 temporal baseline；统一输入、seed、预算、case split、失败报告，只使用 train/dev。

## 执行边界

- 不看 test 调参，不读取 test input/gold/private mapping。
- 不修改 `../../3.数据集`，不安装或下载包。

## 完成结果

- chance、majority、domain threshold、traditional ML 接口和 temporal persistence baseline 已实现。
- test split 和 test tuning 被拒绝；seed、train-only majority、threshold 来源和失败记录已固定。
- 验证：pytest 49 passed；project check passed；mypy 修正后通过；CLI smoke 通过。
- commit：`d9b3de0`；下一任务：`P4-BASELINE-VISION`。
