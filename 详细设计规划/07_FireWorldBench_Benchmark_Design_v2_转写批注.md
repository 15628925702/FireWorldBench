# FireWorldBench Benchmark 设计方案 v2 转写与修改批注

## 转写说明

- 原始文件：`../开发要求约束/FireWorldBench_Benchmark_Design_v2.pdf`
- 原始 PDF 页数：9
- 原始 PDF SHA-256：`16b4caec881825b8a8d41556a5abe6a428ae77944c98c45e56789add54c8d7ce`
- 转写原则：保留原始章节、表格、示例、术语和参考资料；只规范 PDF 换行和 Markdown 表格格式。
- 批注规则：<span style="color:#d00000">红色文字是原方案中建议修改或收缩的表述</span>（紧随其后的括号给出修改原因和方向）。未标红部分不代表已经完成实验验证，只表示无需因本轮核心 idea 审查而改写。
- 本文件是带批注的历史转写，不替代原始 PDF；新版执行方案见 `08_FireWorldBench_ICLR2027_核心方案_v3.md`。

---

# FireWorldBench

## 火灾物理世界理解 Benchmark 设计方案

面向 LLM / multimodal agent 的火灾预警、火灾识别与火灾演化理解

核心定位：本 benchmark 不把火灾场景简化为“图像中是否有火”或“传感器是否超过阈值”。它要评估模型是否能从多模态证据背后<span style="color:#d00000">恢复一个受火灾动力学约束的世界模型</span>（建议改为“在部分可观测火灾动力系统中完成隐藏状态推断、动力学预测和受控干预推理”。当前 benchmark 评测的是可观测行为，不能直接证明模型内部形成了世界模型）：火源、热释放、热羽流、顶棚射流、烟层、通风、能见度、毒性与干预措施之间如何相互作用。

资料核对日期：2026-06-27。本文档用于研究 benchmark 设计，不应用作实际消防系统决策依据。

## 1. 总体设计

建议将 FireWorldBench 设计为三大任务：火灾预警、火灾识别、火灾演化。三者分别对应火灾系统的早期弱信号、当前隐状态、未来状态转移。这样既符合火灾工程中的关键需求，也能凸显 LLM/agent 相比普通视觉分类器或时序预测器的能力差异。

<span style="color:#d00000">三大任务目前主要按应用阶段并列描述</span>（建议增加统一形式化：隐藏状态 `s_t`、历史观测 `o_<=t`、干预 `do(a)` 和可查询观测 `q`。T1/T2/T3 应由同一个部分可观测动力系统导出，而不是三个独立 QA 集）。

| 任务 | 核心问题 | 要测的“物理世界理解” | 首选数据源 |
|---|---|---|---|
| T1 火灾预警 | 火灾是否正在形成，是否需要提前报警？ | 弱信号归因、噪声/通风扰动区分、早期风险判断、缺失信息意识。 | Immersed Tunnel CFD；PolyUFire sidewall vent；FDS/FD-Gen 扩展；D-Fire/DetectiumFire 视觉辅助。 |
| T2 火灾识别 | 当前火灾处于什么状态，主导机制是什么？ | 火源、火灾阶段、通风机制、烟层与回流状态识别，而非单纯 fire/smoke detection。 | Immersed Tunnel；PolyUFire 经验表；FDS validation/exp；D-Fire/DFS/DetectiumFire/Fire360。 |
| T3 火灾演化 | 未来烟气、温度、能见度、风险如何变化？干预后会怎样？ | 状态转移、反事实、干预推理、物理一致性与证据链。 | FDS + FD-Gen 为主；Immersed Tunnel 排烟配置 pairs；PolyUFire 真实温度测试做外部验证。 |

设计原则：每个任务都应同时给出最终答案、关键物理机制、证据来源和置信度。只给分类标签的样本可以保留作 baseline，但不应作为 benchmark 的核心。

