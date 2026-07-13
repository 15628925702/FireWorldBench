---
handoff_id: H-20260714-S026-001
handoff_state: READY
task_status: READY
source_session: 2026-07-14_S026_P4-BASELINE-LLM模型与提示冻结.md
current_task: P4-TOOL-001
---

# 下一任务增量

## P4-BASELINE-VISION completed

Visual baseline is formally `N/A` because approved visual assets, region annotations, interference protocol, and a reproducible runtime are unavailable. Detection and physical-reasoning metrics remain separate and unset; only train/dev is accepted, and no dataset or test/private asset was read.

## Next window: one task only

`P4-BASELINE-LLM`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, freeze model ID, prompt, few-shot, sampling, retries, parser, budget, and runtime boundaries. Without an approved model or API, record `BLOCKED` and do not fabricate results. Run checks, commit, and try `push origin main`.

## P4-BASELINE-LLM completed

LLM baseline contracts are frozen for separate text/table and multimodal tracks. The current pilot is formally `BLOCKED` because model approval, API budget, and runtime are unavailable; configuration and reporting exist without fabricated results. Only train/dev is accepted.

## Next window: one task only

`P4-TOOL-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, then implement separate retrieval/plot/formula-FDS-proxy/tool-use tracks with frozen whitelist, call limits, replayable traces, dev ablations, cost, and failure reports. Do not mix information budgets or read test/private assets. Run checks, commit, and try `push origin main`.

- 任务 ID：`P2-FREEZE-001`
- 目标：逐条审计 P2 出口，冻结 Schema、ontology、split、leak 规则、公开/私有边界和评测协议；封存测试资产与 FD-Gen generation plan。
- 第一动作：创建本轮 `IN_PROGRESS` 草稿，复用 P2 ontology、Schema、split、leak policy、evaluation spec 和 P1 freeze manifest。
- 输入：`configs/data_sources.toml`、`项目治理/数据资产登记.md`、仓库外 `../../3.数据集`、各来源官方许可证据。
- 交付：P2 freeze manifest、test embargo/private manifest、无访问确认、FD-Gen generation plan/hash、批准决策、迁移规则和 P3 输入清单。
- 门禁：全部机器测试通过；D-005/D-007 等决策获批或明确阻塞；测试资产不可达；下一任务只能是 `P3-PIPELINE-001`。
- 当前限制：空 Conda 环境；不得安装/下载；不得修改仓库外 `../../3.数据集` 原始文件；不得读取仓库外 `../../4.升级拓展`；任务验收通过后必须执行任务级 `commit + push origin main`。
## P2-FREEZE-001 已完成

P2 出口、ACTIVE test embargo、无访问确认、FD-Gen 冻结计划、P2 manifest 和迁移规则已在 commit `2ecc3f8` 推送。D-005/D-007 与数据许可、感知近重复、FDS/FD-Gen 环境仍需审批或外部证据，不能生成正式测试结果。

## 下一窗口唯一任务

任务 ID：`P3-PIPELINE-001`

先按 AGENTS.md、CURRENT_STATUS.md、source_session、NEXT_SESSION_PROMPT.md 和任务包顺序读取；创建新的 IN_PROGRESS 会话草稿；仅使用已批准且可访问的仓库内契约与 fixture 开展 pipeline 骨架工作；不得读取隐藏测试资产、不得修改 `../../3.数据集`、不得安装或下载包；完成后必须运行现有检查、commit 并 push `origin/main`。
## P3-PIPELINE-001 已完成

已完成只读 inventory、CSV/JSON/JSONL adapter、L0 保留、时间单位转换、case graph、canonical manifest 和结构化 failure report。未知单位不猜测，坏行不静默丢弃，受保护测试路径直接拒绝访问。

## 下一窗口唯一任务

任务 ID：`P3-BUILD-T1`

先按 AGENTS.md、CURRENT_STATUS.md、source_session、NEXT_SESSION_PROMPT.md 和任务包顺序读取；创建新的 IN_PROGRESS 会话草稿；只使用 pipeline 产出的 train/dev 或仓库 fixture，禁止读取 test input/gold/private mapping，禁止修改 `../../3.数据集`，禁止安装/下载包；完成后运行检查、commit 并 push `origin/main`。
## 当前阻塞

P3-PIPELINE-001 本地 commit `4801792` 已完成，三次 `git push origin main` 均因无法连接 `github.com:443` 失败。下一窗口只先重试推送并核验远端 SHA；推送成功前不要标记 DONE，不要进入 `P3-BUILD-T1`。
## P3-BUILD-T1 已完成

已实现 T1-A/B/C 火灾预警样本 builder，限定 train/dev，拒绝 test/OOD 和未批准阈值；Schema、正常/边界/拒绝路径验证通过。下一唯一任务：`P3-BUILD-T2`。
## P3-BUILD-T2 已完成

已实现 T2-A/B/C builder，保留 mechanism family、evidence observation ID 和 unknown/underdetermined 边界。下一唯一任务：`P3-BUILD-T3`。
## 当前阻塞

P3-BUILD-T2 本地 commit `48683d3` 已完成，GitHub 推送连续三次失败。下一窗口第一动作是重试 `git push origin main` 并核验远端 SHA；成功前保持 `BLOCKED_PUSH`，不要进入 `P3-BUILD-T3`。
## 当前阻塞

P3-BUILD-T2 实现提交 `48683d3` 及阻塞记录 `264aff5` 尚未推送，GitHub 443 连续不可达。下一窗口先重试 `git push origin main` 并核验远端 SHA；成功前保持 `BLOCKED_PUSH`，不要进入 `P3-BUILD-T3`。
## P3-BUILD-T3 已完成

已实现趋势、有效单变量 pair 和状态转移 trace builder，缺少必要证据时明确拒绝或输出 unknown。下一唯一任务：`P3-SCORER-001`。
## P3-SCORER-001 已完成

已完成 9 个任务的参考评分闭环，保留 sample/case/pair 原始分数和失败记录。下一唯一任务：`P3-EXPERT-001`。
## P3-EXPERT-001 已完成

已完成 rubric、校准模板、双人标注一致性计算和分歧裁决流程；实际标注仍为 0，专家门明确阻塞。下一唯一任务：`P3-MVP-RC1-001`。
## P3-MVP-RC1-001 已完成

已完成可重建 MVP RC1 双包，公开包排除私有评分字段和测试 gold，双构建逐文件一致。下一唯一任务：`P4-HARNESS-001`。
## P4-HARNESS-001 已完成

已完成统一运行器和 public/private run 隔离，失败样本保留且禁止覆盖已有 run。下一唯一任务：`P4-BASELINE-NUM`。
## P4-BASELINE-NUM 已完成

已完成数值/时间序列 baseline，并固定 seed、train-only majority、threshold 来源和 test 禁止调参规则。下一唯一任务：`P4-BASELINE-VISION`。
