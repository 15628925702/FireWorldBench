# Nine-Task Protocol

版本：`2.0.0-dev`。固定定义来自核心 PDF；标为 `TBD-PILOT` 或 `TBD-EXPERT` 的数值不能在验证前擅自填写。

## L1-1 Early Signal Attribution

- 输入：S 为 3/6/10/20 秒温度、soot、CO、风速窗口；I 为早期单帧或关键帧；V 为 4-8 秒片段。视觉轨只给视觉和时间。
- 输出：`class` = `fire/no_fire/ventilation_disturbance/sensor_fault`，附 0-1 confidence。
- 标签：FDS 无火基线、低 HRR、无火通风切换；传感器故障由版本化 drift/stuck/spike 注入规则生成。
- 候选/负例：四类平衡；视觉负例匹配背景和亮度。D-Fire 仅映射 fire/smoke/none OOD，不伪造传感器故障或通风标签。
- 主评分：Accuracy。补充 Macro-F1、ECE、Brier Score；按 3/6/10/20 秒分别报告。

## L1-2 Next-State Selection

- 输入：当前观测、预测间隔 `delta_t` 和四候选。S 为数值窗口 + 未来摘要；I 为 2-3 前序帧 + 4 候选帧；V 为当前短片 + 4 候选短片。
- 输出：`choice` = A/B/C/D。
- 标签：正例来自同一 event 的 `t+delta_t`。
- 候选：同几何、视角、时间跨度；困难负例来自相近烟量但不同通风/火源，或同一 event 的过去/过远未来。禁止随机异背景。
- 主评分：Accuracy；按 `delta_t` 和难度报告；chance = 25%。正确位置全局差异不超过 2%。

## L1-3 Temporal Coherence Verification

- 输入：S 时间表；I 为 2-4 张带时间戳帧；V 为 4-12 秒片段。
- 输出：`consistency` = `consistent/inconsistent`；不一致时 `violation_type` = `reverse/jump/disappearance/direction_flip/sensor_conflict`。
- 标签/负例：原始连续序列为正；交换相邻片段、局部倒放、同场景拼接、替换通道生成负例，比例固定 50%。
- 主评分：Consistency Accuracy；补充 Violation-type Accuracy。Fire360 只做时间扰动 OOD，不给复杂物理标签。

## L2-1 Source and Stage Recovery

- 输入：当前窗口与统一 8 区域布局；S/I/V 均可。
- 输出：`source_region` = R1..R8；`stage` = `incipient/growth/developed/decay`。
- 标签：source 由场景配置；stage 由 HRR 曲线和变化率规则。阶段边界设置 `TBD-EXPERT` 缓冲区，边界样本进入 ambiguous。
- 候选：结构化输出可不设 options；若用有限候选，必须覆盖合法 region/stage 且不改变评分。
- 主评分：`(Source Accuracy + Stage Accuracy)/2`；补充 Joint Exact Match。

## L2-2 Current Risk Region Recovery

- 输入：当前观测与 8 区域布局；S/I/V 均可。
- 输出：`risk_region` = R1..R8；`risk_level` = `low/moderate/high/critical`。
- 标签：FDS 区域温度、能见度、CO/soot 通过冻结规则聚合。最高两区差小于 `TBD-EXPERT` 时排除或进入 multi-risk 扩展集。
- 外部限制：PolyUFire 只发布温度风险子轨；真实视觉不进入核心评分。
- 主评分：`(Region Accuracy + Risk-level Accuracy)/2`；若发布 mask，补充 IoU。

## L2-3 Dominant Mechanism Recognition

- 输入：观测窗口与可见的通风/排烟条件或布局；S/I/V 均可。
- 输出：`mechanism` = `buoyant_plume/ceiling_jet/smoke_layer/longitudinal_ventilation/backlayering/extraction_dominated`。
- 标签：由火源高度、速度方向、烟层位置、临界速度关系和排烟流量确定性派生，只保留主导机制明确样本；至少 10% 由火灾工程背景人员复核。
- 外部限制：PolyUFire 只验证 critical velocity、backlayering、sidewall extraction 等实际机制。
- 主评分：Accuracy；补充 Macro-F1。

## L3-1 Future Trend Prediction

- 输入：当前窗口、目标区域、10/30/60 秒预测时长。S/V 为核心；I 仅用 2-4 张前序帧。
- 输出：`temperature_trend/smoke_trend/visibility_trend`，各为 `up/stable/down`。
- 标签：比较当前末段与未来末段的区域稳健统计，使用训练/pilot 冻结的 dead-band；未来缺失或边界样本删除。
- 主评分：三个变量 Accuracy 的均值，同时报告各变量 Accuracy。

## L3-2 Future Risk Region Prediction

- 输入：当前观测、8 区域布局、预测窗口。S/V 为核心；I 仅在关键帧有足够动态信息时发布。
- 输出：`first_high_risk_region` = R1..R8/none。
- 标签：未来轨迹中各区首次超过高风险阈值的时间；最早区为标签。时间差小于 `TBD-EXPERT` 容差时进入 multi-region 扩展集。
- 主评分：9 类 Accuracy；补充 Event-time MAE。

## L3-3 Counterfactual Comparison

- 输入：A/B 配对当前观测和唯一差异，问题指定比较量；S/I/V 均可。
- 输出：`comparison` = `A/B/same`。
- 标签：从同一基础 event 复制并只改变一个参数；几何、camera、随机种子、采样和其他条件相同。未来轨迹直接比较，差异小于 `TBD-PILOT` 阈值时排除。
- 候选：A/B 顺序随机化并记录映射；不得通过描述长度或变量命名泄漏方向。
- 主评分：Accuracy；补充 Counterfactual Consistency。

## Task/Track Publication Gate

任务表允许的轨道只定义上限。builder 必须逐 source/task/track 证明：输入包含足够区分信息、标签来自真实字段或可靠规则、负例可区分、样本通过 shortcut audit。任一条件失败则不发布该组合，并在 coverage report 中计为 unsupported，而不是补造标签。
