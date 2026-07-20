# FireWorldBench ICLR 2027 核心方案 v3

## 1. 研究问题与范围

FireWorldBench v1 是面向 LLM 和多模态 agent 的火灾物理世界诊断 benchmark，目标是测量模型在部分可观测火灾动力系统中的三类能力：T1 早期预警、T2 当前状态与主导机制识别、T3 演化预测与受控干预推理。v1 只限定火灾领域；跨领域物理世界扩展留待后续版本。

本项目不宣称单一分数证明模型具有“世界模型”。可报告的结论必须绑定到可观测行为、证据引用、物理约束和跨任务一致性。

## 2. 统一任务本体

每个 case 由同一部分可观测动力系统生成，包含隐藏状态 `s_t`、观测 `o_<=t`、干预 `do(a)`、查询 `q` 和证据来源。T1/T2/T3 是同一 case 的不同视图，而不是互不相关的问答集合。

| 主线 | 能力 | 最小输出 |
|---|---|---|
| T1 | 弱信号检测、异常归因、风险与提前量判断 | 风险、提前量、证据、缺失信息、不确定性 |
| T2 | 当前状态、火灾阶段、主导机制与物理一致性 | 状态、机制、证据、约束检查 |
| T3 | 趋势、反事实方向、状态转移和干预后果 | 转移图、时间/方向、结果、因果证据 |

统一输出使用结构化 `physical_state_graph`：`state_nodes`、`mechanism_edges`、`temporal_order`、`evidence_links`、`constraint_checks`。自由文本仅作为解释，不作为唯一评分依据。

## 3. 能力—数据源—任务矩阵

异构数据集允许承担不同证据角色，不要求每个数据集覆盖全部任务。仿真数据提供可控变量、反事实和完整状态；实验/实测数据提供外部真实性校验；视觉数据只承担感知或辅助 OOD 轨道，不能直接充当物理 ground truth。

| 数据源 | 证据角色 | 主任务 | 限制 |
|---|---|---|---|
| Immersed Tunnel CFD | 受控仿真、空间定位、排烟对比 | T1/T2/T3 | 规模有限，需匿名化与物理标签派生审计 |
| PolyUFire | 实验/整理测量外部验证 | T1/T2，T3 趋势验证 | 变量不完整，不能替代完整场 |
| FDS/FD-Gen | 受控生成、反事实、难度扩展 | T1/T2/T3 | 需记录网格、边界、验证状态；模拟值不等于现实真值 |
| D-Fire、DetectiumFire、Fire360 | 视觉感知与辅助 OOD | T1/T2 辅助轨道 | 非同 case 多模态，不能与 CFD 直接融合 |

## 4. 样本与切分

每个样本必须有稳定 `case_uid`、`source_id`、`gold_origin`、观测预算、时间窗、变量单位和许可状态。采用 group-first 切分，并按火源位置、HRR、通风、几何、传感器布局和时间 horizon 做 OOD 评估。反事实 pair 只有在初始状态和其他变量对齐、且只改变一个干预变量时才成立。

## 5. 评测与报告

基础指标包括 AUROC/AUPRC、macro-F1、lead-time、趋势方向准确率、事件时间误差、MAE/RMSE 和校准误差。物理指标包括 evidence alignment、physical violation rate、机制 F1、causal edge F1、counterfactual consistency 和 cross-task consistency。每个结果必须同时报告数据源、任务视图、切分、样本数、置信区间和许可状态。

## 6. 基线与方法路线

先运行数值/时间序列 baseline、视觉 baseline、text-only/sensor-table LLM、plotting、retrieval 和 tool-use 对照。benchmark 与基线稳定后，根据最明显失败模式决定方法：物理 trace prompting、结构化状态记忆、检索或仿真工具调用。方法不是预先硬塞的贡献，而由 benchmark 暴露的问题驱动。

## 7. 论文主张边界

论文主张应表述为“在火灾动力学诊断任务上的能力差异和失败模式”，避免无证据的“首个”与“理解世界”绝对表述。ICLR 2027 版本的核心贡献是统一 task ontology、异构数据源的证据分工、跨 T1/T2/T3 一致性评测和可复现的模型运行协议。

## 8. 支撑文献

文献包见 `G:/0-newResearch/2/1.参考文献/FireWorldBench_补充文献_2026-07-16/`，索引和 SHA-256 见其中 `INDEX.md` 与 `MANIFEST.json`。通用物理 benchmark、因果/反事实推理、火灾数据与 FDS 方法学均已纳入；新增论文必须先登记、核验许可和 DOI/arXiv 元数据。

