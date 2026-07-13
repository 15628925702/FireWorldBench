# P2-FREEZE-001 迁移与版本规则

1. ontology、sample/prediction schema、split、leakage policy 或 evaluation protocol 任一变更，必须递增对应版本并写入新的任务记录；不得覆盖旧文件。
2. 已生成的样本、预测、评分和 manifest 必须记录 schema、ontology、split、leakage、evaluation 与 generator/FDS 版本；版本不匹配时拒绝评分。
3. split 变更必须重新执行 group-first、重复/近重复和 OOD 轴审计；已有测试结果不得迁移为新 split 的正式结果。
4. leakage 规则变更必须重新生成匿名映射审计；旧结果只能标记为历史结果，不得直接进入论文主表。
5. evaluation 变更必须保留 case-level 原始指标与失败日志；任何 aggregate 只能作为派生摘要，不能替代任务指标。
6. FD-Gen 参数、seed、预算、失败处理或 case family 变更必须先生成新计划版本，再执行新 pilot；禁止看过 pilot 结果后回填正式参数。
7. 测试集和 private mapping 只允许在预注册授权、batch harness/评分保管人范围内访问，并追加访问 ledger；普通开发与模型流程均不得读取 test gold。
