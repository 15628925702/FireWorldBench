# P1-DATA-002 字段、单位与标准化契约

审计范围：P1-DATA-001 中允许继续研究的 D01-D04。D05-D11 仍因许可/版本门禁或仅有演示素材而不进入本契约。原始目录 `../../3.数据集` 只读，所有转换均为逻辑映射，不覆盖源文件。

## 1. 证据边界

| 源 | 字段证据 | 单位证据 | 当前可研究边界 |
|---|---|---|---|
| D01 | `01_Immersed-Tunnel-CFD/README.md`、`ReadDataSet.py`、CSV 前两行 | CSV 第一行：`Time=s`；C 类含 `mol/mol`；部分末尾列含 `kg/s`；其余必须逐列读取单位行 | 原始宽表时序、文件名 case 元数据、滑窗逻辑；不可把 C/T 物理含义扩展到未读证据 |
| D02 | `Tunnel_Fire_Database-master/README.md`、`Tunnel_sidewall_vent/Read me.txt`、Test1 说明、表名 | XLS 单位未由可读说明确认 | 主题表/测点列名可登记；数值单位、坐标和采样间隔保持 `UNKNOWN` |
| D03 | `sample_card.md`、5 个 CSV 表头/单位行 | Aalto：`s,kW/m2` 或 `s,kg/s/m2`；ATF 走廊 CSV 未提供单位行 | 时间和文件级字段登记；HRR/热流/TC/VEL 的单位未知时不转换 |
| D04 | `FD-Gen-main/README.md`、示例 `.fds`、`LICENSE.md` | FDS/FD-Gen 语法和示例值可引用；未标注单位不猜测 | 仅作为受控生成参数 schema/配置输入；生成结果必须另有 FDS 版本、seed、配置和输出 manifest |

## 2. L0 原始字段字典

### D01 Immersed-Tunnel-CFD

| 原字段/来源 | 原始语义 | 原单位 | L0 类型 | 备注 |
|---|---|---|---|---|
| `Time` | 仿真时间轴 | `s` | float | 保留原始值和原始文本精度 |
| `C-*` | CSV 中的 C 系列测点 | `mol/mol`（按对应单位行） | float | 不扩写为具体化学组分；列名/位置是证据 |
| `T-*` | CSV 中的 T 系列测点 | 逐列读取；未确认则 `UNKNOWN` | float | 不把 T 自动转换为摄氏/开尔文 |
| 末尾流量列 | 流量相关输出 | 部分为 `kg/s` | float | 只有单位行明确时才进入 canonical |
| 文件名 `70M01` 等 | 位置/车道/排烟配置编码 | N/A | string | README：70/100/130 为位置；M/U 为车道；末两位为排烟配置；位置数值单位由 README 的“meters”给出 |

`ReadDataSet.py` 还显示原作者的预处理：`soot_sensors=[0,10,...,100]`、`temp_sensors=[213,220,...,290]`、`time=300`、`slide=30`，并用 `f[-11:-9]` 取排烟标签。该逻辑只登记为历史 adapter 证据，不自动成为冻结划分规则。

### D02 PolyUFire

| 原字段/来源 | 原始语义 | 原单位 | L0 类型 | 备注 |
|---|---|---|---|---|
| `RecordTime` | 记录时间 | `UNKNOWN` | string/number | 需逐工作表读取确认 |
| `1-1-1`、`1-2-4`、`1-jg1-3` 等 | 实验测点编号 | `UNKNOWN` | float | 测点拓扑/坐标未在当前证据中闭合 |
| `3.1`-`3.7` 工作表/文件 | HRR、flame length、ceiling gas temperature、critical velocity、back-layering、smoke layer thickness、plug-holing | `UNKNOWN` | table | 主题名不是单位证据 |
| `Test1`-`Test8` | 实验分组 | N/A | string | 不得在未读取元数据前解释为独立 case/family |

### D03 FDS-exp

