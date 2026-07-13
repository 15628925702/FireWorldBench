# P2-FREEZE-001 P2 出口审计与封存

日期：2026-07-14  
目标会议：ICLR 2027  
任务状态：DONE_WITH_BLOCKED_GATES

## 审计结论

| 出口 | 结论 | 说明 |
|---|---|---|
| ontology | CONDITIONAL_FREEZE | ontology 文件已入库；正式物理专家批准仍需补签 |
| sample/prediction schema | FROZEN | v2 schema 与字段契约已存在；validator 测试可复现 |
| split | CONDITIONAL_FREEZE | group-first 和 OOD 轴已定义；受 P1 数据许可与敏感重复核验限制 |
| leakage policy | CONDITIONAL_FREEZE | opaque ID 与规则已固定；感知近重复检查仍 BLOCKED |
| evaluation protocol | CONDITIONAL_FREEZE | case-level 指标、失败处理和 aggregate 禁止替代规则已固定 |
| test embargo | ACTIVE | 普通开发、模型流程不得读取 test input/gold/private mapping |
| private test assets | NO_ACCESS_CONFIRMED | 本轮未创建、未读取，仓库仅有占位 README |
| FD-Gen plan | FROZEN_PLAN_NOT_EXECUTED | 参数轴、seed、预算约束和失败规则已预分配；pilot 尚未执行 |

## 决策门

D-005（group-first split）和 D-007（case-level evaluation）当前仍为 `PROPOSED`，不是已批准决策。因此本任务将它们标记为 `BLOCKED_PENDING_APPROVAL`，不伪造批准状态；P3 只能使用本封存版本，不得绕过该门生成正式测试结果。

## P3 输入

- `schemas/benchmark_sample.v2.schema.json`
- `schemas/prediction.v2.schema.json`
- `configs/split_P2-SPLIT-001.json`
- `configs/leak_policy_P2-LEAK-001.json`
- `configs/evaluation_P2-EVAL-001.json`
- `configs/test_embargo.toml`
- `项目治理/fdgen_generation_plan_P2-FREEZE-001.json`
- 本文件与 `项目治理/p2_migration_rules_P2-FREEZE-001.md`

## 明确禁止

本任务不读取或生成仓库外私有测试资产，不生成模型测试结果，不把未授权数据写入 train/dev/test 或公开发布目录。
