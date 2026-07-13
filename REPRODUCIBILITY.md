# Reproducibility Contract

FireWorldBench 的最小复现单位不是单个分数，而是完整 run：固定代码、数据 manifest、benchmark/scoring 版本、配置、环境、模型快照、prompt、工具和原始输出。

正式 run 必须保存：

- Git commit 与 dirty diff 状态；
- Python/依赖锁、OS、硬件和外部二进制版本；
- 数据、split、benchmark、评分器和配置 SHA-256；
- 模型完整 ID/快照日期、生成参数、随机种子与重复编号；
- prompt/few-shot/retrieval/tool 配置；
- 全部原始响应、解析错误、重试、工具轨迹、token、成本和延迟；
- 逐样本得分、聚合指标、统计脚本和生成表图的命令。

正式 run 必须来自 clean Git commit。只有 freeze 决策明确批准时才允许使用不可变源码归档替代，并记录归档 SHA-256；普通 dirty/UNBORN 状态不得生成正式结果。正式结果目录不可覆盖。论文冻结前必须在干净环境完成一次从数据 manifest（或合规 fixture）到代表性表格的独立重建。
