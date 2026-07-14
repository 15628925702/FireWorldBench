---
handoff_id: H-20260714-S047-001
handoff_state: READY
session_id: 2026-07-14_S047
task_id: P1-PLANNING-STAGING
next_task: P3-PIPELINE-STAGING-INTEGRATION
---

# 2026-07-14_S047_P1-PLANNING数据下载staging

## 1. 会话元数据

- 任务 ID：`P1-PLANNING-STAGING`
- 状态：`DONE_LOCAL`
- 开始/结束：`2026-07-14 Asia/Shanghai`
- 执行者：`Codex`
- Git branch：`main`
- Git HEAD：提交前为 `09c6a7be0c49470673f4a7199d6362e61195cde6`；最终任务提交 SHA 以 `git rev-parse HEAD` 为准。
- Git remote：`origin https://github.com/15628925702/FireWorldBench.git`
- 任务级 Git 交付：`COMMIT_ONLY_PENDING_PUSH`
- 任务提交 SHA：以 `git rev-parse HEAD` 为准。
- 远端推送结果：`PENDING_PUSH_ATTEMPT`
- 工作区既有改动：会话开始时已有 `PROJECT_CHARTER.md`、`README.md`、`开发要求约束/开发约束总则.md`、`详细设计规划/README.md` 未提交改动；本轮未读取其 diff、未修改、未暂存。

## 2. 目标与验收

- 本轮目标：把后续 pipeline 预研可用的原始数据纳入工程本地 `data/raw` staging，生成逐文件 manifest 和 SHA-256，并保持许可证/再分发 fail-closed。
- 明确不做：不下载 D06/D07/D08/D09/D11；不安装依赖；不运行模型；不读取 test gold/private mapping；不修改仓库外 `../../3.数据集`；不读取 `../../4.升级拓展`。
- 验收标准：
  - [PASS] D01/D02/D03/D04/D05/D10 staging manifest 完成：`项目治理/download_manifest_<DATASET_ID>_planning.json`。
  - [PASS] 总登记完成：`项目治理/download_staging_registry_P1-PLANNING.json`。
  - [PASS] 所有 staged 数据保持 `license_status UNKNOWN/BLOCKED`、`redistribution_status UNKNOWN/BLOCKED`、`formal_benchmark_eligible=false`。
  - [PASS] 原始数据不进 Git：`data/raw/**` 仍由 `.gitignore` 排除。

## 3. 输入与依据

- 必读文件：`AGENTS.md`、`进度跟进记录/CURRENT_STATUS.md`、`进度跟进记录/2026-07-14_S046_P7-RELEASE-001最终发布冻结阻断决策.md`、`进度跟进记录/NEXT_SESSION_PROMPT.md`、`configs/data_sources.toml`、`项目治理/data_manifest_P1-DATA-001.json`、`项目治理/data_license_eligibility_P1-DATA-001.md`。
- 数据/配置版本：既有 P1 manifest `项目治理/data_manifest_P1-DATA-001.json`；本轮新增 planning manifests 和 registry。
- 关键假设：本轮是 planning-stage staging，不完成最终许可证核验；D10 官方来源未在本地证据闭合，因此 source URL 保留 `UNKNOWN_OFFICIAL_SOURCE_NOT_REVERIFIED`。

## 4. 实际完成

- 新增 D01/D02/D03/D04/D05/D10 逐文件 planning manifests，均含 source_url、acquisition_date、upstream_version_or_commit、download_status、license_status、redistribution_status、intended_role、file_count、total_bytes、files、raw_files_unchanged、formal_benchmark_eligible 和 note。
- 新增 `项目治理/download_staging_registry_P1-PLANNING.json`，登记 staged 与按指令跳过的数据集。
- 新增 `项目治理/download_staging_audit_P1-PLANNING.md`，记录状态、风险和验证命令。
- 更新 `configs/data_sources.toml`，增加 staging_dir/source_url/planning_download_status/planning_manifest；`eligible=false` 保持不变。

## 5. 未完成与偏差

- D10 官方 source_url 未闭合：本地证据只有 existing local sample，未把未核验 URL 写成正式来源。
- D06/D07/D08/D09/D11 按用户指令不下载。
- 没有完成许可证最终核验；没有产生模型实验结果。

