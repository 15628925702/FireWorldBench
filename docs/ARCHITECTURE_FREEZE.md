# FireWorldBench v2 Architecture Boundary During Redesign

状态：`TASK_METRIC_FREEZE_LIFTED_BY_USER_DATA_BOUNDARIES_STILL_FROZEN`
日期：`2026-07-21`

用户已明确要求重设计细粒度任务和指标。旧任务/指标冻结不再授权新的实验或排行榜；新的现行
设计入口为 `docs/FINE_GRAINED_TASK_METRIC_REDESIGN.md` 和 `docs/TASK_PROTOCOL.md`。

仍然冻结且不可更改：

- FireWorldBench 的三层能力目标与 S/I/V 真实模态边界。
- Fire Event、event_group-first split、公开问题/私有 gold 分离。
- FDS Core v3.3.1 的 180/180 Events、4,039 QA、release manifest 与全部文件。
- 外部来源的 candidate/substitute/quarantine/gap 状态及其独立报告边界。
- 禁止把外部数据放入 FDS Overall，禁止 LLM judge，禁止伪造标签、许可或专家审核。
- `src/fireworld/` 为唯一 active implementation；legacy 不得复用为新协议证据。

尚未冻结：

- 新 QA/prediction schema 和新增字段。
- horizon、difficulty、violation location、risk driver、time bin、pairing metadata。
- 新 challenge subset、support 门禁和任务级阈值。
- 新 scorer、validators 和新协议 Overall 的发布资格。

在这些项目完成并验收前，禁止正式或 pilot 模型实验。文档设计可以继续；FDS Core 不得回写。
