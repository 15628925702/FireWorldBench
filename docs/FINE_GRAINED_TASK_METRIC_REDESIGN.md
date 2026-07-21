# FireWorldBench v2 细粒度任务与指标重设计

状态：`USER-DIRECTED-REDESIGN-DRAFT`
日期：`2026-07-21`
协议代号：`FWB-FINEGRAIN-v1`

## 1. 为什么重设计

现有合规结果并非所有任务都过高：`openai/gpt-4o-mini` 的 FDS S 轨九任务宏平均为
57.50，其中 L1-1/L1-2/L1-3 分别为 18.10/31.23/39.84。真正的问题是难度不均、部分
任务可被组件平均掩盖，以及极小 support 产生虚高：L2-3 在 S 测试中 n=1 得到 100，
L3-3 n=7 得到 71.43；I 轨只有 L1-3，不能形成完整 I Overall。

本次重设计不通过分数缩放、故意制造歧义或查看私有测试结果后反复调题来“压分”。
30--50 被定义为多家族代表模型在冻结开发挑战集上的难度校准目标带，而不是每个模型、
每个任务必须落入的分数区间。正式测试一旦解盲不得再按模型表现修改任务。

## 2. 保留与废止

保留：

- L1 Dynamic Perception、L2 State Recovery、L3 Evolution Reasoning 三层研究目标。
- S Structured、I Image、V Video 三轨真实输入边界。
- Fire Event、event_group-first split、公开问题/私有 gold 分离、来源隔离和确定性评分。
- FDS Core v3.3.1 的只读性；180/180 Events、4,039 QA 和既有正式结果保持不变。
- 外部 candidate/substitute/quarantine 状态及“绝不进入 FDS Overall”的规则。
- 固定离散答案、严格 schema、semantic validator、失败计数和禁止 LLM judge。

废止为新协议主张：

- 用单字段 Accuracy 或多字段 Accuracy 均值统一充当所有任务主指标。
- 用极少样本任务参与模型排名。
- 仅凭总体 Accuracy 判断任务质量。
- 把有效预测子集分数当作完整覆盖分数。
- 未冻结时距、配对或事件时间字段时报告对应指标。
- 将旧 v3.3.1 prediction schema 和结果直接迁移成新协议结果。

## 3. 新九任务总览

| ID | 新任务 | 强制结构化输出 | 新主指标 | 关键诊断指标 |
|---|---|---|---|---|
| L1-1 | 多信号早期事件归因 | event_class | Macro-F1 | balanced accuracy、per-class recall、ECE/Brier（有合法 confidence 时） |
| L1-2 | 因果下一状态辨别 | choice | horizon-macro Accuracy | 各 horizon/difficulty Accuracy、hard-negative error rate |
| L1-3 | 时序违规定位与分类 | consistency + first_violation_bin + violation_type | Hierarchical Joint Exact Match | consistency Accuracy、violation Macro-F1、location Accuracy |
| L2-1 | 火源—阶段联合恢复 | source_region + stage | Joint Exact Match | 两字段 Accuracy、stage Macro-F1 |
| L2-2 | 风险区域—等级—驱动因素恢复 | risk_region + risk_level + risk_driver | Joint Exact Match | 三字段指标、risk-level Macro-F1 |
| L2-3 | 主导机制—流向—控制域诊断 | mechanism + flow_direction + control_regime | Joint Exact Match | mechanism Macro-F1、各组件 Accuracy |
| L3-1 | 多时距多变量趋势预测 | 3 horizons × temperature/smoke/visibility | horizon-level Strict Triple Exact Match 的宏平均 | 变量/时距 Macro-F1、单字段 Accuracy |
| L3-2 | 首次高风险越阈预测 | region + time_bin + trigger_variable | Joint Exact Match | region Macro-F1、time-bin ordinal error、trigger Macro-F1 |
| L3-3 | 反事实效应分解 | direction + magnitude_bin + earliest_affected_target | Joint Exact Match | direction Macro-F1、pair-swap consistency |

### 轨道资格上限

