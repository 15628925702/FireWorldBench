# P1-FREEZE-001 P1 阶段审计与批准包

审计时间：`2026-07-14 Asia/Shanghai`。本包只审计已经完成的 P1 证据，不新增数据研究。冻结 manifest 及自身哈希见 [`p1_freeze_manifest.json`](p1_freeze_manifest.json) 和 [`p1_freeze_manifest.json.sha256`](p1_freeze_manifest.json.sha256)。

## 1. 出口审计

| 出口 | 结论 | 证据 | 状态 |
|---|---|---|---|
| 文件清单和完整性 | D01-D11 共 312 文件，逐文件路径/大小/SHA-256，manifest 自身哈希已记录 | `data_manifest_P1-DATA-001.json` | PASS |
| 许可、版本、获取日期 | D01-D11 五类用途资格全部 fail-closed；D05/D06 平台许可字段不足以闭合权利链 | `data_license_eligibility_P1-DATA-001.md` | BLOCKED |
| 字段、单位、标准化 | D01-D04 字段契约完成；未知单位保留 `UNKNOWN/BLOCKED`，不做猜测转换 | `data_field_contract_P1-DATA-002.md`, `data_schema_P1-DATA-002.json` | PASS_WITH_SCOPE |
| 质量和缺失 | 312 文件无零字节；D01/D03 CSV 无缺失/异常数值；D02 XLS 语义未闭合 | `data_quality_case_leakage_P1-DATA-003.md` | PASS_WITH_SCOPE |
| case/family/split | D01/D03 group key 可执行；感知重复尚未执行；D01 pair 降级为配置比较 | `data_quality_case_leakage_P1-DATA-003.md` | PASS_WITH_SCOPE |
| 相关工作与创新 | 有 ICLR 2027 暂行政策和相关工作矩阵；未支持“首个/全面”等主张 | `research_venue_relatedwork_contamination_P1-RESEARCH-001.md` | PASS_AS_BOUNDARY |
| ICLR 2027 政策 | 官方确认会议和地区；2027 CFP/Dates 仍未发布，具体 deadline/页数/artifact 全部 TBD/BLOCKED | `research_venue_relatedwork_contamination_P1-RESEARCH-001.md` | BLOCKED |
| 污染与泄漏 | 已定义名称去除、来源外机制题、模板反事实、重复隔离和记忆控制探针；尚未运行模型污染实验 | 同上 | OPEN |
| paper-ready 主实验 | 许可、FDS/FD-Gen 环境、专家、冻结评测尚未满足；MVP 不得当作 paper-ready | D-003、风险登记、数据许可报告 | BLOCKED |

## 2. 决策提交状态

以下决策本轮提交用户/导师批准、拒绝或修改；本记录不代替审批，因此原 `决策记录.md` 中的 `PROPOSED` 状态保持不变。

| 决策 | 建议 | 当前状态 | 影响 |
|---|---|---|---|
| D-002 共享 physical trace 契约 | 作为 P2 ontology/schema 输入，但先由用户/导师批准字段范围 | PENDING_APPROVAL | 未批准前不得冻结正式样本契约 |
| D-003 v1-mvp 与 v1-paper 分层 | 接受“当前仅 MVP/研究性闭环，paper-ready 需补受控 FDS/专家/冻结评测” | PENDING_APPROVAL | 禁止将当前数据支撑 A 会主实验结论 |
| D-004 原始数据区只读 | 作为已执行的工程约束继续采用 | PENDING_APPROVAL | 原始数据不入仓库，派生链只追踪 manifest/rule |
| D-006 视觉数据仅辅助证据 | 接受；不从视觉数据生成 T3 物理演化真值 | PENDING_APPROVAL | 视觉结果与物理推理分开报告 |
| D-008 目标会议 | 用户已指定 ICLR 2027；日期和正式政策待官方发布 | PARTIALLY_RESOLVED | 不倒推 deadline，不把 2026 政策写成 2027 政策 |

## 3. 遗留风险和开放问题

- `R-001/R-002/R-003/R-005/R-007/R-008/R-009/R-011/R-012/R-015/R-016` 继续 `OPEN`；本轮没有证据关闭它们。
- ICLR 2027 CFP、deadline、页数、匿名和 artifact 规则：`OPEN/BLOCKED`，官方页面发布后重新审计。
- D01 配置编号到排烟物理参数的映射、D02 XLS 单位、D05/D06 权利链与视觉序列：`BLOCKED`。
- FDS/FD-Gen 运行环境、算力预算、专家资源和模型预算：`OPEN`。

## 4. P2 输入和边界

P2 可开始的输入：

1. P1 的 manifest、字段契约、质量报告和 venue/污染边界。
2. `D-002` 的共享 trace 契约草案，但必须继续标记 `PENDING_APPROVAL`。
3. D01/D03 的 group key 规则和 D01 “配置比较而非单变量物理 pair”的限制。

P2 不得做的事情：

- 不得把 `BLOCKED` 数据变成训练/测试/发布数据。
- 不得在未批准 D-002/D-003/D-004/D-006 前宣称正式 benchmark freeze 或 paper-ready 结果。
- 不得把 ICLR 2026 约束当作 ICLR 2027 已定政策。
- 不得把“研究设计边界”写成已经证明的创新性或模型能力结果。

下一任务：`P2-ONTOLOGY-001`。
