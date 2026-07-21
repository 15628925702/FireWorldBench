# FireWorldBench

FireWorldBench 是 simulation-grounded 火灾物理世界理解 benchmark，研究模型能否从 S/I/V
有限观测中完成动态感知、状态恢复和未来演化推理。

## 当前状态

状态为 `PAUSED_FOR_FINE_GRAINED_TASK_METRIC_REDESIGN`。用户已要求停止使用旧九任务指标开展
新实验。新的任务与指标草案位于：

- `docs/FINE_GRAINED_TASK_METRIC_REDESIGN.md`
- `docs/TASK_PROTOCOL.md`
- `docs/EVALUATION_CARD.md`

新协议保留九个 ID，但将任务升级为：多信号归因、因果下一状态、时序违规定位、联合
source-stage、风险驱动恢复、机制-流向-控制域、多时距多变量预测、首次越阈预测和反事实
效应分解。主指标改为 Macro-F1、分层 Accuracy 和 Joint/Strict Exact Match。

S/I/V 是三个独立评测套件，可分别使用文本模型、图像/VL 模型和 direct-video 模型；不要求
同一个模型覆盖三轨，未参评轨道不扣分，也不生成跨轨总分。

## 不可变事实

- FDS Core v3.3.1：180/180 strict Events、4,039 QA，只读。
- 外部 formal Events/QA：0；所有 candidate/substitute/quarantine/gap 继续分离。
- 旧 gpt-4o-mini 与 baseline 分数仅为旧协议难度证据。
- 只有 `src/fireworld/` 是 active implementation；当前未授权修改代码或启动模型实验。
- 不使用 LLM judge，不处理新数据集，不把外部数据并入 FDS Overall。

## 下一门禁

先版本化 QA/prediction schema 和新增 metadata，再实现 validators/scorer/tests，随后构建独立
challenge candidate subset。只有难度、support、专家可回答性和基线门禁通过后才启动 pilot。