三轨是三个相互独立的评测套件，不要求一个模型同时完成 S/I/V。S 可选择文本模型，I 可选择
图像/VL 模型，V 可选择支持 direct-video 的模型；三轨可以使用完全不同的固定 exact model
ID。同一模型支持多轨时可以自愿参加多个套件，但不支持其他轨道不会扣分，也不存在跨轨总分。

每轨在模型选择前冻结自己的任务集合、答案空间和输入适配器。新协议不假设九任务都能从
所有模态可靠作答：

| Task | S | I | V | 说明 |
|---|---|---|---|---|
| L1-1 | full | unsupported | unsupported | 传感器故障与通风扰动不能仅凭 RGB 可靠区分 |
| L1-2 | full | eligible | eligible | 必须真实提供候选图像/视频，不得用路径或文字替代 |
| L1-3 | full | eligible | eligible | I 需要有序多帧；V 需要 direct-video input |
| L2-1 | full | conditional | conditional | 只有区域布局和阶段视觉证据充分时发布 |
| L2-2 | full | unsupported | unsupported | CO/温度等风险驱动不可从普通 RGB 可靠恢复 |
| L2-3 | full | conditional | conditional | 控制条件、布局和动态流向必须可见 |
| L3-1 | full | unsupported | unsupported | 完整三变量含温度，不能用视觉代理冒充 |
| L3-2 | full | unsupported | unsupported | 触发变量包含温度/CO，普通 RGB 信息不足 |
| L3-3 | full | conditional | conditional | 必须有严格匹配 A/B 视觉对与冻结 pairing contract |

未来若要建立视觉专用趋势或风险任务，必须使用新的 `I-*`/`V-*` subtrack ID 和可观察答案
空间，不能沿用 S 轨字段后把不可观察物理量补造出来。S 九任务可以形成 `S Overall`；I/V
只能形成各自冻结任务集合的 `I Suite Macro` / `V Suite Macro`，不得称为跨轨 FDS Overall。
不同模型只允许在相同轨道、相同任务集合、相同 subset 和相同协议版本内比较。

## 4. 逐任务协议

### L1-1 多信号早期事件归因

- 目的：区分真实火灾、无火背景、通风扰动和传感器故障，并验证模型是否跨信号求证。
- 输入：冻结的早期窗口；S 提供多传感器时序，I/V 只在视觉证据足够时发布。
- 输出：`event_class ∈ {fire, no_fire, ventilation_disturbance, sensor_fault}`。
- 主指标：四类 Macro-F1。原因是安全类任务不能让大类 Accuracy 掩盖少数类完全失效。
- 诊断：balanced accuracy、per-class precision/recall/F1、confusion matrix、合法置信度校准。
- 难度：同几何、同亮度、相近温升/烟量的匹配负例；故障和通风扰动必须具有邻近信号证据。

### L1-2 因果下一状态辨别

- 目的：从当前动态与控制条件中选择物理上最合理的下一状态。
- 输入：当前窗口、冻结 `horizon_s`、5 个同场景候选；候选必须匹配视角、总体烟量和背景。
- 输出：`choice`，只能取冻结候选 ID。
- 主指标：先在每个 `horizon_s` 桶计算 Accuracy，再对时距桶宏平均。
- 诊断：按 hard-negative 类型、OOD split 和任务难度分层的 Accuracy。
- 难度：负例来自唯一控制变量不同、时间方向错误、传播方向错误或近邻时刻；禁止随机异背景。
- 元数据门禁：`horizon_s` 和 `difficulty_type` 未冻结时，本任务不得进入新主榜。

### L1-3 时序违规定位与分类

- 目的：不仅判断序列是否异常，还要定位首次违规位置并识别违规类型。
- 输出：
  - `consistency ∈ {consistent, inconsistent}`；
  - `first_violation_bin ∈ {none, early, middle, late}`；
  - `violation_type ∈ {none, reverse, jump, disappearance, direction_flip, sensor_conflict}`。
