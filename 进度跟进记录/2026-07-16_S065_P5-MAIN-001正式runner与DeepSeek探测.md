---
handoff_id: H-20260716-S065-001
handoff_state: READY
session_id: 2026-07-16_S065
task_id: P5-MAIN-001
next_task: P5-MAIN-001
---

# 2026-07-16_S065_P5-MAIN-001 正式runner与DeepSeek探测

## 1. 会话元数据

- 任务 ID：`P5-MAIN-001`
- 状态：`BLOCKED`
- 时间：`2026-07-16 Asia/Shanghai`
- Git branch：`main`
- 开始 HEAD：`10f2d7f793c1cc418b320fd664d83d9ff2c13e3c`
- 本轮目标：把 formal main 从“只会报 blocker”推进到“有真实执行入口，并先用 DeepSeek 走通真实 probe 链路”

## 2. 本轮完成

- 新增 `src/fireworldbench/formal_runner.py`
  - 支持 `formal-main-probe`
  - 支持 `formal-main-run`
  - 内置预算上限预阻断、重复输出拒绝、schema 校验、raw response 哈希、失败保留、clean git 要求
- 扩展 `src/fireworldbench/deepseek.py`
  - 抽出通用 OpenAI-compatible JSON adapter
  - DeepSeek 改为复用该通用适配层
- 扩展 `src/fireworldbench/formal_readiness.py`
  - formal model matrix 的必需执行字段更严格，避免“配置概念上存在但 runner 无法消费”
- 扩展 `src/fireworldbench/cli.py`
  - 新增 `formal-main-probe`
  - 新增 `formal-main-run`
- 更新 `configs/model_matrix_P5-MAIN-001.json`
  - 为模型项补充可执行字段：`adapter_kind`、`credential_env`、`prompt_id`、`max_input_tokens`、`top_p`、token pricing fields
  - 为 `deepseek-chat` / `deepseek-reasoner` 补充可探测级别的 endpoint / budget / prompt hash

## 3. DeepSeek 正式链路 probe 结果

- 命令已实际执行：
  - `python -m fireworldbench.cli formal-main-probe --samples artifacts/p5_research_deepseek_18_S063.json --model-matrix configs/model_matrix_P5-MAIN-001.json --model-id deepseek-chat --output artifacts/p5_formal_main_probe_deepseek_S066.json --max-samples 18 --allow-unapproved`
- 状态：`PROBE_PASSED`
- 样本数 / 执行数：`18 / 18`
- 失败：`0`
- schema error：`0`
- scorer failure_counts：`{}`
- token：input `12539` / output `4320`
- 关键 task metrics：
  - T1-A `1.0`
  - T1-B `1.0`
  - T1-C `0.99`
  - T2-A `1.0`
  - T2-B `1.0`
  - T2-C `1.0`
  - T3-A `0.5`
  - T3-B `1.0`
  - T3-C `1.0`

这意味着 DeepSeek 已经通过“真实 formal adapter/probe 链路”，不只是研究脚本或早期 pilot 脚本。

## 4. formal preflight 现状

- 已重新执行 `formal-preflight`
- 最新结果仍为：`BLOCKED_FORMAL_PREFLIGHT`
- 最新 readiness hash：`ed6182883a34b150d2e43145cf3946f9e531a43566fedb9cd7e6eded818098d3`

当前主要 blockers：

- `data:*`：formal input files / split audit / leak audit / uniqueness audit 仍未闭环
- `models:*`：批准状态、完整任务覆盖、若干本地模型的 prompt hash / required values 仍未补齐
- `models:matrix_not_approved_frozen`
- `calibration:*`：结果未完成
- `preregistration:cost_ceiling_not_approved`
- `runtime:*`：批准 runtime 未闭环

## 5. 对“避免浪费钱”的实际意义

本轮已经把最容易浪费钱的工程性风险往前拦了一步：

- 没有 readiness 就不能正式 full-run
- output root 已存在时拒绝重复跑
- 预算上限可在样本级调用前阻断
- prompt/adapter/schema 现在能先用 probe 走真实链路测试
- raw response 与失败记录能保留，避免“花了钱但不知道哪一步坏了”

## 6. 仍未完成的外部阻塞

本轮不能单方面完成的部分仍然存在：

- formal 数据资格 / 许可 / paper-ready case manifest
- approved multi-model matrix 的最终审批
- calibration complete 结果
- formal runtime / budget ceiling 审批

因此，当前状态已经接近“补齐审批与模型信息后可以安全开跑”，但还不是“现在立刻允许 full-run”。

## 7. 下一步交接

- 唯一下一任务：`P5-MAIN-001`
- 第一动作：继续围绕 `项目治理/p5_formal_readiness_P5-MAIN-001.json` 的 blocker 清单逐项关闭或确认
- 已有真实 formal run 命令模板：
  - `python -m fireworldbench.cli formal-main-run --root <repo_root> --samples <paper_ready_inputs.json> --model-matrix configs/model_matrix_P5-MAIN-001.json --readiness 项目治理/p5_formal_readiness_P5-MAIN-001.json --model-id <approved_model_id> --output-root artifacts/formal_runs/<run_id>`
- 禁止：
  - readiness blocked 时直接执行 `formal-main-run`
  - 重跑旧 research DeepSeek 脚本
  - 访问 hidden test/private
  - 未授权下载或安装
