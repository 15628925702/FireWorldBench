# Server Handoff Prompt

你现在接手 FireWorldBench 项目，担任 benchmark 架构师、数据工程负责人和实验负责人。

工作区根目录是你当前服务器上包含 `1.参考文献/`、`2.方案研究/`、`3.数据集/`、`5.项目实现/` 的目录。项目仓库位于 `5.项目实现/v1`。

最高优先级规则：

1. `2.方案研究/FireWorldBenchv2(1).pdf` 是唯一核心设计来源。先计算 SHA-256，必须为 `ba63ab8428d1f759629a89864af7f623589d023dd6d5a29e4940fc6d629a19a6`。
2. 先完整阅读 `5.项目实现/v1/AGENTS.md`、`PROJECT_CHARTER.md`、`ROADMAP.md`、`docs/ARCHITECTURE_FREEZE.md`、`docs/TASK_PROTOCOL.md`、`docs/PILOT_20_EVENTS.md`、`进度跟进记录/CURRENT_STATUS.md` 和其 `source_session`。
3. 旧 `src/fireworldbench/`、旧 T1/T2/T3、P0-P7、formal/quasi experiments 和 `artifacts/` 是 `LEGACY-NONCOMPARABLE`。不得把旧结果作为 v2 结果，不得为兼容旧代码修改核心方案。
4. 固定三层九任务与 S/I/V；所有来源先转 Fire Event，再按 event_group split 后派生 QA。
5. 当前阶段是 `V2-A2-PILOT-PREP`。不得直接生成 180 events、运行正式模型矩阵或扩展任务。

接手后的第一轮必须完成：

1. 先运行 `python scripts/verify_transfer_manifest.py --workspace-root ../.. --manifest migration/transfer_manifest.json`，再运行 `python scripts/server_preflight.py --workspace-root ../..`，报告传输完整性、PDF、Git、Python、磁盘、数据目录和 FDS 工具链状态。
2. 创建 Python 3.11 环境并执行全量 pytest、Ruff、mypy；不得安装项目未声明的大型模型或数据。
3. 检测 Linux FDS、Smokeview、FD-Gen 的精确版本与可执行 SHA-256。Windows 的 `FD-Gen.exe` 不能作为 Linux runtime。
4. 审计 `configs/fds_prototype.v2.json` 中仍为 TBD 的版本、mesh、boundary 和 expert thresholds。
5. 先实现并验证 20 个独立 Fire Events 的 dry-run manifest，保证 counterfactual family 和 event_group 不跨 split。
6. 按顺序实现 L1-2、L2-1、L3-3，优先 S+I；加入 filename/path/EXIF、候选位置、时间位置和困难负例检查。
7. 只有 20-event pilot 的 Schema、泄漏、成本、存储和标签稳定性门禁通过后，才提出扩展到九任务与 180 events 的执行申请。

工作要求：保护现有文件和 Git 历史；不删除原始资料；所有修改先测试，再更新 CURRENT_STATUS、会话记录、开放问题和需求追踪；提交并推送时明确列出 commit SHA、测试结果和仍阻塞项。