- 主指标：三字段 Hierarchical Joint Exact Match；consistent 样本要求两个附加字段均为 `none`。
- 诊断：consistency Accuracy；仅在不一致 gold 上报告 violation Macro-F1 和 location Accuracy。
- 难度：局部倒放、短跳变、同场景拼接和跨通道冲突；扰动长度及位置跨类别平衡。

### L2-1 火源—阶段联合恢复

- 目的：从部分观测同时恢复火源区域和发展阶段。
- 输出：`source_region ∈ R1..R8`，`stage ∈ {incipient, growth, developed, decay}`。
- 主指标：Joint Exact Match；只有两个字段同时正确才记为该条主指标正确。
- 诊断：source Accuracy、stage Accuracy、stage Macro-F1、区域混淆矩阵。
- 难度：对称区域、相邻区域、阶段边界附近但仍可唯一作答的样本；边界歧义继续排除。

### L2-2 风险区域—等级—驱动因素恢复

- 目的：恢复最高风险区域、严重程度及造成风险的首要物理驱动。
- 输出：
  - `risk_region ∈ R1..R8`；
  - `risk_level ∈ {low, moderate, high, critical}`；
  - `risk_driver ∈ {temperature, visibility, co, soot}`。
- 主指标：三字段 Joint Exact Match。
- 诊断：三个组件 Accuracy、risk-level Macro-F1、risk-driver Macro-F1。
- 标签门禁：driver 必须由冻结风险函数的最大贡献项确定；近似并列进入 ambiguous，不得人工猜测。

### L2-3 主导机制—流向—控制域诊断

- 目的：把“机制名称识别”扩展为可验证的机制、运动方向与控制主导域联合诊断。
- 输出：
  - `mechanism ∈ {buoyant_plume, ceiling_jet, smoke_layer, longitudinal_ventilation, backlayering, extraction_dominated}`；
  - `flow_direction ∈ {vertical, downstream, upstream, bidirectional, mixed}`；
  - `control_regime ∈ {buoyancy, ventilation, extraction, mixed}`。
- 主指标：三字段 Joint Exact Match。
- 诊断：mechanism Macro-F1、各组件 Accuracy、confusion matrix。
- support 门禁：每个 mechanism 在计分 split 至少 20 条且至少覆盖 3 个 event_group；不足则只报告、不排名。

### L3-1 多时距多变量趋势预测

- 目的：预测短、中、长三个时距的温度、烟气和能见度趋势，避免单时距偶然命中。
- 输出：冻结 3 个 horizon；每个 horizon 分别输出 temperature/smoke/visibility 的 up/stable/down。
- 主指标：每个 horizon 先算 Strict Triple Exact Match，再对 horizon 宏平均。
- 诊断：每变量每时距 Accuracy/Macro-F1、趋势转折错误率、OOD split 分解。
- 标签门禁：horizon、dead-band 和有效未来窗口必须在 QA metadata 中机器可读且冻结。

### L3-2 首次高风险越阈预测

- 目的：预测哪个区域、在哪个离散时间桶、由哪个变量最先触发高风险。
- 输出：
  - `first_high_risk_region ∈ {R1..R8, none}`；
  - `time_bin ∈ {none, 0_10s, 10_30s, 30_60s, after_60s}`；
  - `trigger_variable ∈ {none, temperature, visibility, co, soot}`。
- 主指标：三字段 Joint Exact Match。
- 诊断：region Macro-F1、time-bin Accuracy 和 ordinal distance、trigger Macro-F1。
- 标签门禁：阈值、并列容差、时间桶和未来窗口均冻结；没有精确预测时间字段时不报告 event-time MAE。

### L3-3 反事实效应分解

- 目的：比较只改变一个控制变量的 A/B 场景，并识别效应方向、幅度和最早影响对象。
- 输出：
  - `direction ∈ {A, B, same}`；
  - `magnitude_bin ∈ {negligible, small, medium, large}`；
  - `earliest_affected_target ∈ {none, temperature, smoke, visibility, risk_region}`。
