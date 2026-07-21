# FireWorldBench v2 路线图

本路线图替代旧 P0-P7 执行链。旧阶段记录仅保留为历史证据，不构成当前冻结或完成状态。

## 2026-07-20 execution update

The A5 FDS core target has been completed as a separately accepted v3.3.1
package: 180 strict-qualified Events and 4,039 QA. A6 external-domain work is
active but source-specific: Immersed, PolyU and FURG have audited raw/candidate
evidence; FURG is a substitute video track, not Fire360. DeepQuest is an
in-progress image substitute download. Detectium is quarantined and several
planned sources remain honest gaps. See `docs/DATASET_STATUS_2026-07-20.md`.

Finalization must build accepted external sources as isolated packages and
reports. They do not alter FDS Core, enter the FDS Overall leaderboard, or
inherit target-source names.

## 2026-07-20 finalization boundary

The current finalization objective is a v2-compliant implementation and release
framework, not a false claim that every planned external source is complete.
`docs/DATASET_STATUS_2026-07-20.md` fixes the accepted FDS Core, external
candidate, substitute, quarantine, and gap states. Continue A6-A9 work only as
source-separated packages. External source acceptance is fail-closed; deferred
license/contact confirmation is recorded as deferred, never passed.

| 阶段 | 目标 | 必要输出 | 出口门禁 |
|---|---|---|---|
| A0 方案对齐 | 以核心 PDF 重置项目事实源 | 不可变决策、冲突审计、迁移边界 | 高层入口不再引用旧方案为权威 |
| A1 架构冻结 | 冻结九任务、三轨、Fire Event/QA、来源、split、指标、QC | 协议文档、Schema、配置、决策记录、契约测试 | 所有 fixture 通过；无未声明任务或排行榜定义 |
| A2 20-event pilot 准备 | 准备 FDS 原型与三代表任务 | 20 个 event 设计、`L1-2/L2-1/L3-3` builder 规则、至少 S/I 或 S/V、成本计划 | FDS 版本/网格/边界/seed 追溯方案通过 |
| A3 20-event pilot 执行 | 小规模验证工程与科学稳定性 | 独立 events、QA、困难负例、event split、baseline、成本/存储/标签报告 | Schema 100%；泄漏 0；候选均衡；标签稳定；成本可接受 |
| A4 九任务扩展 | 在 pilot 证据上实现九个 builder | 九任务可重复构建和逐任务评分 | 每任务输入/输出/标签/候选/评分有测试；歧义样本隔离 |
| A5 180-event release | 批量生成核心 FDS 数据 | 约 180 events、4,000-6,000 QA、IID/OOD splits | 事件计数真实；FDS 失败留痕；主数据质量门禁通过 |
| A6 外部域桥接 | 接入 External-CFD、Experiment、Real-Visual OOD | 来源级 Fire Events 和独立报告 | 许可与标签范围确认；不越权造标签；不进入不可比 Overall |
| A7 模型评测 | 统一模型接口和主榜 | 主榜、分层/分任务/分轨/分源结果、校准和失败报告 | 评分可从原始预测重算；无 LLM Judge 主评分 |
| A8 FireState Card | 轻量失败模式验证 | 确定性 Card、原输入 + Card 对比 | 不扩展为 Agent/大型模型；仅作为 proof-of-concept |
| A9 论文与发布 | 冻结证据和合规包 | 图表、证据矩阵、数据卡、许可、复现包 | 所有数字可追溯；公开/私有分离；限制与负结果完整 |

## 当前允许范围

当前执行 A0-A2。允许文档、Schema、配置、接口骨架、最小 fixture 和 pilot 规划；不允许批量下载、180-event 生成、正式训练、复杂方法或主实验。

## Pilot 硬门禁

只有同时满足以下条件，A4/A5 才能启动：

