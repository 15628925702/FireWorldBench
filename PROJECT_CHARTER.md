# FireWorldBench 项目章程

状态：`V2-ARCHITECTURE-FREEZE`
版本：`2.0.0-dev`
生效日期：`2026-07-17`

## 1. 权威与替代关系

唯一核心方案为 `G:/0-newResearch/2/2.方案研究/FireWorldBenchv2(1).pdf`。本章程替代 2026-07-14 的 v1 章程。旧 T1/T2/T3 定义、融合方案、任务收缩、复杂方法设计及既有正式/准实验状态全部降级为历史资料；复用任何旧代码前必须证明其符合本章程和新 Schema。

## 2. 研究定位

FireWorldBench 评估多模态基础模型能否从部分、有限且不同形式的火灾观测中，依次完成：

1. L1 Dynamic Perception：动态感知；
2. L2 State Recovery：当前状态恢复；
3. L3 Evolution Reasoning：未来演化推理。

项目是 simulation-grounded fire world understanding benchmark，不是火烟检测数据集，不声称模型求解完整 PDE，也不要求模型读取完整四维 CFD 场。

## 3. 固定任务和输入轨道

固定九任务：`L1-1` 早期信号归因、`L1-2` 下一状态选择、`L1-3` 时间一致性验证、`L2-1` 火源与阶段恢复、`L2-2` 当前风险区域恢复、`L2-3` 主导机制识别、`L3-1` 未来趋势预测、`L3-2` 未来风险区域预测、`L3-3` 反事实条件比较。

固定三轨：`S` 为文字/数值表/传感器时序或曲线摘要；`I` 为单图或 2-4 张有序关键帧；`V` 为 4-12 秒单段视频。任务不因形式完整而强制支持所有轨道。

## 4. 数据角色

- FDS / Smokeview / FD-Gen：核心主数据、隐藏物理真值、S/I/V 派生和反事实配对；进入主榜。
- Immersed Tunnel CFD：外部 CFD 数值验证；单独报告 `External-CFD`。
- PolyUFire Tunnel Database：实验桥接；只评价实际存在的温度趋势、critical velocity、backlayering 等量；单独报告 `Experiment`。
- D-Fire：真实图像 OOD；仅视觉存在、误报和有限风险感知；单独报告 `Real-Image OOD`。
- Fire360：真实视频 OOD；仅可靠视觉动态和退化场景；单独报告 `Real-Video OOD`。
- DetectiumFire：可选视觉补充；受访问、许可和实际标签约束。

所有来源先转换为统一 Fire Event；禁止把原始文件随机混合后划分。

## 5. 规模与阶段门禁

正式目标约 180 个独立 FDS Fire Events，派生约 4,000-6,000 条 QA。第一交付是 20-event pilot，覆盖 `L1-2`、`L2-1`、`L3-3`、至少两个输入轨道、困难负例、自动标签、事件级 split、Schema 验证、简单 baseline，以及成本/存储/标签稳定性报告。pilot 未通过不得扩展。

## 6. 评分与报告

- 九任务以 Accuracy、Component Accuracy 或 Mean Accuracy 为主；按任务补充 Macro-F1、Joint Exact Match、IoU、Event-time MAE、ECE、Brier Score、Evidence Accuracy。
- `L1/L2/L3` 分别为层内三任务宏平均；`Overall` 为九任务宏平均。
- 只有任务定义和答案空间可比的正式轨道进入 Overall；外部 CFD、实验和真实视觉 OOD 单报。
- 开放解释只作次要分析，不用不稳定 LLM Judge 形成主榜。

## 7. 成功标准

- 九任务的输入、输出、标签、候选构造和评分规则全部冻结并可机检。
- 100% Fire Event 和 QA 通过 Schema，缺失模态显式为空。
- `event_group` 跨 split 泄漏为 0，公开文件和元数据标签泄漏为 0。
- 四选一正确位置差异不超过 2%，随机基线接近 25%。
- 困难负例抽检至少 90% 为视觉相近但物理可区分；正式测试歧义率低于 2%。
- 所有来源、许可、引用、版本、FDS 配置和派生链可追溯；评分可复现。

## 8. 非目标

不构建实际消防决策系统、完整四维重建系统、交互式 Agent、多轮探索、复杂大型新架构、危险真实火灾实验或九任务之外的扩展。FireState Card 仅用于 benchmark 失败模式的轻量验证。