<span style="color:#d00000">每个任务分别给出答案、机制、证据和置信度</span>（建议进一步统一为同一个结构化物理状态图，并增加同一 case 在 T1/T2/T3 间的跨任务一致性；否则九个子任务仍可能形成彼此独立的输出模板）。

## 2. 可用数据源与角色分工

| 数据源 | 公开内容 | 最适合支撑的任务 | 不足与处理建议 |
|---|---|---|---|
| Immersed-Tunnel-Fire-Location-Detection-Data<br>https://github.com/zhang-zhen-project/immersed-tunnel-fire-location-detection-data | 超宽沉管隧道 FDS/CFD 数据；6 个火源位置、32 种排烟配置、192 个计算结果；CSV 与读取/建模代码。 | T1 预警：早期传感器窗口；T2 识别：火源位置与排烟配置；<span style="color:#d00000">T3 演化：同火源不同排烟策略的反事实 pair</span>（只有参数差分证明除声明干预外其余条件相同，且比较基于干预后的有效时间窗时才能称为反事实；否则只能称配置比较）。 | 规模小，配置离散；文件名含标签，发布 benchmark 时需匿名化；缺少自然语言解释、因果链和完整多模态标注。 |
| PolyUFire Tunnel Fire Database<br>https://github.com/PolyUFire/Tunnel_Fire_Database | 2020 TUST 论文相关整理表：HRR、flame length、ceiling temperature、critical velocity、back-layering、smoke layer thickness、plug-holing 等；另有 sidewall smoke extraction 的 8 组测试温度时序。 | T1 预警：真实温度时序；T2 识别：critical velocity/back-layering 等机制标签；T3 演化：温度演化外部验证。 | 不是完整原始物理场；多为整理表和温度数据；缺少 soot、CO、visibility、velocity 场，需要与 FDS 数据结合。 |
| NIST FDS / firemodels<br>https://pages.nist.gov/fds-smv/<br>https://github.com/firemodels/fds | FDS/Smokeview 官方工具、验证案例、输入文件与实验对照。 | <span style="color:#d00000">三大任务的物理 ground truth</span>（建议区分 simulator state、deterministic derived label 和实验 measurement。FDS 输出是仿真真值，不等同于真实世界 ground truth）；尤其适合生成 T3 演化和反事实干预样本。 | 需要自行建模、运行和后处理；计算成本较高；要进行网格、边界条件和验证说明。 |
| FD-Gen<br>https://github.com/usnistgov/FD-Gen | NIST 火灾数据生成工具，可随机化 FDS 参数并批量生成场景。 | 扩展 T1/T2/T3 的场景覆盖：HRR、火源位置、通风、开口、障碍物、传感器布置等。 | 需制定参数空间和合理性过滤规则；输出仍需转换成 QA、trace 和 counterfactual 标注。 |
| DetectiumFire<br>https://arxiv.org/abs/2511.02495 | 多模态火灾安全数据，包含图像、视频、bbox、caption、risk level 等。 | T1/T2 的视觉预警与场景识别；可用于训练/评测视觉 grounding。 | 偏视觉与风险描述，不含完整物理场和干预反事实。 |
| D-Fire<br>https://github.com/gaia-solutions-on-demand/DFireDataset | 21k+ 火/烟图像，YOLO bbox，含 fire、smoke、fire+smoke、none。 | T1/T2 的视觉 baseline：火/烟检测、误报干扰。 | 静态图像，不能单独支撑火灾物理演化理解。 |
| Fire360<br>https://arxiv.org/abs/2506.02167 | 228 个 360 度消防训练视频，低能见度/热变形等条件，含 VQA、action captioning、object localization、safety reasoning 等任务。 | T2 视觉场景识别与安全推理；可补充 degraded perception 场景。 | 偏消防员视角和感知记忆，不是隧道/建筑火灾 CFD ground truth。 |

<span style="color:#d00000">视觉、传感器和仿真来源在同一表中被统称为多模态来源</span>（建议明确“多源评测”与“同 case 多模态融合”的区别。只有时间、空间和 case 对齐的观测才能构成多模态样本；D-Fire、Fire360 等不对齐来源应作为辅助/OOD track）。

