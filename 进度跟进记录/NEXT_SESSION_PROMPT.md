---
handoff_id: H-20260716-S063-001
handoff_state: READY
task_status: BLOCKED
source_session: 2026-07-16_S063_P5-RESEARCH-RUN-001个人研究结果.md
current_task: P5-RESEARCH-DEEPSEEK-001
---

## Authoritative next window: P5-RESEARCH-DEEPSEEK-001

个人研究全量链已经可用：D01 192/192，train/dev/visible-holdout 为 3,300/750/750，零成本 baseline 和导师简报已完成。下一窗口不要重建数据，不要回到 formal 多模型/专家/隐藏 test 流程。

唯一任务是运行 18 条 DeepSeek 平衡代表集。先在用户本地 PowerShell 将可用 key 设置为当前进程的 `DEEPSEEK_API_KEY`，然后执行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_research_deepseek.ps1`。脚本会拒绝重复输出，成功后自动评分。只跑 18 条，不扩大到 750 条；完成后更新 `项目治理/p5_preliminary_research_results_S063.json` 和中文简报、测试、commit、push。

本节为当前权威交接；下方均为历史记录。

## Authoritative next window: P5-MAIN-001

当前工程 preflight 已完备，但正式主跑状态是 `BLOCKED_FORMAL_PREFLIGHT`。先读取 source session、`项目治理/p5_formal_input_audit_P5-MAIN-001.json`、`项目治理/p5_formal_readiness_P5-MAIN-001.json` 及六类 `configs/*P5-MAIN-001.json`。

唯一目标是取得并验证当前缺失的外部证据：formal data eligibility/paper-ready case manifest、至少两个 exact approved model/runtime、pricing/cost ceiling、环境锁和 train/dev calibration results。未经明确批准，不下载 D01/模型、不安装包、不调用正式 API、不访问 test/private。证据到位后依次重跑 `formal-input-audit` 与 `formal-preflight`；只有输出 `READY_FOR_FORMAL_MULTI_MODEL_FULL_RUN` 才可给出并执行正式 full-run 命令。

本节为当前权威交接；下方内容是历史累计记录，不得覆盖本节状态。

## Next window: P5-MAIN-001

本轮已修复 `.xls` 适配器的整表内存问题，并成功生成 `artifacts/p5_main_staging_assessment_S061.json`；正式主实验仍因 preregistration、approved model matrix、calibration、approved runtime 四项门禁保持 `BLOCKED`。下一窗口先读取本会话和该 assessment，继续处理真实 train/dev 输入与主实验准备；不要调用 DeepSeek 全量、不要读取 test/private、不要修改 `../../3.数据集` 原始文件、不要安装或下载包。

## Next window: P5-MAIN-001

本轮已把 planning-only 主跑前置链实际跑通：D01/D02-readable-XLSX/D03 canonical、51 dev/48 train 九任务样本、domain-threshold/majority baseline 和正式 gate 审计均有产物。下一窗口继续处理 P5-MAIN-001 的未完成项：优先解决 D01 剩余 184 个 CSV 的完整下载或校验可用本地副本，再处理 D02 legacy XLS；不得调用 DeepSeek 全量，不得把 planning 结果称为正式 benchmark。复用 `configs/main_run_P5-PLANNING-001.json` 和现有 artifacts，先检查 Git 状态与数据文件完整性。

本轮已完成 D01/D02-readable-XLSX/D03 的规划链适配、模型矩阵登记、自动 Gold 规则登记和 DeepSeek 低分单独分析。D01 官方完整源已核验为 192 个 CSV，但当前本地仍只有 8 个；GitHub 大文件下载在当前网络下约 15 KB/s，未完整下载的文件不得纳入 staging。D02 的 8 个 XLSX 已可读，80 个 legacy XLS 仍为 BLOCKED。

下一窗口先复用 `项目治理/dataset_chain_expansion_P5-PLANNING.json`、`configs/model_matrix_P5-PLANNING.json`、`configs/gold_status_P5-PLANNING.json` 和 `项目治理/P5-deepseek-smoke-error-analysis.md`，确认这些阻塞项后再决定是否用当前可用规划样本做受控主跑。不得把当前结果称为全量 benchmark 或论文结果，不得消耗 DeepSeek 预算做重复验证。

上一任务已完成全九任务 remediation pilot。下一窗口只做 planning-scale main-run readiness decision：允许规划 D01 扩展，但必须保留 D01-only/自动标签限制、失败恢复 ledger 和所有任务分数；不得读 test/private，不得把 planning 结果称为正式 benchmark 或论文结论。

交付提示：全任务演练本地提交为 `ab4b7eb`，GitHub 连接重置导致 push 失败。先重试 `git push origin main`；失败则保留 `BLOCKED_PUSH` 并继续本地修复。

交付提示：本地统计提交为 `98f985c`，GitHub 443 当前不可达。先重试 `git push origin main`；失败则保留 `BLOCKED_PUSH` 并继续本地任务。

交付提示：P5-MAIN-RUN 本地提交为 `db5480f`，GitHub push 因 443 连接失败，先重试 `git push origin main`；失败则继续本地推进并保留 `BLOCKED_PUSH`。

交付提示：P4-PILOT-RUN 本地提交为 `102ca3d`，首次 push 因 GitHub HTTPS 连接重置失败，重试 `git push origin main`；失败则继续记录 `BLOCKED_PUSH` 并保留本地提交。

交付提示：planning-mode 本地提交为 `83a8218`，GitHub push 因 443 不可达失败；先重试推送，失败则继续本地执行 `P4-PILOT-RUN`。

先读取 `AGENTS.md`、`CURRENT_STATUS.md`、本文件、source session 和可用任务包；创建新的 IN_PROGRESS 会话草稿。完成后运行测试、mypy，提交并尝试 push；push 失败则记录 `BLOCKED_PUSH` 并保留本地提交继续推进。

## Next window: P3-PIPELINE-STAGING-INTEGRATION

第一动作：检查本轮本地 commit/push 状态，然后读取 `项目治理/download_staging_registry_P1-PLANNING.json` 和 6 个 `download_manifest_<DATASET_ID>_planning.json`。

先读 `AGENTS.md`、`CURRENT_STATUS.md`、本文件、source session、`configs/data_sources.toml`、`项目治理/download_staging_audit_P1-PLANNING.md`。

只执行 staging 到 pipeline 的受限预研接入：允许读取 `data/raw/D01_Immersed-Tunnel-CFD`、`data/raw/D02_PolyUFire`、`data/raw/D03_FDS-exp`、`data/raw/D04_FD-Gen`、`data/raw/D05_D-Fire`、`data/raw/D10_FIgLib-SmokeyNet` 和本轮 planning manifests；输出必须显式保留 `formal_benchmark_eligible=false`、`license_status=UNKNOWN/BLOCKED`、`redistribution_status=UNKNOWN/BLOCKED`。

禁止把 staged 数据标记为正式 train/dev/test/redistribution；禁止提交 `data/raw/**`；禁止读取 test gold/private mapping；禁止读取或使用 `../../4.升级拓展`；禁止下载 D06/D07/D08/D09/D11，除非用户另行批准 D06 的存储和许可证预案。

完成标准：pipeline 预研入口可读取 staging manifest 并生成只读 inventory/probe 结果；不产生模型实验结果；运行现有检查、commit，并尝试 `git push origin main`。若 push 失败，记录 `BLOCKED_PUSH` 并保留本地 commit。

## P7-RELEASE-001 completed

最终阶段门禁审计已完成，生成了本地 manifest、changelog、artifact checklist 和发布指令。正式状态为 `BLOCKED_CRITICAL_RISKS`：无冻结结果、论文导出包、匿名包和 clean-room 输入，Git 历史未同步，且没有明确外部发布批准；未创建 tag、GitHub Release 或外部发布包。

## Next window: explicit approval required

当前没有可安全自动执行的下一任务。若要进行外部发布，必须先明确批准 tag/GitHub Release/外部包发布范围；批准前只保持本地审计记录，不执行外部发布。

## P7-REPRO-001 completed

clean-room reproduction 门禁已建立：需要合法 release README、独立环境锁、合法输入、benchmark/代表 baseline/paper registry 三类重建日志、hash 和 deviations。当前没有 release root/README，正式状态为 `BLOCKED_NO_RELEASE_INPUT`，没有创建环境、下载内容或虚构重建结果。

## Next window: one task only

`P7-RELEASE-001`: 按顺序读取 handoff 文件和任务包，审计所有阶段门禁、版本、checksum、论文数据、匿名/复现文档；只生成本地最终冻结审计，不执行 tag/push/release 或其他外部发布，除非用户明确授权。完成检查、commit，并按约束尝试 push `origin/main`。

## P7-ANON-001 completed

匿名/双盲清理契约已冻结：显式导出根会扫描身份、用户名、绝对路径、私有 URL、secret、Git 元数据、test gold/private mapping 和受限第三方数据；许可与 source-version 声明未解决前资产不得进入 public。当前没有导出根，正式状态为 `BLOCKED_NO_EXPORT`，没有生成匿名包。

## Next window: one task only

`P7-REPRO-001`: 按顺序读取 handoff 文件和任务包，在独立全新环境按 release README 评估 benchmark、代表 baseline 和论文数字 registry 的重建；当前没有合法论文包或冻结结果时记录正式 blocked/no-input 决策，不声称复现成功。完成检查、commit，并尝试 push `origin/main`。

## P6-EXPORT-001 completed

论文导出契约已冻结：public/private 是两个独立根，各自拥有 manifest/checksum；manifest 不自哈希但 checksums 覆盖 manifest 和其他文件；public 严禁 private、test gold、身份映射、restricted ref、secret 和绝对路径。当前无冻结结果和完整 provenance，正式状态为 `BLOCKED_NO_FROZEN_RESULTS`，没有生成空包或伪造论文包。

## Next window: one task only

`P7-ANON-001`: 按顺序读取 handoff 文件和任务包，扫描作者名、用户名、绝对路径、私有 URL、密钥、Git 元数据、测试 gold 和不允许再分发的第三方数据；当前没有论文导出包时记录正式 no-input/block 决策，不生成匿名包。完成检查、commit，并尝试 push `origin/main`。

## P6-AUDIT-001 completed

已建立论文数字独立追踪审计：对 claims、table、figure、text 做全量扫描和固定随机抽查，要求数字映射冻结 run，并检查统计、单位、取整、样本数、引用、许可、双盲和 claims matrix。当前无冻结论文导出物，正式状态为 `BLOCKED_NO_FROZEN_EXPORTS`；未解释数字差异为空但没有生成任何结果数字，修复不得覆盖旧导出。

## Next window: one task only

`P6-EXPORT-001`: 按顺序读取 handoff 文件和任务包，创建新的 `IN_PROGRESS` 会话草稿，按论文数据导出规范评估 public/private 两个独立根、manifest/checksum、泄漏扫描和本地重建。当前没有冻结结果时记录正式 blocked/no-input 决策，不生成伪造论文包。完成检查、commit，并尝试 push `origin/main`。

## P6-PAPER-TEXT-001 completed

正文数字 registry 已冻结门禁：仅允许来自冻结统计结果的数字进入正文，字段包含 run ID、metric、取整、单位和 provenance；显式论文源扫描到的数字默认是 `UNMAPPED`，非结果数字必须进入有 provenance 的 allowlist。当前无冻结统计结果，因此正式状态为 `BLOCKED_NO_FROZEN_RESULTS`，没有生成 `text_number_map.csv` 或任何论文结果数字。

## Next window: one task only

`P6-AUDIT-001`: 按顺序读取 handoff 文件和任务包，创建新的 `IN_PROGRESS` 会话草稿，审计 claims、tables、figures、text 中所有数字是否映射到冻结 run；当前没有冻结导出物时记录正式 no-input/block decision，不生成差异或论文数字。完成检查、commit，并尝试 push `origin/main`。

# 下一任务增量

## P6-PAPER-FIGURES-001 completed

Figure export is formally `BLOCKED_NO_FIGURE_SOURCE`. No figure data, plot spec, script, PDF, PNG, or caption fact was generated; future figures must use the same frozen result source as tables and retain provenance.

## Next window: one task only

`P6-PAPER-TEXT-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and build the manuscript number registry only from frozen statistics. With no frozen results, record a no-input decision and do not add paper-result numbers. Run checks, commit, and push.

## P6-PAPER-TABLES-001 completed

Paper-table export is formally `BLOCKED_NO_FROZEN_RESULTS`. No CSV, JSON, or LaTeX metrics were generated; future table cells must be traced to immutable sample scores/raw runs and source hashes.

## Next window: one task only

`P6-PAPER-FIGURES-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and freeze source data, plot specs, scripts, styles, rendering, and caption facts. With no frozen result data, record a no-input figure decision and do not fabricate PDF/PNG figures. Run checks, commit, and push.

## P5-CLAIMS-FREEZE-001 completed

The claims-evidence matrix is frozen with six explicitly supported, conditional, blocked, N/A, or removed claims. The result freeze manifest contains no run IDs or result hashes, so no unsupported performance or table claim remains.

## Next window: one task only

`P6-PAPER-TABLES-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and generate tables only from frozen result files. With no frozen results, record a formal no-input export decision and do not fabricate CSV/LaTeX values. Run checks, commit, and push.

## P5-ERROR-001 completed

Blind error analysis is formally `BLOCKED_NO_RAW_OUTPUT`. The nine-class taxonomy, hidden model identity, pre-registered sampling, two-rater adjudication, and negative-result retention rules are frozen; no error label or representative case was selected.

## Next window: one task only

`P5-CLAIMS-FREEZE-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and build the claims-evidence matrix. Downgrade or remove claims without code/config/data evidence; do not invent numerical or model-performance claims. Run checks, commit, and push.

## P5-STATS-001 completed

Statistics are formally `BLOCKED_NO_RAW_OUTPUT`. The frozen contract requires all sample/case/pair metrics, confidence intervals, effect sizes, multiple-comparison, cost, and failure fields to be recomputed from immutable raw predictions; no manual metrics were created.

## Next window: one task only

`P5-ERROR-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and freeze blind error-analysis taxonomy, sampling, adjudication, and representative-case index. Without raw predictions, record a formal no-input decision and do not inspect test/private assets. Run checks, commit, and push.

## Push block carried forward

P5-STATS-001 is locally complete at `988ea2d19530ca306d9ff3df0af3a2afdbde29ed`, but GitHub push and remote SHA verification failed. Keep `BLOCKED_PUSH`, retry during the next delivery, and continue P5-ERROR-001 locally.

## P5-ROBUST-001 completed

The six robustness transformations are frozen with label-invariance requirements: sensor noise, missing observation, sensor fault, visual degradation, wording variation, and tool failure. No main run exists, so the status is `BLOCKED_NO_MAIN_RUN` and all performance/failure/cost slices remain empty.

## Next window: one task only

`P5-STATS-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and audit raw prediction availability for case/pair statistics, 95% CI, effect sizes, multiple comparisons, cost, and failures. Without raw outputs, record a formal no-input decision and never hand-edit metrics. Run checks, commit, and push.

## P5-ABLATION-001 completed

The preregistered ablation factors are frozen one at a time: information budget, evidence visibility, and uncertainty reporting. Main execution has no run index, so the formal status is `BLOCKED_NO_MAIN_RUN`; ablation runs, parameter diffs, and paired results remain empty. Extra findings are exploratory only.

## Next window: one task only

`P5-ROBUST-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and audit preregistered noise, missingness, sensor-fault, visual-degradation, wording, and tool-failure transformations. Without main outputs, record a formal no-run decision and do not fabricate robustness metrics. Run checks, commit, and retry pending pushes.

## P5-MAIN-001 completed

The preregistered main matrix is formally `BLOCKED`: preregistration, approved model matrix, calibration, paper-ready inputs, and runtime gates are not closed. No harness run or model output exists; run index, raw responses, failures, and costs remain empty, and the runner does not read gold.

## Next window: one task only

`P5-ABLATION-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and audit the preregistered one-factor-at-a-time ablation plan. Without an executable main run, record a formal no-input/no-run decision and do not invent paired results. Run checks, commit, and retry pending pushes.

## Push block carried forward

P5-MAIN-001 is locally complete at `de0b449eae9c414df360e6f802b639624205cbda`; push reported success but remote SHA verification failed. Keep `BLOCKED_PUSH`, retry during the next delivery, and continue P5-ABLATION-001 locally.

## P5-PREREG-001 completed

The preregistration contract freezes hypotheses, all nine primary metrics, secondary metrics, statistical families, model/track matrix, ablations, repetitions, exclusions, stopping rules, and versioned post-freeze changes. Test access remains `NO_ACCESS_CONFIRMED`; no test asset or result was read. The plan is `BLOCKED_PENDING_APPROVAL` until model and data gates close.

## Next window: one task only

`P5-MAIN-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and audit whether the frozen main matrix can run. Ordinary development must not read test input/gold/private mapping. If approved models, inputs, or runtime are unavailable, record a formal blocked run plan and no model outputs. Run checks, commit, and push.

## P5-FINAL-CALIBRATION-001 completed

Final calibration is formally `BLOCKED`: paper-ready train/dev manifest, approved model configuration, and approved runtime are unavailable. No checkpoint, prompt adaptation, threshold fit, or calibration score was fabricated; model set and primary metrics remain frozen, and test access is `NO_ACCESS_CONFIRMED`.

## Next window: one task only

`P5-PREREG-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and freeze hypotheses, primary/secondary metrics, statistical families, model matrix, ablations, repeats, exclusions, stopping rules, and test-access ledger before any test asset access. Do not read test input/gold/private mapping. Run checks, commit, and push.

## Push block carried forward

P5-FINAL-CALIBRATION-001 is locally complete at `56941c96d36d6d1bd9367fd817b80d38500216ae`, but GitHub push and remote SHA verification failed. Keep `BLOCKED_PUSH`, retry during the next delivery, and continue P5-PREREG-001 locally.

## P5-BENCHMARK-INTEGRATE-001 completed

FD-Gen produced no cases, so integration is formally `BLOCKED_NO_INPUT`. No empty or fabricated benchmark addendum was written. The future seven-step integration chain is frozen and test access remains `NO_ACCESS_CONFIRMED`.

## Next window: one task only

`P5-FINAL-CALIBRATION-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and use only available paper-ready train/dev inputs plus the frozen P4 selection protocol. Do not read individual test input/gold or change the model set/main metrics. If approved models or inputs are unavailable, record `BLOCKED` and do not fabricate calibration results. Run checks, commit, and push.

## P5-FDGEN-001 completed

The frozen FD-Gen plan remains `FROZEN_PLAN_NOT_EXECUTED`. The P5 decision is formally `BLOCKED` because generator/FDS versions, case counts, final plan hash, runtime, and approvals are unresolved. No simulator ran, no scenes were fabricated, and generation/failure/cost outputs remain empty or unset.

## Next window: one task only

`P5-BENCHMARK-INTEGRATE-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and make a formal no-input integration decision if P5-FDGEN produced no cases. If approved generated cases later exist, re-run the full canonical adapter, builders, split/leak audit, gold/trace, schema, and scorer chain without reading model test results. Run checks, commit, and retry pending GitHub pushes.

## P4-PILOT-FREEZE-001 completed

The train/dev pilot matrix is frozen. Main tracks are `text_only_table` and `retrieval`; exploratory tracks are `multimodal`, `plot`, `formula_fds_proxy`, and `tool_use`. Repetitions, budgets, failure rules, and no-test-selection policy are explicit. The plan remains `BLOCKED_PENDING_APPROVAL` because model IDs, runtime/pricing, and train/dev sample manifest are unavailable; sample counts and cost cap are `null`.

## Next window: one task only

`P5-FDGEN-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and inspect only the already frozen FDS/FD-Gen plan plus safe runtime metadata. Do not read test/private assets or modify `../../3.数据集`. If the runtime or approvals are unavailable, record a formal blocked generation decision and do not fabricate scenes. Run checks, commit, and push.

## Push block carried forward

P4-PILOT-FREEZE-001 is locally complete at `4cece19b1b251e83cf77a77c50fb0664d7d2ce0b`, but GitHub push and remote SHA verification failed. Keep `BLOCKED_PUSH`, retry during the next delivery, and continue P5-FDGEN-001 locally.

## P4-TOOL-001 completed

Tool tracks are frozen independently for retrieval, plot, formula/FDS proxy, and declared tool use. Each has its own whitelist, knowledge-base identity, call/cost limits, replayable trace, and information-budget label. Current execution is `BLOCKED` without an approved model/runtime; no test/private assets were read.

## Next window: one task only

`P4-PILOT-FREEZE-001`: read the mandated handoff files and task package, create a new `IN_PROGRESS` session draft, and freeze the train/dev pilot matrix, model/track set, repetitions, sample counts, prompts, budgets, failure rules, main/exploratory matrix, and test-access ledger. Do not select anything from test performance. Run checks, commit, and retry all pending GitHub pushes.

## Earlier push block resolved

P4-BASELINE-LLM was locally complete at `f0a25ceecc07fa7cc4de7051d71ddc9b92838618`; its initial GitHub port 443 block was resolved when the P4-TOOL-001 chain reached `origin/main` at `96ece1811e0c9dfabfce580eeb0f308ddea862e7`.

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