1. 20 个独立 Fire Events，不用相邻切片虚增事件数。
2. `L1-2`、`L2-1`、`L3-3` 端到端完成，至少两个轨道。
3. 自动标签可从配置/轨迹确定性重算，困难负例满足物理可区分性。
4. `event_group` 跨 split 泄漏为 0；文件名/路径/元数据无标签泄漏。
5. 所有 Event/QA 通过 Schema；缺失模态显式 `null`。
6. 简单 chance/rule baseline 可复现。
7. 给出单事件 CPU 时间、峰值内存、原始/派生存储和标签稳定性报告。
8. 阶段、风险、机制、dead-band 和并列容差中需要专家确认的项已批准或明确排除。

## 2026-07-21 Finalization Update

FDS Core v3.3.1 is the accepted, immutable main package: 180/180 strict Events
and 4,039 QA. Current work is benchmark finalization, not data production.
External formal Events/QA remain zero; candidates, substitutes, quarantine and
gaps remain source-separated and never enter FDS Overall. The active hard gate is
the model API authorization failure (HTTP 403) after an otherwise valid public
S-track dry-run. Continue validators, baselines, reports, release evidence and
acceptance documentation without changing frozen data.

## 2026-07-21 Runner and Reporting Update

FDS Core v3.3.1 remains immutable and accepted: 180/180 strict Events and
4,039 QA. External formal Events/QA remain zero; candidate, substitute and
quarantine states are unchanged and excluded from FDS Overall. The fixed
OpenAI-compatible runner model is `openai/gpt-4o-mini`; a proxy-backed API
smoke test succeeded and an S-track full run is in progress. The active hard
gate is now completion of that run followed by private deterministic scoring,
not dataset work. Track-aware scoring, release verification, evidence matrix,
CSV task tables and source/task/track coverage reporting write only to
`artifacts/`; no LLM judge or unsupported calibration metric enters the main
result.
## 2026-07-21 S-Track Evaluation Update

FDS Core v3.3.1 remains immutable and accepted: 180/180 strict Events and
4,039 QA. External formal Events/QA remain zero; candidate, substitute,
quarantine, and gap states are unchanged and remain outside FDS Overall.

The fixed OpenAI-compatible model openai/gpt-4o-mini completed the FDS public
S track after a nine-task structured-output preflight. All 1,360 predictions
passed schema and semantic validation after retrying 14 transient proxy TLS
failures. The private deterministic FDS S-track macro is 56.194247062475384;
this is not FDS Overall and must not be presented as such. No LLM judge was
used. The active hard gate is independent I/V-track runner support and their
separate protocol-qualified evaluation; no external source processing is
authorized.
## 2026-07-21 Multimodal Evaluation Update

FDS Core v3.3.1 remains immutable and accepted: 180/180 strict Events and
4,039 QA. External formal Events/QA remain zero; candidate, substitute,
quarantine, and gap states are unchanged and remain outside FDS Overall.

The previous S diagnostic run is superseded because its L1-2 candidate assets
were not supplied to the model. The corrected public-asset S run uses
structured_json_and_candidate_hydration_v1 and has 1,360/1,360 valid
predictions, zero missing predictions, and deterministic FDS S-track macro
57.50100292190619. This is a track result, not FDS Overall.

The image adapter openai_image_url_data_v1 has completed the released I track:
66/66 valid predictions, zero missing, with L1-3 score 68.93939393939394.
Only L1-3 is published for I, so I Overall is null. The fixed model declares
text/image/file inputs but no video input; V is explicitly unsupported and no
frame-proxy result is reported. No LLM judge was used.
## 2026-07-21 Strict Baseline Update

Release-native strict baselines were regenerated from frozen public train/test
inputs under the current prediction contract. No API model or dataset processing
was used. On the FDS S track, seeded_chance is 21.03476689780523,
train_majority is 32.50098405595995, and physical_rule is
53.46437556768639; the compliant fixed-model S result is 57.50100292190619.
All four are track-level nine-task macros, not FDS Overall.

On I (L1-3 only), seeded_chance is 34.09090909090909, train_majority is 50.0,
and the fixed model is 68.93939393939394. physical_rule is unsupported for I
because it has no structured physical input. V remains unsupported for the
fixed model. Result tables are generated under artifacts/results/fds_core_v3_3_1.