## 3. 任务一：火灾预警 Fire Early Warning

目标不是检测“是否已经看到明火”，而是评估 agent 是否能在弱信号阶段判断火灾正在形成，并区分真实火灾、传感器噪声、通风扰动和非火灾烟雾。

### 3.1 子任务设计

| 子任务 | 输入 | 输出 | 物理理解点 |
|---|---|---|---|
| T1-A 早期火灾判别 | 短窗口传感器：temperature、soot、CO、风速；可选图像/视频帧；隧道/房间布局。 | 是否预警、风险等级、预警时间、置信度。 | 弱信号是否形成火灾一致模式；是否理解烟气/温度/CO 的时序关系。 |
| T1-B 异常归因 | 同上，并提供可能干扰：风机切换、传感器漂移、热源非火灾扰动。 | fire / non-fire / ventilation disturbance / sensor fault 分类，并说明证据。 | 区分生成机制，而非只看数值变大。 |
| T1-C 信息需求选择 | 给定不完整观测和若干可查询传感器/图像/曲线。 | <span style="color:#d00000">选择下一步最应查看的信息，并说明为什么</span>（建议改为有多个候选、不同成本和允许停止的序贯决策；以真实 value of information 或风险降低计分。固定“有下一观测就查询”只测指令遵循）。 | agent 是否知道哪些变量最能区分假设，如通风方向、上游 soot、顶棚温度。 |

### 3.2 示例样本

给定：S16 的 soot 在 12 秒开始上升，T12 在 18 秒后升高，T08 基本不变；纵向风向为上游到下游。问题：这更像火灾早期、通风扰动还是传感器故障？请给出预警等级、证据传感器和还需要查看的信息。

<span style="color:#d00000">示例只给一个自然语言问题，没有明确可见观测、隐藏状态和不可见 gold 的边界</span>（建议同一 case 生成不同观测预算版本，并确保判定阈值和派生规则不出现在被测模型 prompt 中）。

### 3.3 数据集匹配

首选 Immersed Tunnel CFD：可截取 3s/6s/10s/20s 早期窗口，生成“是否应预警、火源区间、受影响区域”的标签。PolyUFire sidewall vent 可作为真实温度时序补充，但变量较少。D-Fire/DetectiumFire/Fire360 可提供视觉预警和火烟误报场景。若要高质量 non-fire 与弱火源样本，应使用 FDS/FD-Gen 生成低 HRR、通风扰动、传感器噪声和无火热源场景。

<span style="color:#d00000">固定 3s/6s/10s/20s 窗口</span>（建议同时引入相对事件时间和多档信息预算。固定绝对秒数可能把不同 case 的物理阶段混在一起，也不足以形成可解释的难度曲线）。

### 3.4 推荐指标

包括 AUROC、AUPRC、提前量 lead time、false alarm rate、miss rate、risk calibration、evidence alignment，以及物理解释违规率。对于 LLM/agent，需额外评分：是否正确指出主导机制、是否识别信息不足、是否选择有效补充观测。

## 4. 任务二：火灾识别 Fire State Recognition

火灾识别不应只做 fire/smoke object detection，而应识别“当前火灾状态”：火源位置或区域、火灾阶段、火势强度、主导输运机制、烟层/回流状态、通风影响和风险区域。

### 4.1 子任务设计

| 子任务 | 输入 | 输出 | 物理理解点 |
|---|---|---|---|
| T2-A 火灾状态识别 | 图像/视频、传感器、布局、通风状态。 | 火灾阶段、火源区域、HRR 档位、风险区域。 | 从可观测现象推断不可直接观测的隐状态。 |
| T2-B 主导机制识别 | 同一场景的观测证据和候选机制。 | buoyant plume / ceiling jet / longitudinal ventilation / sidewall extraction / backlayering 等机制。 | 区分“看到了烟”与“理解烟为什么这样走”。 |
| T2-C 物理一致性判断 | 给出一段解释或模型回答。 | 判断是否物理合理，并指出错误机制。 | 检验热浮力、烟层、质量/能量守恒、通风方向等约束。 |

