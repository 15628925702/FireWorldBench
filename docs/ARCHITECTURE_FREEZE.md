# FireWorldBench v2 Architecture Freeze

状态：`FROZEN-FOR-PILOT`
版本：`2.0.0-dev`
依据：`G:/0-newResearch/2/2.方案研究/FireWorldBenchv2(1).pdf`
日期：`2026-07-17`

## 1. 不可变决策

1. 能力顺序固定为 L1 Dynamic Perception -> L2 State Recovery -> L3 Evolution Reasoning。
2. 任务固定为 `L1-1` 至 `L3-3`，不得增加、删除、合并或以旧 T1/T2/T3 替换。
3. 输入轨道固定为 S/I/V。S 最多 20-40 行规范化文字/表格/曲线摘要；I 是 1 张图或 2-4 张有序关键帧；V 是 4-12 秒单段短视频。
4. 所有来源先转换为 Fire Event，再生成 QA。`event_group` 是 split 的原子单位。
5. FDS/Smokeview/FD-Gen 是主榜核心；外部 CFD、实验、真实视觉 OOD 分域报告。
6. 主答案为固定标签、区域编号、趋势类别或有限候选；开放解释不进入主排行榜。
7. 先完成 20-event pilot，再扩展到九任务和约 180 events。
8. FireState Card 只由确定性脚本提取，不作为额外任务或复杂方法。

## 2. Task Ontology

| Layer | Task | Fixed output | Primary |
|---|---|---|---|
| L1 | L1-1 Early Signal Attribution | `fire/no_fire/ventilation_disturbance/sensor_fault` | Accuracy |
| L1 | L1-2 Next-State Selection | `A/B/C/D` | Accuracy |
| L1 | L1-3 Temporal Coherence Verification | consistency + optional violation type | Accuracy |
| L2 | L2-1 Source and Stage Recovery | `R1..R8` + 4-stage label | Component Accuracy |
| L2 | L2-2 Current Risk Region Recovery | `R1..R8` + risk level | Component Accuracy |
| L2 | L2-3 Dominant Mechanism Recognition | one of six mechanisms | Accuracy |
| L3 | L3-1 Future Trend Prediction | temperature/smoke/visibility trends | Mean Accuracy |
| L3 | L3-2 Future Risk Region Prediction | `R1..R8/none` | Accuracy |
| L3 | L3-3 Counterfactual Comparison | `A/B/same` | Accuracy |

完整答案空间、候选构造和评分见 `TASK_PROTOCOL.md`。

## 3. Fire Event Contract

Fire Event 表示一个独立物理事件，而非一个时间切片。机器定义见 `schemas/fire_event.schema.json`。

必备语义：

- `event_id`：无标签语义的随机公开 ID。
- `event_group`：同一基础事件的切片、模态、增强和反事实版本的分组 ID。
- `source_domain`：来源域；禁止用原始文件随机混合替代。
- `geometry`：场景、坐标系、尺寸和最多 8 个稳定区域。
- `controls`：来源确实存在的火源、HRR、通风、排烟、开口和随机种子；真实视觉可为 `null`。
- `timeline`：事件起止与规范采样信息。
- `observations`：`structured`、`images`、`video` 三字段始终存在；缺失显式 `null`。
- `ground_truth`：仅保存来源直接存在或可可靠派生的标签，并逐字段记录 origin。
- `provenance`：源文件引用、版本、哈希、转换版本，以及 FDS 的软件/网格/边界/seed/log。
- `license`：许可证据、引用、用途和再发布范围。

不得把同一 FDS run 的 20 个相邻窗口登记为 20 个独立 events。反事实 A/B 可以是两个 event，但必须共享 `event_group` 并记录唯一干预轴。

## 4. QA Contract

机器定义见 `schemas/qa.schema.json`。每条 QA 必须包含：

- `qa_id/case_id/event_id/event_group/source_domain/split`；
- `layer/task_id/track`；
- 单轨 `observation`，未使用模态显式为 `null`；
- `question/options/answer`；
- `scoring` 主指标及组件；
- `confidence_target/evidence_metadata/provenance/quality`。

测试发布时私有 answer 与公开输入物理分离。QA 数量不能代替独立 event 数量。

## 5. Track Eligibility

- 任务表允许 S/I/V，不代表任何来源自动获得三轨资格。
- I 关键帧必须按时间顺序、时间标签统一；不得称为视频。
- V 只能引用一个固定帧率/分辨率的视频文件，不叠加多视角或其他视觉模态。
- L3-1/L3-2 的 V 只在视频含足够前序动态时发布；I 只在 2-4 张前序关键帧足够时发布。
- D-Fire 不支持机制、趋势或反事实；Fire360 不支持精确 HRR、CO、未来场或无证据的火源真值。

## 6. Splits

先按 `event_group` 划分，再在 split 内切片和派生 QA。

| Partition | Rule |
|---|---|
| `train` / `dev` | 可发布；不得包含 external/real OOD |
| `test_iid` | 几何和参数范围见过，但事件、seed、切片未见 |
| `test_ood_geometry` | 至少一个几何仅在测试出现 |
| `test_ood_condition` | 未见 HRR x ventilation 组合 |
| `test_ood_view_sensor` | 未见相机或传感器布局 |
| `external_cfd` | Immersed Tunnel，仅独立测试 |
| `experiment` | PolyUFire，仅独立测试 |
| `real_image_ood` | D-Fire/合格 Detectium 图像 |
| `real_video_ood` | Fire360/合格 Detectium 视频 |

同一 `event_group` 在所有 manifest 中只能有一个 partition。外部域不得参与主数据训练或 Overall。

## 7. Metrics and Leaderboard

每个 task 先在可比正式轨道上计算 task score，范围 0-100：

```text
L1 = mean(L1-1, L1-2, L1-3)
L2 = mean(L2-1, L2-2, L2-3)
L3 = mean(L3-1, L3-2, L3-3)
Overall = mean(all 9 task scores)
```

Component Accuracy 是组件准确率算术平均；L3-1 Mean Accuracy 是三个趋势变量准确率算术平均。补充指标按任务报告 Macro-F1、Joint Exact Match、IoU、Event-time MAE、ECE、Brier Score、Evidence Accuracy。不能用来源样本量加权掩盖任务差异，不能把 External-CFD、Experiment、Real-Visual OOD 强行平均进 Overall。

## 8. Quality Control

发布门禁：

- `event_group` 跨 split 交集为 0；精确/感知重复、视频邻帧和反事实 family 不跨 split。
- 随机公开 ID；路径、文件名、EXIF、配置编码和上下文不泄漏答案。
- A/B/C/D 位置全局差异不超过 2%；文本长度/风格匹配。
- NSS 困难负例匹配几何、视角、时间跨度、背景、亮度和总体烟量，并保留物理可区分证据。
- 标签间窗口长度和时间位置匹配；防止“越晚越危险”捷径。
- 多区近似并列、阶段边界、未来窗口缺失或差异小于容差的样本进入 `ambiguous`，不进入正式测试。
- FDS 未收敛、异常数值或渲染错误事件不计分，但失败 run 仍保留在运行清单。
- 困难样本执行两名非作者标注者和一名领域审核者检查；专家尚未到位时不得伪造通过状态。

## 9. Pilot Scope

20 个独立 FDS events，至少覆盖有火、无火/扰动、不同几何/火源/HRR/通风条件；实现 `L1-2/L2-1/L3-3`，至少两个轨道。pilot 报告必须给出 event、QA、task、track、source、split 六种计数，以及 CPU 时间、内存、存储、FDS 失败率、标签边界率和困难负例通过率。
