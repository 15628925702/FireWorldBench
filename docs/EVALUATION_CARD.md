# FireWorldBench v2 Evaluation Card

状态：`PAUSED_FOR_TASK_METRIC_REDESIGN`
协议：`FWB-FINEGRAIN-v1 draft`

## Headline evaluation

- S/I/V 是独立套件，可以由不同模型分别参评；不要求一个模型覆盖三轨。
- 未参评轨道不计 missing、不扣分。模型只在同轨、同任务矩阵、同 subset、同协议版本内排名。
- 新主榜使用九项细粒度任务各自的协议匹配主指标，不再统一使用 Accuracy/组件均值。
- 排行榜分数使用完整分母：missing、malformed、schema-invalid 均计 0。
- 每个模型同时报告 valid-only 诊断分数、coverage、失败类型和每类 support。
- S 九任务全部通过门禁时可计算 `S Overall`；I/V 只计算预先冻结的 eligible task suite macro。
- 不生成跨 S/I/V 总分；外部数据独立报告，永不进入 FDS Overall。

## Task metrics

- L1-1 Macro-F1。
- L1-2 horizon-macro Accuracy。
- L1-3 Hierarchical Joint Exact Match。
- L2-1/L2-2/L2-3 Joint Exact Match。
- L3-1 三个时距 Strict Triple Exact Match 的宏平均。
- L3-2/L3-3 Joint Exact Match。

每任务的组件 Accuracy、Macro-F1、confusion matrix、balanced accuracy 和配对一致性是
诊断指标，不自动进入 Overall。ECE/Brier 仅在合法 confidence 存在时报告。

## Difficulty and integrity

开发挑战集的代表模型中位数以 30--50 为校准目标；不缩放分数，不通过歧义或错误标签压分。
要求专家上限、基线差距、hard-negative、event-group OOD、模板与路径 shortcut audit。
正式测试解盲后禁止重新调任务、阈值和答案空间。

旧 FDS Core v3.3.1、gpt-4o-mini 和 baseline 结果保留为
`legacy_protocol_calibration_evidence`，不与新协议结果直接比较。