| 原字段/来源 | 原始语义 | 原单位 | L0 类型 |
|---|---|---|---|
| Aalto CSV 第 1 列 | 时间 | `s` | float |
| `HRRPUA`（flaming） | 文件表头给出的字段 | `kW/m2` | float |
| `HRRPUA`（smolder） | 文件表头给出的字段 | `kg/s/m2` | float |
| ATF `Time` | 时间字段 | `UNKNOWN` | float |
| ATF `HRR` | 热释放率字段名 | `UNKNOWN` | float |
| ATF `Heat_Flux_*` | 热流字段名 | `UNKNOWN` | float |
| ATF `TC_*` | 热电偶字段名 | `UNKNOWN` | float |
| ATF `VEL_TEMP_*` / `VEL_BDP_*` | 速度/差压相关字段名 | `UNKNOWN` | float |

### D04 FD-Gen

| 原字段/语法 | 原始语义 | 单位处理 |
|---|---|---|
| `PROJECT_NAME`, `NUMBER_OF_CASES`, `SEEDS` | 项目、生成 case 数、随机种子 | string/int；不转换 |
| `T_BEGIN`, `T_END`, `DT_DEVC`, `DT_HRR` | 时间控制 | README/示例明确为 FDS 时间参数；canonical 统一为秒，但源值必须保留 |
| `MESH IJK`, `XB`, `MULT DX/DY`, `MESH_SIZE` | 网格索引、坐标边界、网格尺寸 | 坐标/长度单位必须由 FDS case 约定；未在本地 case 全部闭合前标 `UNKNOWN` |
| `IFSL`, `IVTP`, `IDWT`, `IRXB` | 火源位置、通风位置、门窗时间、障碍物参数 | 数值范围/结构保留；单位未知不转换 |
| `IFTD`, `IMHR`, `IHRC` | 火灾持续时间、最大 HRR、HRR 曲线 | 时间按源字段保留；HRR 单位未知不转换 |
| `MRND` | 采样分布、seed、范围/均值/标准差 | 参数类型和数值保留；不得把 `APPROX` 当物理单位 |

## 3. Canonical L1 schema

每条记录必须保留 `source_dataset_id`、`source_relative_path`、`source_sha256`、`source_row_index`、`case_id`、`sequence_id`、`time_value_l0`、`time_unit_l0`、`variables_l0`、`units_l0`、`canonical_values`、`conversion_trace` 和 `status`。

- `case_id`：D01 暂用文件名去除 `_devc.csv`；D02/D03/D04 在 metadata 完整前为 `UNKNOWN` 或显式项目名，不由索引猜测。
- `sequence_id`：窗口切片前为 `case_id`；不得把窗口编号当独立 case。
- `canonical_values`：仅对单位明确且存在可逆规则的字段填值；否则为空并将该变量标为 `UNKNOWN_UNIT`。
- `conversion_trace`：记录 `identity`、`s_to_s` 等规则、原值 hash/行号和工具版本；任何不可逆清洗均拒绝。
- 缺失编码：原始空字段、`NaN`、非数字文本原样保留于 `raw_value`，canonical 值为 null，原因写入 `missing_reason`；不把 0 推断为缺失。

## 4. 可逆转换规则

| 规则 ID | 输入 | 输出 | 可逆性 |
|---|---|---|---|
| `identity_numeric` | 已确认单位的数值 | 相同数值/单位 | PASS |
| `time_s_to_s` | `s` | `s` | PASS |
| `length_identity_unknown_unit` | 长度数值但单位未闭合 | 不生成 L1 数值 | BLOCKED |
| `unit_unknown` | 任意未知单位 | 不转换 | BLOCKED |

本轮不执行摄氏/开尔文、kg/s 与 mol/mol、HRR/热流等换算，因为对应原始单位/物理定义未完整闭合。

## 5. 研究边界

D01-D04 的字段契约已形成，但 P1-DATA-001 的用途资格仍是 `BLOCKED`；本轮契约不授权训练、开发、测试、派生发布或再分发。下一任务应先做质量、缺失、重复、case/family 和潜在泄漏键审计。
