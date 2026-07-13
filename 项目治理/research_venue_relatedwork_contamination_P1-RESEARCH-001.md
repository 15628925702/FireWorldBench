# P1-RESEARCH-001 ICLR 2027 会议、相关工作与污染审计

审计时间：`2026-07-14 Asia/Shanghai`。目标会议由用户指定为 `ICLR 2027`。本报告只使用官方 ICLR 页面和论文/预印本页面；不把候选政策、未发布 CFP 或未核实数据许可写成已确定事实。

## 1. ICLR 2027 venue policy

| 项目 | 结论 | 证据/状态 |
|---|---|---|
| 会议存在与地点 | `ICLR 2027: West Coast North America` | [ICLR Future Meetings](https://iclr.cc/Conferences/FutureMeetings) |
| 2027 CFP | `BLOCKED`，官方 `https://iclr.cc/Conferences/2027/CallForPapers` 在审计日返回 HTTP 404 | 需 CFP 发布后复核 |
| 2027 日期/截稿 | `BLOCKED`，官方 `https://iclr.cc/Conferences/2027/Dates` 在审计日返回 HTTP 404 | 不使用 2026 日期倒推 2027 deadline |
| 双盲/匿名 | 2027 `BLOCKED`；ICLR 2026 明确 double blind，作者身份出现在正文或补充材料可 desk reject | [ICLR 2026 Author Guide](https://iclr.cc/Conferences/2026/AuthorGuide) |
| 正文页数 | 2027 `BLOCKED`；2026 为正文不超过 9 页，参考文献不计入 | [ICLR 2026 Author Guide](https://iclr.cc/Conferences/2026/AuthorGuide) |
| 补充材料 | 2027 `BLOCKED`；2026 要求与主论文同时提交，代码可作为补充材料，审稿人不一定阅读 | [ICLR 2026 Author Guide](https://iclr.cc/Conferences/2026/AuthorGuide) |
| 提交系统 | 2027 `BLOCKED`；2026 使用 OpenReview | [ICLR 2026 Call for Papers](https://iclr.cc/Conferences/2026/CallForPapers) |
| 数据/artifact | 2027 `BLOCKED`；2026 作者指南鼓励代码和可复现说明，但不等同于数据必须开放 | [ICLR 2026 Author Guide](https://iclr.cc/Conferences/2026/AuthorGuide) |
| 伦理/安全 | 需准备 ethics statement 和数据权利/隐私说明；2027 具体措辞待 CFP/指南发布 | [ICLR 2026 Author Guide](https://iclr.cc/Conferences/2026/AuthorGuide) |

### 对项目设计的约束

1. 论文正文采用不超过 9 页的保守目标，方法、数据边界、泄漏控制和局限性必须优先于大规模附录叙事。
2. 从现在起保持双盲友好：匿名仓库、匿名数据链接、去除作者身份的 supplementary，避免用私有仓库或带作者姓名的路径。
3. 代码和复现材料应可匿名提交，但当前数据许可仍为 `BLOCKED`，不能承诺公开原始数据或派生 benchmark。
4. ICLR 2027 日期、artifact 和数据政策不得在 P1-FREEZE-001 前假定；发布官方 CFP 后必须形成一次政策更新记录。

## 2. 相关 benchmark/论文差异矩阵

| 工作 | 主要对象/任务 | 与 FireWorldBench 的重合 | 当前可证差异 | 不能声称 |
|---|---|---|---|---|
| [Benchmarking Multi-Scene Fire and Smoke Detection](https://arxiv.org/abs/2410.16631) | 多场景火焰/烟雾检测，统一数据和评测 | 火灾视觉检测、跨场景评测 | FireWorldBench 计划聚焦 case/group、时序/CFD/实验约束、状态与演化推理；当前 D01 pair 已降级为配置比较 | “首个火灾 benchmark”或比其更全面 |
| [Sen2Fire](https://arxiv.org/abs/2403.17884) | Sentinel 多光谱/气溶胶野火检测 | 火灾检测、域外泛化 | 其核心是卫星遥感；FireWorldBench 的拟议核心是隧道/实验/CFD 与机制语义 | 跨传感器结果可直接比较 |
| [FireRisk](https://arxiv.org/abs/2303.07035) | 遥感火灾风险评估数据集与 benchmark | 火灾风险预测 | 场景和观测空间不同；需进一步读取全文确认标签/划分后再做细粒度差异 | 其任务与隧道火灾演化推理等价 |
| [GWFP: A Large Scale Open-Source Image and Video Dataset for Robust Wildfire Detection and Classification](https://arxiv.org/abs/2606.10174) | 全球野火图像/视频检测分类、跨域 | 图像/视频、负样本、域移 | FireWorldBench 目标不是扩大视觉素材规模，而是结构化 case、物理观测和证据链 | 仅靠视觉准确率证明物理理解 |
| [Robust Wildfire Forecasting under Partial Observability](https://arxiv.org/abs/2603.09042) | 遮挡/缺失观测下的野火时空预测 | 时序预测、观测不完整、预测鲁棒性 | 其核心是卫星火图预测；FireWorldBench 计划覆盖传感器/CFD/实验的机制问答与演化解释 | 把不同观测空间的预测指标直接合并 |
| [PhysBench](https://arxiv.org/abs/2501.16411) | 通用视觉语言物理世界理解 | 物理推理、VLM 评测 | FireWorldBench 可收缩为火灾领域、可观测字段、case provenance 和拒答/证据约束 | “首次物理世界 benchmark” |
| [FIRE / FIRE-Bench](https://arxiv.org/abs/2407.11522) | 多模态反馈改进对话 benchmark | 多模态、评测、反馈 | 不是火灾物理 benchmark；但 acronym/关键词会增加预训练或检索污染风险 | 将 FIRE-Bench 当作火灾相关基线 |

## 3. 可证实贡献边界

当前可以支持的表述：

- `FireWorldBench v1 设计一个面向火灾场景的、case-grouped 的多任务评测框架草案，尝试把时序观测、CFD/实验来源、结构化物理字段、状态识别和演化推理放进同一 provenance 契约。`
- `本项目明确区分视觉检测、可观测传感器预测和物理机制推理，不把检测准确率包装为世界理解。`
- `当前 D01 只能形成固定位置/车道下的配置比较；不存在已证实的单变量物理反事实 pair。`

禁止表述：`首个`、`唯一`、`全面覆盖`、`物理上真实理解`、`可公开再分发`，除非后续有正式证据、批准和冻结记录。

## 4. 污染风险与探针

| 风险 | 证据/原因 | 缓解 | 状态 |
|---|---|---|---|
| 公开论文/README/样本已进入模型预训练 | D01-D11 多数来源公开，且 ICLR/OpenReview/arXiv 内容公开 | 不把记忆性问答作为主证据；加入来源外、配置化和反事实一致性测试 | OPEN |
| 文件名直接泄漏标签 | D01 文件名含位置/车道/配置；D04 示例含项目名和参数 | 公开输入使用 opaque ID；私有映射保留；训练/测试按 group 隔离 | OPEN |
| 同一 case 窗口跨 split | D01 每个文件包含完整时序；D03 每个文件是序列 | 先按 case/family/sequence 划分，再切窗；执行 group intersection=0 检查 | REQUIRED |
| 视觉帧近重复/邻帧泄漏 | D05/D06/D10 有图像/序列样本 | 感知 hash、序列 stem、原始视频/来源分组；未完成前测试资格 BLOCKED | OPEN |
| 模板/生成器污染 | D04 README、示例 `.fds` 和生成器代码公开 | generator/project/template/seed family 整体隔离；测试前冻结参数空间 | REQUIRED |
| 题名/关键词碰撞 | `FIRE` 已被多个 benchmark 使用 | 使用明确的 `FireWorldBench` 标识和 opaque sample ID；污染探针加入无上下文控制题 | OPEN |
| 数据权利污染 | P1-DATA-001 将 D01-D11 用途资格全部置为 BLOCKED | 不训练、不评测、不公开派生数据；先完成许可证/版本审批 | BLOCKED |

### 最小污染探针

1. **名称去除对照**：比较带文件名/来源提示与 opaque ID 的性能差异，差异异常增大则判为 metadata leakage。
2. **来源外机制题**：仅使用未出现在公开样本中的参数组合和结构化字段，要求输出证据字段、单位和拒答状态。
3. **模板反事实题**：交换非答案相关命名、重排字段顺序和单位表达，检查答案是否保持语义一致。
4. **近重复隔离审计**：精确 hash、感知 hash、序列 stem、case/family/template 四层键均不得跨 split。
5. **记忆控制组**：加入与公开论文/README 同词但物理关系改变的控制题；不得把语言流畅度当作正确性。

## 5. 论文证据矩阵与开放问题

| 主张 | 必需证据 | 当前状态 |
|---|---|---|
| ICLR 2027 投稿约束 | 2027 官方 CFP/Author Guide/Dates | BLOCKED，页面尚未发布 |
| 数据可用于训练/评测/发布 | 逐源许可证、版本、获取日期、权利链 | BLOCKED，继承 P1-DATA-001 |
| D01 存在单变量物理 pair | FDS 输入/配置 diff/输出 manifest | NOT_SUPPORTED，已降级为配置比较 |
| 无 case/sequence/template 泄漏 | split manifest、精确/感知重复审计 | OPEN，规则已定义，执行待 P2 |
| 贡献区别于视觉 FSD/遥感 benchmark | 相关工作矩阵和实验任务差异 | PASS_AS_DESIGN_BOUNDARY，不等于 novelty proof |
| 物理推理能力 | 可观测字段、机制 gold、拒答与物理一致性评测 | OPEN，需 P2 ontology/schema |

下一任务：`P1-FREEZE-001`，只审计 P1 出口，不新增数据研究。