- 主指标：三字段 Joint Exact Match。
- 诊断：direction Macro-F1、magnitude Accuracy、pair-swap consistency、干预轴分层结果。
- 配对门禁：必须冻结 pair_id、唯一干预轴、A/B 交换映射和 same/magnitude 阈值。

## 5. 计分和覆盖规则

1. 每任务主指标范围 0--100；缺失、malformed 和 schema-invalid prediction 在完整分母中计 0。
2. 同时报告 `contract_adjusted_score` 和 `valid_only_score`；排行榜只使用前者。
3. 每任务必须报告总 n、event_group 数、gold class support、有效/缺失/malformed/unsupported 数及 coverage。
4. 不满足 support 门禁的任务显示 `not_ranked_insufficient_support`，不得用 0/100 参与模型排序。
5. S/I/V 是独立套件，可以由不同模型参加；不支持未参评轨道不计 missing、不扣分。
6. `S Overall` 仅在 S 九任务均通过 support 与协议门禁后取九任务无权宏平均。I/V 按各自预先
   冻结且证据充分的任务集合报告 suite macro；不生成跨 S/I/V 总分。
7. 外部 CFD、Experiment、Real-Image/Video OOD 永不进入 FDS Overall。
8. confidence 为空时 ECE/Brier 为 `not_reported`，不得填默认 0.5。
9. 不使用 LLM judge，不对近似字段名自动映射，不修复模型答案。

## 6. 难度校准而非按分调题

开发挑战集冻结前使用至少四个不同家族、不同供应商的代表模型和三类确定性基线校准：

- 代表模型九任务中位数目标：30--50；最强模型可高于 50，但若多个家族在同任务均超过 65，必须审计泄漏、候选过易和标签捷径。
- chance/majority/trivial-rule 应显著低于代表模型；若规则基线接近强模型，任务更可能在测模板或公开规则。
- 火灾领域专家目标不低于 80，且专家—代表模型差距建议至少 20；专家也低于 70 时优先判定任务不清晰或证据不足。
- 任何任务不能靠极小 support 达到校准结论。推荐计分 split 每类至少 20 条、每任务至少 100 条；达不到则只做诊断。
- 难度调整只允许在开发挑战集上完成；正式测试 gold 解盲后禁止再次改题或改阈值。

## 7. 合法增难方式

- 同场景、近外观、物理不同的 hard negatives。
- 多字段联合精确匹配，同时保留组件诊断，避免只靠一个容易字段得高分。
- 多时距、多变量和首次越阈联合预测。
- event_group 级 Geometry/Condition/View-Sensor OOD。
- 成对反事实与 A/B 交换一致性。
- 类别、时距、违规位置、候选位置和模板风格平衡。
- 对路径、文件名、数值精度、选项长度、时间位置和生成模板进行 shortcut audit。

禁止通过模糊问题、不可观测 gold、随机噪声、错误标签、秘密改变答案空间或分数非线性缩放来压低模型分数。

## 8. 工程影响

本文件是设计草案，不直接改变 FDS Core v3.3.1。实施新协议前必须：

1. 新建版本化 QA/prediction schema；不得覆盖 v3.3.1 schema 或 gold。
2. 冻结新增 metadata：horizon、difficulty、first-violation、risk-driver、time-bin、pairing。
3. 实现新 semantic validators、主/诊断 scorer 和 deterministic rerun tests。
4. 从现有 FDS 轨迹构建独立的 challenge candidate package，并通过可回答性与 support 验收。
5. 先跑基线与少量 smoke；难度校准通过后才能进行多模型 pilot。
6. 旧 gpt-4o-mini 与 baseline 分数标记为 `legacy_protocol_calibration_evidence`，不得与新协议直接排名。

## 9. 当前结论

新协议保留 FireWorldBench 的核心研究目标，但不再依赖“所有任务统一 Accuracy/组件均值”。
它把任务难点放在动态因果辨别、违规定位、联合状态恢复、多时距演化和反事实效应分解上；
同时以 support、专家上限、强/弱基线差距和严格覆盖率判断任务质量。正式实验保持暂停，直到
schema、metadata、challenge subset 和 scorer 全部版本化并验收。