<span style="color:#d00000">T2-B 在机制不可由当前观测识别时仍被设计为机制分类</span>（建议把“可识别性”作为 gold 属性；只有存在区分证据时进入机制主任务，否则正确输出应为 underdetermined，并避免该类占据绝大多数样本）。

<span style="color:#d00000">T2-C 与 T3-C 都承担解释/物理链评测</span>（建议 T2-C 收缩为 held-out physical violation 诊断集；完整状态转移图统一在跨任务结构化输出中评分，减少任务重复）。

### 4.2 示例样本

解释待判定：“高温烟气密度较大，因此火灾初期会优先贴地向上游扩散。”期望回答：不合理。高温烟气通常密度较低，先由浮力上升形成火羽流，撞击顶棚后形成顶棚射流和烟层；上游回流需要结合通风速度与 critical velocity 判断。

### 4.3 数据集匹配

Immersed Tunnel 适合做火源位置、排烟配置和受影响区域识别。PolyUFire 的 critical velocity、back-layering length、smoke layer thickness、plug-holing 等整理表适合生成机制识别与物理一致性题。D-Fire、DFS、DetectiumFire 和 Fire360 适合视觉火/烟与安全场景识别，但需要补充机制标签。FDS validation/exp 可作为标准物理机制案例库。

### 4.4 推荐指标

包括 state accuracy、macro-F1、mechanism F1、physical consistency accuracy、explanation violation rate、evidence sensor precision/recall。对生成式回答，建议把输出结构化为 JSON：answer、mechanism、evidence、uncertainty、violations。

## 5. 任务三：火灾演化 Fire Evolution Reasoning

这是最能体现火灾物理世界理解的任务。模型需要预测未来状态或比较干预后果，而不是只读当前图像或当前曲线。核心是状态转移、反事实和物理约束。

<span style="color:#d00000">“最能体现物理世界理解”</span>（建议改为“为动力学预测和干预一致性提供可证伪证据”。任何单一任务分数都不能直接证明模型具有物理世界理解）。

### 5.1 子任务设计

| 子任务 | 输入 | 输出 | 物理理解点 |
|---|---|---|---|
| T3-A 未来趋势预测 | 当前观测窗口、空间布局、通风状态。 | 未来 30/60/120 秒温度、soot、CO、能见度、风险区域的方向性变化或区间。 | 是否理解烟气随通风和浮力演化。 |
| T3-B 反事实干预推理 | Case A 与 Case B，仅改变一个变量：风速、风阀、火源位置、HRR、障碍物。 | 哪个区域风险上升/下降；传感器响应顺序如何变化；是否更可能 backlayering。 | 区分相关性和因果性，是 benchmark 的核心样本类型。 |
| T3-C 状态转移追踪 | 多模态证据 + 问题。 | initial_state、dominant_mechanism、transition steps、outcome、evidence。 | 答案对不够，必须中间物理链也对。 |

<span style="color:#d00000">T3-C 使用自由文本 transition steps 或空 trace 也可能被形式评分接受</span>（建议改成类型化状态图：节点、边、方向、时序、证据引用和约束均可机器核验；空图不得获得完整 trace 分数）。

### 5.2 示例样本

Case A：下游排烟阀开启；Case B：下游排烟阀关闭；其他条件相同。问题：哪个 case 更可能导致下游能见度快速下降？上游 backlayering 风险如何变化？请给出因果链和证据变量。

### 5.3 数据集匹配

FDS + FD-Gen 是首选，因为演化和反事实需要可控变量和完整 ground truth。Immersed Tunnel 数据天然包含同一火源下不同排烟配置，<span style="color:#d00000">可构造干预 pair</span>（应先验证输入配置差分和共同初始状态；如果多个条件共同变化，只能构造配置比较）。PolyUFire sidewall vent 提供真实温度演化，可用于验证模型是否能迁移到实验数据。Fire360/DetectiumFire 可补充真实视觉演化，但不能替代物理场 ground truth。

