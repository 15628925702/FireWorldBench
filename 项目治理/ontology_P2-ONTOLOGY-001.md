# P2-ONTOLOGY-001 任务与物理机制 ontology

状态：`DESIGNED_PENDING_EXPERT_APPROVAL`。本体服务于 9 个子任务：`T1-A/B/C`、`T2-A/B/C`、`T3-A/B/C`。P1 freeze 的数据许可和 paper-ready 阻塞继续有效；本文件不授权训练、评测或发布。

## 1. 统一语义

- `unknown` 表示证据不足或不可观测，不等于负类。
- `insufficient_information`/`underdetermined`/`*_unknown` 是拒答或不确定输出，不得按错误负类强行计分。
- 每个事实必须关联可解析的 `observation_id`；不存在证据时只能写 `missing_information`。
- `simulator_truth` 只适用于确实由受控仿真输出提供的量；视觉素材不能生成隐藏 CFD 真值。
- `expert_annotation` 必须记录 rubric、标注者版本和裁决来源；当前专家资源尚未落实。
- `case` 是统计单位；窗口、帧和问题派生物不是独立 case。
- 非法 counterfactual pair 只能标 `pair_invalid`，不能给因果方向分数。

机器定义见 [`ontology_P2-ONTOLOGY-001.json`](ontology_P2-ONTOLOGY-001.json)。

## 2. 九个子任务

| ID | 标签空间 | 可观测性边界 | gold origin | 典型正例 | 反例/拒答 |
|---|---|---|---|---|---|
| T1-A | `fire_forming` / `not_fire_forming` / `insufficient_information` | 需要传感器或已验证视觉证据；单帧不能证明火灾形成 | measurement/simulator/rule/expert | 连续观测满足预注册确认规则 | 只有一张火焰图但无时间/来源，输出 `insufficient_information` |
| T1-B | `fire` / `non_fire` / `ventilation_disturbance` / `sensor_fault` / `insufficient_information` | 归因需要能区分的观测和质量字段 | measurement/simulator/rule/expert | 通风扰动导致同步响应且无火灾证据 | 没有 sensor quality 证据却判 `sensor_fault` |
| T1-C | `query_observation` / `stop_and_decide` / `insufficient_information` | 查询集合、成本和信息价值必须冻结 | rule/expert | 在预算内选择尚未观测且能区分候选的传感器 | 查询名本身带答案，或候选集合缺失 |
| T2-A | `baseline_or_no_fire` / `forming_or_early` / `growth` / `developed_or_peak` / `decay_or_ventilation_change` / `state_unknown` | 阶段需时序/仿真 truth；不能从单帧猜精确 HRR | measurement/simulator/rule/expert | 由时间序列和阶段规则支持 `growth` | 无 HRR 或代理却输出精确 HRR 档位 |
| T2-B | 多标签机制 + `mechanism_unknown` | 只能从可观测 signature 推断；隐藏机制为 unknown | simulator/measurement/literature/expert | 温度响应顺序与通风证据共同支持 `ceiling_jet` | 仅凭视觉颜色命名 `backlayering` |
| T2-C | `consistent` / `inconsistent` / `underdetermined` | 需适用的冻结约束和证据 | rule/simulator/expert | 解释与给定通风方向和响应顺序一致 | 没有适用约束却标记物理违规 |
| T3-A | `increase` / `decrease` / `stable` / `mixed_or_non_monotonic` / `trend_unknown` | 目标变量、截止时刻、预测 horizon 必须明确 | measurement/simulator/rule | 30s horizon 温度趋势方向正确 | 单位未知时给出精确未来数值 |
| T3-B | `case_a_higher_risk` / `case_b_higher_risk` / `no_material_difference` / `pair_invalid` / `underdetermined` | 只对单变量、同 base case、参数 diff 完整的 pair 作因果判断 | simulator/rule/expert | 受控风量变化导致 A/B 风险方向一致 | D01 多因素配置比较被称为因果反事实 |
| T3-C | `trace_supported` / `trace_partially_supported` / `trace_unknown` | 节点、边、顺序逐项有 evidence 或 unknown | measurement/simulator/rule/literature/expert | `initial_state -> mechanism -> transition -> outcome` 每段可追溯 | 末端答案正确但中间机制链无证据 |

## 3. 机制层级

### Level 0：观测与质量

`time_series`、`temperature_signal`、`concentration_signal`、`flow_or_pressure_signal`、`visual_fire`、`visual_smoke`、`sensor_fault_signal`、`missing_observation`。

### Level 1：可观测/可推断过程

