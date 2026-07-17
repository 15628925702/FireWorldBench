# FireWorldBench v2 Data Directory

- `raw/`：当前已有来源快照，只读，不移动、改名、覆盖或自动扩大下载。
- `events/`：通过 `schemas/fire_event.schema.json` 的统一 Fire Events。
- `qa/`：通过 `schemas/qa.schema.json` 的九任务 S/I/V QA。
- `splits/`：按 event_group 在任何切片和 QA 派生前生成的 manifest。

旧 raw 资产不因已下载而获得 v2 资格。只有 FDS 核心、Immersed/PolyU 外部桥接、D-Fire/Fire360 真实 OOD 和合格的可选 Detectium 按 `docs/SOURCE_ROLE_MATRIX.md` 使用。任何生成物必须记录来源、许可、版本、哈希和再发布范围。

