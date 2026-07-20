# FireWorldBench Benchmark Design v2 (PDF text transcription)

> Generated from PDF text layer.

---

FireWorldBench
火灾物理世界理解 Benchmark 设计方案
面向 LLM / multimodal agent 的火灾预警、火灾识别与火灾演化理解
核心定位：本 benchmark 不把火灾场景简化为“图像中是否有火”或“传感器是否超过阈值”。它要评估模型是否能从多模态
证据背后恢复一个受火灾动力学约束的世界模型：火源、热释放、热羽流、顶棚射流、烟层、通风、能见度、毒性与干预措施之
间如何相互作用。
资料核对日期：2026-06-27。本文档用于研究 benchmark 设计，不应用作实际消防系统决策依据。

1. 总体设计
建议将 FireWorldBench 设计为三大任务：火灾预警、火灾识别、火灾演化。三者分别对应火灾系统的早期弱信号、当前隐状态、未来状态
转移。这样既符合火灾工程中的关键需求，也能凸显 LLM/agent 相比普通视觉分类器或时序预测器的能力差异。
任务 核心问题 要测的“物理世界理解” 首选数据源
T1 火灾预警 火灾是否正在形成，是否需要
提前报警？
弱信号归因、噪声/通风扰动区分、早期风险
判断、缺失信息意识。
Immersed Tunnel CFD；
PolyUFire sidewall vent；
FDS/FD-Gen 扩展；D-
Fire/DetectiumFire 视觉辅
助。
T2 火灾识别 当前火灾处于什么状态，主导
机制是什么？
火源、火灾阶段、通风机制、烟层与回流状
态识别，而非单纯 fire/smoke detection。
Immersed Tunnel；PolyUFire
经验表；FDS
validation/exp；D-
Fire/DFS/DetectiumFire/Fire3
60。
T3 火灾演化 未来烟气、温度、能见度、风
险如何变化？干预后会怎样？
状态转移、反事实、干预推理、物理一致性
与证据链。
FDS + FD-Gen 为主；
Immersed Tunnel 排烟配置
pairs；PolyUFire 真实温度测
试做外部验证。
设计原则：每个任务都应同时给出最终答案、关键物理机制、证据来源和置信度。只给分类标签的样本可以保留作 baseline，但不应作为
benchmark 的核心。

2. 可用数据源与角色分工
数据源 公开内容 最适合支撑的任务 不足与处理建议
Immersed-Tunnel-Fire-
Location-Detection-Data
https://github.com/zhan
g-zhen-
project/immersed-
tunnel-fire-location-
detection-data
超宽沉管隧道 FDS/CFD 数据；6
个火源位置、32 种排烟配置、192
个计算结果；CSV 与读取/建模代
码。
T1 预警：早期传感器窗口；
T2 识别：火源位置与排烟配
置；T3 演化：同火源不同排
烟策略的反事实 pair。
规模小，配置离散；文件名含标
签，发布 benchmark 时需匿名
化；缺少自然语言解释、因果链和
完整多模态标注。
PolyUFire Tunnel Fire
Database
https://github.com/PolyU
Fire/Tunnel_Fire_Databas
e
2020 TUST 论文相关整理表：
HRR、flame length、ceiling
temperature、critical velocity、
back-layering、smoke layer
thickness、plug-holing 等；另有
sidewall smoke extraction 的 8
组测试温度时序。
T1 预警：真实温度时序；T2
识别：critical
velocity/back-layering 等机
制标签；T3 演化：温度演化
外部验证。
不是完整原始物理场；多为整理表
和温度数据；缺少 soot、CO、
visibility、velocity 场，需要与
FDS 数据结合。
NIST FDS / firemodels
https://pages.nist.gov/fd
s-smv/
https://github.com/firem
odels/fds
FDS/Smokeview 官方工具、验证
案例、输入文件与实验对照。
三大任务的物理 ground
truth；尤其适合生成 T3 演
化和反事实干预样本。
需要自行建模、运行和后处理；计
算成本较高；要进行网格、边界条
件和验证说明。
FD-Gen
https://github.com/usnis
tgov/FD-Gen
NIST 火灾数据生成工具，可随机化
FDS 参数并批量生成场景。
扩展 T1/T2/T3 的场景覆
盖：HRR、火源位置、通
风、开口、障碍物、传感器
布置等。
需制定参数空间和安全/合理性过
滤规则；输出仍需转换成 QA、
trace 和 counterfactual 标注。
DetectiumFire
https://arxiv.org/abs/251
1.02495
多模态火灾安全数据，包含图像、
视频、bbox、caption、risk level
等。
T1/T2 的视觉预警与场景识
别；可用于训练/评测视觉
grounding。
偏视觉与风险描述，不含完整物理
场和干预反事实。
D-Fire
https://github.com/gaia-
solutions-on-
demand/DFireDataset
21k+ 火/烟图像，YOLO bbox，含
fire、smoke、fire+smoke、
none。
T1/T2 的视觉 baseline：火/
烟检测、误报干扰。
静态图像，不能单独支撑火灾物理
演化理解。
Fire360
https://arxiv.org/abs/250
6.02167
228 个 360° 消防训练视频，低能
见度/热变形等条件，含 VQA、
action captioning、object
localization、safety reasoning 等
任务。
T2 视觉场景识别与安全推
理；可补充 degraded
perception 场景。
偏消防员视角和感知记忆，不是隧
道/建筑火灾 CFD ground
truth。