`fire_forming`、`growth`、`decay_or_change`、`buoyant_plume`、`ceiling_jet`、`longitudinal_ventilation`、`sidewall_extraction`、`smoke_layer_formation`、`backlayering`。

### Level 2：任务结论

`risk_level`、`state_label`、`trend_direction`、`response_order`、`counterfactual_direction`、`state_transition`。

Level 2 结论必须由 Level 0 观测和适用的 Level 1 机制证据支持；不能跳过证据直接从图像外观产生 Level 2 物理结论。

## 4. Physical violation taxonomy

| 代码 | 名称 | 触发条件 |
|---|---|---|
| `V_DIRECTION` | wrong direction | 趋势或响应方向违反冻结关系 |
| `V_TEMPORAL_ORDER` | wrong event order | 事件/传感器顺序错误 |
| `V_VENTILATION_SIGN` | ventilation sign error | 通风/排烟影响方向错误或无证据 |
| `V_BACKLAYERING` | backlayering constraint | backlayering 与流动/几何证据矛盾 |
| `V_MASS_ENERGY` | mass/energy constraint | 违反给定质量、能量或 HRR 约束 |
| `V_UNIT` | unit/dimension error | 单位缺失、冲突或量纲错误 |
| `V_EVIDENCE` | unsupported evidence | evidence 缺失或不支持主张 |
| `V_OBSERVABILITY` | unobservable claim | 把隐藏 CFD truth 写成观测事实 |
| `V_CAUSAL_LEAP` | causal leap | 无干预/机制/证据却断言因果边 |
| `V_STATE_TRANSITION` | invalid state transition | 状态转移不可能或无支持 |
| `V_PAIR_INVALID` | invalid pair | A/B 改变多个因素或缺 intervention 记录 |
| `V_METADATA_LEAK` | metadata answer leak | 文件名、来源、split 或查询名泄漏答案 |

## 5. 缺失、拒答和评分语义

| 情况 | 规范输出 | 评分原则 |
|---|---|---|
| 关键观测缺失 | `insufficient_information` 或任务对应 `*_unknown` | 不当作错误负类；记录缺失原因 |
| 物理真值不可观测 | `underdetermined` / `trace_unknown` | 禁止视觉猜测；证据字段为空或仅指向缺失 |
| pair 参数不满足单变量 | `pair_invalid` | 不进入因果方向主指标；进入质量报告 |
| 证据 ID 不存在 | 保留原输出，增加 `V_EVIDENCE` | evidence 得分为 0，不人工修复 |
| 单位未知 | 保留 raw value，canonical null，增加 `V_UNIT` | 不执行换算；数值指标按任务规则排除/单列 |
| 输出 JSON 无效 | 原文保留，结构字段缺失 | 按失败计分，不删除样本 |

## 6. 任务输入/输出矩阵

| 任务 | 输入 | 必需输出 | 私有 gold |
|---|---|---|---|
| T1-A | 观测窗口、场景、问题 | fire-forming label、risk、evidence、uncertainty | confirm event/time |
| T1-B | 异常窗口、质量/通风上下文 | attribution label、mechanism、evidence | class and rationale |
| T1-C | 不完整观测、查询集合、成本 | query/stop、cost、expected value | utility and optimal action |
| T2-A | 时序/布局/可用上下文 | state、region/HRR if observable、evidence | state origin and tolerance |
| T2-B | 观测和机制候选 | multi-label mechanisms、evidence | mechanism graph/labels |
| T2-C | 观测 + candidate explanation | consistency、violations、evidence | applicable constraints |
| T3-A | 截止观测、horizon、目标变量 | trend/range、event time if valid、evidence | future trajectory/events |
| T3-B | validated A/B pair | ranking、intervention、causal chain | pair direction and diff |
| T3-C | sequence/trace prompt | nodes/edges/order/outcome、evidence | private trace graph |

## 7. 专家待确认项

- T2-A 阶段边界、HRR 档位和 `decay_or_ventilation_change` 的可分辨条件。
- T2-B 机制标签是否允许层级多标签共存，以及 `multiple_mechanisms` 的使用规则。
- T2-C 各 violation code 的最小证据和边界反例。
- T3-A 的趋势容差、horizon 和非单调序列规则。
- T3-B “no_material_difference”的效应阈值和 pair invalid 的自动 validator。
- T3-C trace 节点/边权重、裁决规则和专家一致性要求。

以上事项在专家资源落实和 P2-SCHEMA-001 前保持 `PENDING_EXPERT_APPROVAL`，不能作为已冻结评测参数。
