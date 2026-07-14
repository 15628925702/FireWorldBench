# P3-PLANNING-MODE-ENABLEMENT

用户已明确授权方案阶段直接使用已下载的 D01/D02/D03/D04/D05/D10 staging，不再以许可证核验阻断本地研究流程。本轮已将 planning mode 写入配置和两份机器报告，并重新生成其哈希。

- `LOCAL_PLANNING_ALLOWED`：本地 train/dev 原型可使用已下载 staging。
- `BLOCKED`：正式测试、正式 benchmark、公开发布和再分发仍保持关闭。
- `NOT_CHECKED_PLANNING_MODE`：本轮不做许可证核验，不代表已获得公开发布许可。
- test/private 访问仍为禁止；`data/raw` 原始文件仍只读；不下载、不安装依赖、不执行外部生成器。

验收结果：planning mode 配置、candidate manifest、staging assessment 和回归测试一致；下一任务是本地 train/dev 原型构建。