### 5.4 推荐指标

包括 trend direction accuracy、event time error、ranking accuracy、counterfactual consistency、state trace score、causal edge F1、physical violation rate。对于数值输出可用 MAE/RMSE，但更建议先做区间或排序题，避免 LLM 被不必要的精确数值惩罚掩盖物理推理能力。

<span style="color:#d00000">当前指标按任务分别罗列，但没有衡量同一 case 的跨阶段矛盾</span>（建议新增 cross-task consistency：T1 风险、T2 状态、T3 未来与干预结果必须在同一状态图上相容）。

## 6. 样本格式与评分协议

建议每个样本包含 scenario、observations、question、answer、physical_trace、scoring_metadata。核心是把可自动评分部分和专家审计部分分开。

| 字段 | 说明 |
|---|---|
| scenario | 隧道/房间几何、传感器坐标、火源候选位置、通风/排烟配置、障碍物。 |
| observations | 传感器时序、图像/视频帧、Smokeview 截图、风险图、已有曲线。 |
| question | 预警、识别或演化问题；可为选择、排序、开放式 JSON。 |
| answer | 最终答案：分类、排序、趋势、风险区间或干预选择。 |
| physical_trace | 标准物理链：初始状态、主导机制、状态转移、结果、关键证据。 |
| scoring_metadata | 可自动评估的事件时间、传感器响应顺序、阈值、反事实方向、因果边。 |

<span style="color:#d00000">样本缺少统一 case view 和 provenance 字段，physical_trace 仍是链式文本概念</span>（建议增加 `case_uid`、`observation_budget_id`、`intervention_id`、`source/gold_origin` 和类型化 `physical_state_graph`；同一 case 的 T1/T2/T3 视图通过稳定 ID 关联）。

推荐输出模板：

```json
{
  "answer": "...",
  "risk_level": "...",
  "dominant_mechanism": "...",
  "causal_chain": ["..."],
  "evidence": ["..."],
  "uncertainty": "...",
  "missing_information": ["..."]
}
```

<span style="color:#d00000">`causal_chain` 是自由字符串列表</span>（建议替换为有 schema 的 `state_nodes`、`mechanism_edges`、`temporal_order`、`evidence_links` 和 `constraint_checks`，避免用语言流畅度代替物理正确性）。

## 7. 数据划分与防投机设计

| 设计点 | 建议 |
|---|---|
| 匿名化 | 文件名、case ID 不得泄漏火源位置或排烟配置。例如原始 100M32.csv 这类名称必须替换为随机 ID。 |
| OOD split | 训练/验证/测试按火源位置、通风配置、HRR、几何布局、传感器布局分层；测试中包含未见过的组合。 |
| Counterfactual pair | 同一场景只改变一个变量，要求模型预测方向性变化。 |
| Adversarial explanation | 加入物理错误解释，让模型检查热浮力、通风方向、烟层、backlayering、质量守恒等。 |
| Tool-use 限制 | agent 可调用绘图、检索、简单公式或 FDS 代理工具，但需记录调用次数和是否真正改善答案。 |
| 人类/专家上限 | 抽样邀请消防工程或火灾动力学背景人员标注，用于校准开放式解释评分。 |

<span style="color:#d00000">OOD 只作为 split 类型列出</span>（建议把观测完整度、预测 horizon、干预幅度、噪声、组合机制复杂度和 sim-to-real 统一为受控难度轴，形成能力退化曲线，而不是只报告 ID/OOD 两个点）。

<span style="color:#d00000">Tool-use 只看“是否改善答案”</span>（建议在相同信息和计算预算下比较，并分别记录工具选择、调用正确性、物理约束满足和净收益；否则工具组与 closed-book 不可解释）。

## 8. 最小可行版本 MVP

第一版不需要一次性覆盖所有火灾场景。建议以“隧道火灾 + 火/烟视觉辅助”为主，先做可发表、可复现的 MVP。

