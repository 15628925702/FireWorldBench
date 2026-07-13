# P2-SPLIT-001 Group-first 与 OOD 划分报告

## 结论

本轮冻结的是“划分规则和研究性候选分配”，不是正式 benchmark split。P1 许可门禁仍阻塞所有 D01-D11 的正式训练/开发/测试/发布用途，因此配置状态为 `research_plan_blocked_by_p1_license_and_sample_size_gates`。

## Group-first 规则

1. 先按 `source_case`、`simulation_family`、`physical_scenario`、`video_sequence`、`near_duplicate_group`、`question_template_family` 建组。
2. 组分配完成后才允许切窗口、派生问答或增强。
3. 同一 case、family、序列、近重复组或题型模板不得跨 train/dev/test。
4. 统计单位是 case 或合法 pair，不是窗口。
5. 不强行使用 8:1:1；比例由 group 数和 OOD 可行性决定。

## 当前候选分配

| split | groups | 含义 | 状态 |
|---|---|---|---|
| `train_id` | D01 70U、100U | 训练域候选 | provisional + P1 license blocked |
| `dev_id` | D01 70M | 开发候选 | provisional + P1 license blocked |
| `test_ood_source_location` | D01 130M、130U | 位置 OOD 候选 | provisional；lane/config 混杂 |
| `test_external_experiment` | D03 Aalto_Woods、ATF_Corridors | 外部实验候选 | provisional + P1 license blocked |

当前 7 个 group 的交集为零，且每个 D01 文件只属于一个 group；D04 只有 generator/template，不进入结果 split；D05-D11 因 P1 门禁或 placeholder 状态排除。

## OOD 可行性

- `source_location`：可以形成一个候选位置 OOD，但只有 5 个 D01 family，且位置与 lane/configuration 不完全平衡；正式结论必须标注混杂。
- `ventilation`：BLOCKED。D01 配置编号没有经过验证的排烟物理参数映射，不能称为通风 OOD。
- `hrr`：BLOCKED。当前文件名/字段单位不足以形成受控 HRR 轴。
- `geometry_or_layout`：BLOCKED。没有足够独立几何 group。
- `external_experiment`：可定义为 test-only 外部域，但 D03 仍受许可证阻塞，不能作为正式测试结果。

## 混杂与风险

| 风险 | 处置 |
|---|---|
| D01 位置与 lane/configuration 混杂 | 只称 `source_location` 候选 OOD；不报告独立因果效果 |
| D01 配置编号不等于已知通风参数 | 不启用 ventilation OOD；等待 FDS 输入/参数 diff |
| D03 文件数量少且单位部分未知 | 仅保留 external validation 组定义，不计算正式指标 |
| 感知重复和模板泄漏尚未完成 | P2-LEAK-001 前禁止正式冻结 split |
| P1 许可证/再分发阻塞 | 所有组标 `PROVISIONAL_BLOCKED_BY_LICENSE` |

## 稳定性

- 配置 seed：`20260714`。
- 组分配不是按窗口随机抽样，而是由 `group_id` 显式记录。
- 后续实现应对 `split_id + seed + group_id + config_version` 计算 SHA-256，并把结果写入 split manifest。
- 任何 group 增删或重分配必须产生新 split 版本，不得静默改写。

下一任务：`P2-LEAK-001`，执行 opaque ID、精确/感知重复、邻帧、模板和元数据泄漏审计。