3. 任务一：火灾预警 Fire Early Warning
目标不是检测“是否已经看到明火”，而是评估 agent 是否能在弱信号阶段判断火灾正在形成，并区分真实火灾、传感器噪声、通风扰动
和非火灾烟雾。
3.1 子任务设计
子任务 输入 输出 物理理解点
T1-A 早期火灾判别短窗口传感器：temperature、
soot、CO、风速；可选图像/视频
帧；隧道/房间布局。
是否预警、风险等级、预警时
间、置信度。
弱信号是否形成火灾一致模式；是
否理解烟气/温度/CO 的时序关
系。
T1-B 异常归因 同上，并提供可能干扰：风机切换、
传感器漂移、热源非火灾扰动。
fire / non-fire / ventilation
disturbance / sensor fault
分类，并说明证据。
区分生成机制，而非只看数值变
大。
T1-C 信息需求选择给定不完整观测和若干可查询传感器/
图像/曲线。
选择下一步最应查看的信息，
并说明为什么。
agent 是否知道哪些变量最能区分
假设，如通风方向、上游 soot、顶
棚温度。
3.2 示例样本
给定：S16 的 soot 在 12 秒开始上升，T12 在 18 秒后升高，T08 基本不变；纵向风向为上游到下游。问题：这更像火灾早期、通风
扰动还是传感器故障？请给出预警等级、证据传感器和还需要查看的信息。
3.3 数据集匹配
首选 Immersed Tunnel CFD：可截取 3s/6s/10s/20s 早期窗口，生成“是否应预警、火源区间、受影响区域”的标签。PolyUFire
sidewall vent 可作为真实温度时序补充，但变量较少。D-Fire/DetectiumFire/Fire360 可提供视觉预警和火烟误报场景。若要高质量
non-fire 与弱火源样本，应使用 FDS/FD-Gen 生成低 HRR、通风扰动、传感器噪声和无火热源场景。
3.4 推荐指标
包括 AUROC、AUPRC、提前量 lead time、false alarm rate、miss rate、risk calibration、evidence alignment，以及物理解释违规
率。对于 LLM/agent，需额外评分：是否正确指出主导机制、是否识别信息不足、是否选择有效补充观测。
4. 任务二：火灾识别 Fire State Recognition
火灾识别不应只做 fire/smoke object detection，而应识别“当前火灾状态”：火源位置或区域、火灾阶段、火势强度、主导输运机制、
烟层/回流状态、通风影响和风险区域。
4.1 子任务设计
子任务 输入 输出 物理理解点
T2-A 火灾状态识别图像/视频、传感器、布局、通风状
态。
火灾阶段、火源区域、HRR 档
位、风险区域。
从可观测现象推断不可直接观测的
隐状态。
T2-B 主导机制识别同一场景的观测证据和候选机制。buoyant plume / ceiling jet /
longitudinal ventilation /
sidewall extraction /
backlayering 等机制。
区分“看到了烟”与“理解烟为什
么这样走”。
T2-C 物理一致性判断给出一段解释或模型回答。 判断是否物理合理，并指出错误
机制。
检验热浮力、烟层、质量/能量守
恒、通风方向等约束。

