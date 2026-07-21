# FireWorldBench v2 协作入口

本文件适用于本仓库及全部子目录。

## 1. 当前用户指令

2026-07-21 用户明确要求暂停实验并重设计细粒度任务与指标。该最新指令优先于核心 PDF 和
旧冻结协议。现行设计入口：

1. `docs/FINE_GRAINED_TASK_METRIC_REDESIGN.md`
2. `docs/TASK_PROTOCOL.md`
3. `docs/EVALUATION_CARD.md`
4. `PROJECT_CHARTER.md`
5. `ROADMAP.md`

旧任务、旧 prediction schema 和旧模型结果只用于解释 FDS Core v3.3.1 与难度证据，不得
继续形成新实验或新排行榜。

## 2. 不可变边界

- FDS Core v3.3.1 只读：180/180 Events、4,039 QA、8,209 manifest entries 不变。
- 外部 formal Events/QA 为零；candidate/substitute/quarantine/gap 状态不变。
- 外部来源永不进入 FDS Overall；不新增数据集工作，不伪造标签/许可/专家审核。
- 只有 `src/fireworld/` 是 active implementation；`src/fireworldbench/` 和旧 artifacts 为 legacy。
- S/I/V 必须使用真实对应模态；无直接视频能力时 V 为 unsupported。
- 禁止 LLM judge、字段别名修复、缺失预测静默忽略和不稳定动态模型 alias。

## 3. 当前允许范围

只允许任务/指标文档设计与一致性审阅。未经用户后续授权，不修改实现/schema，不构建新 QA，
不调用模型，不启动 pilot，不改 FDS Core，不处理任何外部数据。

## 4. 新协议原则

- 30--50 是冻结开发挑战集上代表模型群体的难度校准目标中位带，不是分数缩放目标。
- S/I/V 为独立评测套件，可使用不同 fixed model IDs；不要求单模型覆盖三轨，不做跨轨排名。
- 新任务采用 Macro-F1、horizon-macro Accuracy、Joint/Strict Exact Match 等协议匹配指标。
- 排行榜使用完整分母；missing/malformed/schema-invalid 计 0。
- support 不足的任务只报告，不排名；极小样本不能得出模型排序结论。
- 新字段必须通过版本化 schema 和 frozen metadata 引入，不回写旧 release。

## 5. 后续实现门禁

任何代码修改前重新读取上述现行设计文件，并先提交 schema/metadata/scorer 测试计划。模型实验
必须等 challenge subset、validators、deterministic scorer、基线、专家可回答性和预算全部验收。
