# Changelog

所有显著的研究协议、数据、代码和发布变更记录在此。未发布版本遵循语义化版本：任务/Schema 不兼容变更提升主版本，向后兼容能力提升提升次版本，修复提升补丁版本。

## [Unreleased]

### Added

- 项目章程、路线图、详细设计、开发约束和跨对话交接协议。
- 数据/划分/评测配置骨架与 benchmark JSON Schema。
- 决策、风险、开放问题、数据资产、需求和论文证据台账。
- 最小 Python 包、项目检查脚本和契约测试。
- 空 Conda 环境规格与本地 `fireworldbench-v1` 环境（暂不安装包）。
- 独立 Git `main` 仓库和 GitHub `origin` 连接（未提交、未推送）。
- 正式多模型全数据集运行的证据化 preflight、逐文件输入审计、模型矩阵、
  calibration/preregistration/runtime/run contract 冻结声明与不可覆盖哈希链。
- 个人研究模式：D01 全量可见 group-first train/dev/holdout、九任务自动标签、
  18 条平衡 DeepSeek 样本、零成本 majority/chance baseline 与初步结果简报。

## [0.1.0] - 2026-07-14

- 建立 FireWorldBench v1 项目初始化基线。