## 6. 验证证据

| 状态 | 时间 | 执行环境/版本 | 命令/检查 | 退出码 | 关键结果 | 证据路径 |
|---|---|---|---|---:|---|---|
| PASS | 2026-07-14 | Anaconda/base Python | manifest generation + SHA-256 | 0 | D01/D02/D03/D04/D05/D10 写入 6 个 manifest + 总登记 | `项目治理/download_staging_registry_P1-PLANNING.json` |
| PASS | 2026-07-14 | Anaconda/base Python | P1 manifest comparison | 0 | staged 文件与既有 P1 manifest 按 filename/size/SHA-256 全部匹配 | 各 `download_manifest_*_planning.json` |
| PASS | 2026-07-14 | Anaconda/base Python | `python scripts/probe_data_contract_p1_data_002.py` | 0 | D01/D03 probe 可读 | stdout |
| PASS | 2026-07-14 | Anaconda/base Python | `python scripts/audit_data_quality_p1_data_003.py` | 0 | 312 文件、0 zero-byte；已知 FD-Gen preview 重复 hash | stdout |
| PASS | 2026-07-14 | Anaconda/base Python | `python scripts/check_project.py` | 0 | 34 required files and core policies verified | stdout |
| PASS | 2026-07-14 | Anaconda/base Python | `python -m fireworldbench.cli pipeline-inventory --root data/raw --output %TEMP%/fwb_staging_inventory.json` | 0 | 196 staging files inventoried | `%TEMP%/fwb_staging_inventory.json` |
| PASS | 2026-07-14 | Anaconda/base Python | `python -m fireworldbench.cli doctor --root .` | 0 | bootstrap invariants verified | stdout |
| PASS | 2026-07-14 | Anaconda/base Python | `python -m pytest -q` | 0 | 120 passed | stdout |
| PASS | 2026-07-14 | Anaconda/base Python | `mypy src` | 0 | Success: no issues found in 37 source files | stdout |

未运行的检查及原因：Ruff 未运行；当前环境未安装，且本轮禁止安装依赖。

## 7. 变更清单

- 新增：`项目治理/download_manifest_D01_planning.json`、`项目治理/download_manifest_D02_planning.json`、`项目治理/download_manifest_D03_planning.json`、`项目治理/download_manifest_D04_planning.json`、`项目治理/download_manifest_D05_planning.json`、`项目治理/download_manifest_D10_planning.json`、`项目治理/download_staging_registry_P1-PLANNING.json`、`项目治理/download_staging_audit_P1-PLANNING.md`、本会话记录。
- 修改：`configs/data_sources.toml`、`进度跟进记录/CURRENT_STATUS.md`、`进度跟进记录/NEXT_SESSION_PROMPT.md`。
- 删除：无。
- 生成但不进 Git：`data/raw/**` 原始 staging 文件；`%TEMP%/fwb_staging_inventory.json`。

## 8. 决策、风险和问题

- 新/更新决策：planning-stage staging only；所有 staged 数据 `formal_benchmark_eligible=false`。
- 新/更新风险：D10 官方来源未闭合；所有数据许可证最终核验仍未完成。
- 需要用户决定：后续若要下载 D06 全量或接入正式 benchmark，需要先确认存储、许可证和再分发边界。

## 9. 下一轮交接

- 唯一下一任务：`P3-PIPELINE-STAGING-INTEGRATION - 将 planning-stage staging manifest 接入 pipeline 的受限预研入口`
- 第一条命令/动作：检查本轮 commit/push 状态和 `download_staging_registry_P1-PLANNING.json`。
- 必须复用：本轮 6 个 per-dataset manifest、总 registry、审计记录。
- 禁止重复/禁止做：不得把 UNKNOWN/BLOCKED 许可证数据标记为正式 train/dev/test；不得提交 `data/raw/**`；不得读取 test gold/private mapping；不得读取 `../../4.升级拓展`。
- 完成标准：pipeline 只能消费 planning-stage manifest，并在输出中显式保留 `formal_benchmark_eligible=false`。