4.2 示例样本
解释待判定：“高温烟气密度较大，因此火灾初期会优先贴地向上游扩散。” 期望回答：不合理。高温烟气通常密度较低，先由浮力
上升形成火羽流，撞击顶棚后形成顶棚射流和烟层；上游回流需要结合通风速度与 critical velocity 判断。
4.3 数据集匹配
Immersed Tunnel 适合做火源位置、排烟配置和受影响区域识别。PolyUFire 的 critical velocity、back-layering length、smoke layer
thickness、plug-holing 等整理表适合生成机制识别与物理一致性题。D-Fire、DFS、DetectiumFire 和 Fire360 适合视觉火/烟与安全场
景识别，但需要补充机制标签。FDS validation/exp 可作为标准物理机制案例库。
4.4 推荐指标
包括 state accuracy、macro-F1、mechanism F1、physical consistency accuracy、explanation violation rate、evidence sensor
precision/recall。对生成式回答，建议把输出结构化为 JSON：answer、mechanism、evidence、uncertainty、violations。

5. 任务三：火灾演化 Fire Evolution Reasoning
这是最能体现火灾物理世界理解的任务。模型需要预测未来状态或比较干预后果，而不是只读当前图像或当前曲线。核心是状态转移、反事
实和物理约束。
5.1 子任务设计
子任务 输入 输出 物理理解点
T3-A 未来趋势预测当前观测窗口、空间布局、通风状
态。
未来 30/60/120 秒温度、soot、
CO、能见度、风险区域的方向性变
化或区间。
是否理解烟气随通风和浮力演
化。
T3-B 反事实干预推理Case A 与 Case B，仅改变一个变
量：风速、风阀、火源位置、HRR、
障碍物。
哪个区域风险上升/下降；传感器响
应顺序如何变化；是否更可能
backlayering。
区分相关性和因果性，是
benchmark 的核心样本类型。
T3-C 状态转移追踪多模态证据 + 问题。 initial_state、
dominant_mechanism、
transition steps、outcome、
evidence。
答案对不够，必须中间物理链
也对。
5.2 示例样本
Case A：下游排烟阀开启；Case B：下游排烟阀关闭；其他条件相同。问题：哪个 case 更可能导致下游能见度快速下降？上游
backlayering 风险如何变化？请给出因果链和证据变量。
5.3 数据集匹配
FDS + FD-Gen 是首选，因为演化和反事实需要可控变量和完整 ground truth。Immersed Tunnel 数据天然包含同一火源下不同排烟配
置，可构造干预 pair。PolyUFire sidewall vent 提供真实温度演化，可用于验证模型是否能迁移到实验数据。Fire360/DetectiumFire 可
补充真实视觉演化，但不能替代物理场 ground truth。
5.4 推荐指标
包括 trend direction accuracy、event time error、ranking accuracy、counterfactual consistency、state trace score、causal edge
F1、physical violation rate。对于数值输出可用 MAE/RMSE，但更建议先做区间或排序题，避免 LLM 被不必要的精确数值惩罚掩盖物理
推理能力。
6. 样本格式与评分协议
建议每个样本包含 scenario、observations、question、answer、physical_trace、scoring_metadata。核心是把可自动评分部分和专家
审计部分分开。
字段 说明
scenario 隧道/房间几何、传感器坐标、火源候选位置、通风/排烟配置、障碍物。
observations 传感器时序、图像/视频帧、Smokeview 截图、风险图、已有曲线。
question 预警、识别或演化问题；可为选择、排序、开放式 JSON。
answer 最终答案：分类、排序、趋势、风险区间或干预选择。
physical_trace 标准物理链：初始状态、主导机制、状态转移、结果、关键证据。
scoring_metadata 可自动评估的事件时间、传感器响应顺序、阈值、反事实方向、因果边。