| 模块 | 具体实现 |
|---|---|
| 数据 | Immersed Tunnel CFD 作为主数据；PolyUFire sidewall vent 作为真实温度验证；<span style="color:#d00000">D-Fire 或 DetectiumFire 作为视觉识别辅助</span>（建议主论文聚焦封闭/隧道火灾动力学。未与同一 case 对齐的视觉数据放 auxiliary track 或附录，避免削弱统一动力系统叙事）。 |
| 任务 | T1 早期预警：3/6/10/20 秒窗口；T2 状态识别：火源区域 + 主导机制；T3 演化：排烟配置反事实 pair。 |
| 标注 | <span style="color:#d00000">从 FDS CSV 自动派生：响应顺序、峰值时间、阈值超限、风险方向；人工补充机制解释模板</span>（建议自动派生只用于可验证事件；机制图需由物理规则、配置和专家审计共同形成。不要让模型在 prompt 中看到生成 gold 的阈值规则）。 |
| 基线 | 传统模型：CNN-LSTM/TCN/Transformer；LLM baseline：text-only、sensor-table QA、LLM+plotting、LLM+retrieval、LLM+tool-use。 |
| 主要卖点 | 不是新的 fire detection 数据集，而是<span style="color:#d00000">首个面向 LLM/agent 的火灾物理世界理解 benchmark：预警、识别、演化三位一体</span>（禁止使用“首个”和直接“理解”主张。建议改为“面向部分可观测火灾动力学的诊断 benchmark，统一评测状态、演化、受控干预和证据一致性”）。 |

<span style="color:#d00000">MVP 同时铺开全部九个子任务和五类 LLM track</span>（建议论文主表先保留早期状态、当前隐状态、多时距演化和受控干预四个高区分度任务；主动感知、机制诊断、视觉和工具作为条件成熟后的辅助分析）。

## 9. 参考资料

1. Immersed Tunnel Fire Location Detection Data: https://github.com/zhang-zhen-project/immersed-tunnel-fire-location-detection-data
2. Zhang et al., Intelligent fire location detection approach for extrawide immersed tunnels, Expert Systems with Applications, 2024: https://doi.org/10.1016/j.eswa.2023.122251
3. PolyUFire Tunnel Fire Database: https://github.com/PolyUFire/Tunnel_Fire_Database
4. NIST FDS/Smokeview Manuals: https://pages.nist.gov/fds-smv/
5. firemodels/fds: https://github.com/firemodels/fds
6. FD-Gen: Fire Data Generator, NIST: https://github.com/usnistgov/FD-Gen
7. DetectiumFire: https://arxiv.org/abs/2511.02495
8. D-Fire Dataset: https://github.com/gaia-solutions-on-demand/DFireDataset
9. Fire360: https://arxiv.org/abs/2506.02167
10. PhysBench: https://arxiv.org/abs/2501.16411
11. CausalPhys: https://arxiv.org/abs/2606.05966
12. QuantiPhy: https://arxiv.org/abs/2512.19526
13. World Models in Words: https://arxiv.org/abs/2605.29585

<span style="color:#d00000">当前相关工作列表不足以证明新版贡献边界</span>（建议补充 CLEVRER、PHYRE、I-PHYRE、Physion、What-If World、PhysicsMind、TimeSeriesExamAgent、HiTSR 和 LLMPhy，并用“部分可观测、连续时序、结构化机制图、干预、主动感知、sim-to-real”统一比较）。

## 附注

现有公开数据并不能直接完成完整 FireWorldBench。真正的 benchmark 贡献在于把公开火灾/隧道/CFD 数据组织成带有反事实、因果链、状态转移和物理一致性评分的任务集合。

<span style="color:#d00000">“任务集合”仍可能被理解为数据集拼盘</span>（建议改为“同一部分可观测动力系统上的多视图诊断协议”，并以同一 case 跨 T1/T2/T3 的一致性、单变量干预和 sim-to-real 作为统一主线）。
