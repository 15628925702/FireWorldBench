# P3-PIPELINE-001 数据适配与 canonical case pipeline

日期：2026-07-14  
任务状态：DONE_WITH_BLOCKED_EXTERNAL_DATA

## 实现内容

- `src/fireworldbench/pipeline.py` 提供只读 inventory、内容 SHA-256、CSV/JSON/JSONL adapter、L0 保留、显式时间单位转换、case/sequence graph、质量统计和失败报告。
- `fwb pipeline-inventory` 只扫描并 hash 文件，不改写输入。
- `fwb pipeline-build` 生成确定性 canonical manifest；每条记录保留来源相对路径、来源 hash、行号、原始值、单位和转换轨迹。
- 不认识的单位、缺失 case_id、坏 JSON 和不支持的后缀均产生结构化 failure；不猜测物理含义、不把缺失值变成 0。

## 数据边界

本轮没有修改仓库外 `../../3.数据集`，没有读取 test input、test gold 或 private mapping。P1 的数据许可门仍为 BLOCKED，因此没有把外部原始数据写入 train/dev/test，也没有生成正式 benchmark 结果。

## 验证

- 正常 fixture：CSV/JSON/JSONL 适配、时间单位转换和 case graph 通过。
- 边界 fixture：未知单位保留 L0 并标记 `UNKNOWN_UNIT`。
- 损坏 fixture：缺失 case_id 进入 `ROW_INVALID`，其余有效记录不丢失。
- `python scripts/check_project.py` 与全量 pytest 是本轮验收门。

下一任务：`P3-BUILD-T1`。
