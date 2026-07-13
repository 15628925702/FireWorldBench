# P1-DATA-003 数据质量、case 语义与泄漏键审计

审计时间：`2026-07-14 Asia/Shanghai`。输入为 P1-DATA-001 manifest、P1-DATA-002 契约和仓库外 `../../3.数据集`；外部目录只读，未生成或覆盖任何原始文件。

## 1. 质量摘要

| 检查 | 结果 | Disposition |
|---|---|---|
| manifest 文件总数 | 312 | PASS；逐文件路径/大小/hash 复用 P1-DATA-001 |
| 零字节文件 | 0 | PASS |
| D01 CSV | 8 个，均 603 行×921 列；缺失 0；非有限/非数字数据单元 0 | PASS；保留宽表，不在本轮切窗 |
| D03 CSV | 5 个，分别 206/361/202/96/75 行；宽度 2/2/2/106/106；缺失 0；非有限/非数字数据单元 0 | PASS；ATF 字段单位仍 UNKNOWN |
| D02 XLS | 110 个文件 | BLOCKED；未安装解析包，单位/工作表语义不闭合 |
| D04 生成器 | 50 个文件 | BLOCKED；不是已生成 FDS 结果集，需单独冻结 generator/version/seed |
| 精确重复 hash | 1 组：`04_FD-Gen/example_preview.png` 与 `04_FD-Gen/FD-Gen-main/images/Picture1.png` | 解释为演示图副本；排除数据样本，不作为训练/评测输入 |
| D05/D06 标签文本 | 当前样本标签文件均非零字节；D05 的空标签语义只由 sample card 描述 | BLOCKED；需在质量阶段确认负样本/空标签规则及来源权利链 |

## 2. Case/family/sequence 注册表

| 数据集 | case key | family key | sequence key | 当前 disposition |
|---|---|---|---|---|
| D01 | 去除 `_devc.csv` 的文件名，例如 `70U01` | 位置+车道：`70U`、`100U`、`130M` | case 内原始时间序列；窗口编号不得成为 case | 可执行，但文件名编码不等于完整物理元数据 |
| D02 | `Test1`-`Test8`/工作表待确认 | 主题实验/试验批次待确认 | `RecordTime` 及测点序列待确认 | BLOCKED，直到 XLS 字段和单位可读 |
| D03 | 相对路径中的文件名 | `Aalto_Woods` / `ATF_Corridors` | 文件内时间序列 | 可执行到文件级；不同实验族不得混合为同一 family |
| D04 | `PROJECT_NAME` + 生成 case index | generator project + parameter family | 生成 case 的 seed/参数记录 | 仅生成计划键；当前样本不是结果集 |
| D05/D06 | 图像 stem/配对 metadata | 原始来源/视频序列待确认 | 图像或视频序列待确认 | BLOCKED，不得用于正式 split |

## 3. D01 pair 参数核验

文件名编码由 D01 README 和 `ReadDataSet.py` 支持：位置 `70/100/130`、车道 `M/U`、末两位排烟配置编号。当前 8 个文件为：

`70M01`, `70U01`, `70U08`, `70U16`, `100U16`, `130M01`, `130M08`, `130U16`。

可观察比较：

- `70U01` vs `70U08` vs `70U16`：位置和车道固定，配置编号变化；只能命名为“排烟配置比较”。
- `130M01` vs `130M08`：位置和车道固定，配置编号变化；只能命名为“排烟配置比较”。
- `70M01` vs `70U01`：位置和配置固定，车道变化。
- `70U01` vs `130U16` 等同时改变位置与配置，不能作为单变量 pair。

缺口：配置编号到实际排烟几何/风量/开关状态的映射未随本地样本提供；因此不能声称“仅改变排烟参数”，也不能把这些文件用于因果/反事实单变量结论。P1 当前降级为配置比较，后续若需物理 pair 必须补齐 FDS 输入和参数 diff，并重新审计。

## 4. 泄漏键与 split 规则

- 强制 group key：`source_dataset_id + case_id`；D01 不得跨同一文件切分 train/dev/test。
- 视觉序列：`source stem + contiguous sequence`；相邻帧、同一原视频、同一标注模板必须同组。
- 近重复键：文件 SHA-256 是精确重复键；感知重复尚未执行，正式 split 前必须补充。
- template 键：D04 的 `PROJECT_NAME`、example 文件、参数模板和 seed family 必须整体隔离；不能把生成窗口当独立样本。
- family 键：D01 的位置+车道至少作为 family 候选，配置编号作为 scenario/config key；未有配置物理映射前不宣称 OOD 轴。
- D02 的 `TestN`、D03 的实验族、D05/D06 的原始来源/视频序列均必须先注册，再切窗或派生问答。

## 5. 修复/排除策略

1. 本轮质量通过且无数值缺失的 D01/D03 文件可进入后续研究性探查，但仍受 P1-DATA-001 的许可与用途 `BLOCKED` 门禁限制。
2. D02 先补充只读 XLS 解析能力和单位证据；不猜测单位、不生成 canonical 数值。
3. D04 只保留 generator inventory；正式生成前冻结 FDS/FD-Gen 版本、参数空间、seed、case family 和输出 manifest。
4. D05/D06 空标签、非火样本和外部来源必须分别验证语义与权利链；未知项保持 BLOCKED。
5. 删除/排除重复演示图的副本不会修改外部原始目录；仓库只记录排除规则，不搬运或清洗原文件。

## 6. 结论

质量问题已逐项 disposition；D01/D03 的 group key 可执行，D02/D04/D05/D06 的关键语义仍有阻塞。D01 现有样本不能形成已证实的单变量物理 pair，正式结论降级为配置比较。下一任务为 `P1-RESEARCH-001`。