推荐输出模板
{"answer":"...","risk_level":"...","dominant_mechanism":"...","causal_chain":["..."],"evidence":
["..."],"uncertainty":"...","missing_information":["..."]}

7. 数据划分与防投机设计
设计点 建议
匿名化 文件名、case ID 不得泄漏火源位置或排烟配置。例如原始 100M32.csv 这类名称必须替换为随机
ID。
OOD split 训练/验证/测试按火源位置、通风配置、HRR、几何布局、传感器布局分层；测试中包含未见过的组
合。
Counterfactual pair 同一场景只改变一个变量，要求模型预测方向性变化。
Adversarial explanation 加入物理错误解释，让模型检查热浮力、通风方向、烟层、backlayering、质量守恒等。
Tool-use 限制 agent 可调用绘图、检索、简单公式或 FDS 代理工具，但需记录调用次数和是否真正改善答案。
人类/专家上限 抽样邀请消防工程或火灾动力学背景人员标注，用于校准开放式解释评分。
8. 最小可行版本 MVP
第一版不需要一次性覆盖所有火灾场景。建议以“隧道火灾 + 火/烟视觉辅助”为主，先做可发表、可复现的 MVP。
模块 具体实现
数据 Immersed Tunnel CFD 作为主数据；PolyUFire sidewall vent 作为真实温度验证；D-Fire 或
DetectiumFire 作为视觉识别辅助。
任务 T1 早期预警：3/6/10/20 秒窗口；T2 状态识别：火源区域 + 主导机制；T3 演化：排烟配置反事实
pair。
标注 从 FDS CSV 自动派生：响应顺序、峰值时间、阈值超限、风险方向；人工补充机制解释模板。
基线 传统模型：CNN-LSTM/TCN/Transformer；LLM baseline：text-only、sensor-table QA、
LLM+plotting、LLM+retrieval、LLM+tool-use。
主要卖点 不是新的 fire detection 数据集，而是首个面向 LLM/agent 的火灾物理世界理解 benchmark：预警、
识别、演化三位一体。
9. 参考资料
Immersed Tunnel Fire Location Detection Data: https://github.com/zhang-zhen-project/immersed-tunnel-fire-location-
detection-data
Zhang et al., Intelligent fire location detection approach for extrawide immersed tunnels, Expert Systems with Applications,
2024: https://doi.org/10.1016/j.eswa.2023.122251
PolyUFire Tunnel Fire Database: https://github.com/PolyUFire/Tunnel_Fire_Database
NIST FDS/Smokeview Manuals: https://pages.nist.gov/fds-smv/
firemodels/fds: https://github.com/firemodels/fds
FD-Gen: Fire Data Generator, NIST: https://github.com/usnistgov/FD-Gen
DetectiumFire: https://arxiv.org/abs/2511.02495
D-Fire Dataset: https://github.com/gaia-solutions-on-demand/DFireDataset
Fire360: https://arxiv.org/abs/2506.02167
PhysBench: https://arxiv.org/abs/2501.16411
CausalPhys: https://arxiv.org/abs/2606.05966
QuantiPhy: https://arxiv.org/abs/2512.19526
World Models in Words: https://arxiv.org/abs/2605.29585

附注：现有公开数据并不能直接完成完整 FireWorldBench。真正的 benchmark 贡献在于把公开火灾/隧道/CFD 数据组织成带有反
事实、因果链、状态转移和物理一致性评分的任务集合。
