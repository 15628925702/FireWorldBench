# FireWorldBench v2 项目章程

状态：`USER-DIRECTED-FINE-GRAINED-REDESIGN`
生效日期：`2026-07-21`

## 1. 当前目标

FireWorldBench 评估多模态基础模型能否从有限火灾观测中完成动态感知、当前状态恢复和未来
演化推理。用户最新指令要求重设计原九任务与指标，使任务更加细粒度、联合、可诊断，并通过
冻结开发挑战集校准合理难度。

现行任务与指标权威为 `docs/FINE_GRAINED_TASK_METRIC_REDESIGN.md` 和
`docs/TASK_PROTOCOL.md`。核心设计 PDF 与旧协议继续解释既有 FDS Core v3.3.1，但不再授权
新实验使用旧任务/指标。

## 2. 研究与数据边界

- 保留 L1/L2/L3 和 S/I/V；不把 I/V 伪装成 S。
- S/I/V 是独立评测套件，可分别选择不同模型；不要求一个模型完成三轨，不生成跨轨总分。
- FDS Core v3.3.1 完全只读：180/180 Events、4,039 QA 不变。
- 旧模型结果仅作难度校准证据，不是新协议结果。
- 外部正式 Events/QA 仍为零；candidate/substitute/quarantine 状态不变且不进入 Overall。
- 不开展新的数据集搜索、下载、迁移、清洗、标注或外部正式 QA 生产。
- 不使用 LLM judge，不静默修复模型输出，不伪造 expert/license/provenance。

## 3. 难度原则

30--50 是代表模型在冻结开发挑战集上的目标中位带，不是强制单模型区间。难度来自 hard
negatives、联合精确输出、多时距、越阈预测、反事实分解和 OOD，而非分数缩放或歧义。
正式测试解盲后不得按模型表现重新调题。

## 4. 当前门禁

模型实验暂停。先完成版本化 schema、metadata、validators、scorer、challenge subset、
deterministic baselines、support 和专家可回答性门禁，再申请小规模多模型 pilot。
