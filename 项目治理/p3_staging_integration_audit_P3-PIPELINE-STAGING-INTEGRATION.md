# P3-PIPELINE-STAGING-INTEGRATION

本轮只读审计了 `data/raw` 中的 D01、D02、D03、D04、D05、D10 staging。没有修改原始文件，没有执行 FD-Gen/FDS/脚本或可执行文件，没有访问 test/private 资产，也没有安装依赖。

机器可读结果：`p3_staging_integration_P3-PIPELINE-STAGING-INTEGRATION.json`。

| 数据源 | 结果 | 结论 |
|---|---|---|
| D01 | `SEMANTIC_SCHEMA_BLOCKED` | FDS CSV 缺 canonical `case_id`，`Time` 需要显式语义适配。 |
| D02 | `SEMANTIC_SCHEMA_BLOCKED` | 主要是 XLS/XLSX，现有安全适配器不能直接形成 canonical case。 |
| D03 | `SEMANTIC_SCHEMA_BLOCKED` | CSV 有 `Time`，但缺 canonical `case_id`/sequence 语义。 |
| D04 | `GENERATOR_RUNTIME_BLOCKED` | 只盘点生成器/FDS 资产，本轮不执行、不生成 benchmark case。 |
| D05 | `AUX_ONLY_BLOCKED` | 视觉辅助标签，没有 canonical case/time 记录。 |
| D10 | `AUX_ONLY_BLOCKED` | 视觉 OOD 辅助标签，没有 canonical case/time 记录。 |

所有 staging 源均保持 `formal_benchmark_eligible=false`；训练、开发、测试、派生发布和再分发资格均为 `BLOCKED`，许可证和版本证据未被本轮重新确认。
