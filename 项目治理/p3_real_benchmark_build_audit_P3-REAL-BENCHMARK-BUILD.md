# P3-REAL-BENCHMARK-BUILD

本轮基于已存在的本地 staging，构建了只读、可重复的候选 case manifest。机器结果为 `p3_real_benchmark_build_P3-REAL-BENCHMARK-BUILD.json`。

- D01：8 个 FDS 两行表头 CSV 被映射为候选 case；case/sequence 使用 `dataset_id + source_relative_path`，Time 保留原始单位，生成每文件最小两行 fixture 探针。
- D02：0 个候选 case；Excel 主体和非标准 CSV 需要单独批准的安全适配器，当前保持阻塞。
- D03：3 个 FDS 两行表头 CSV 被映射为候选 case；仍需正式 schema、case/family/sequence 审核和 gold provenance。
- 总计：11 个候选 case，状态为 `CANDIDATE_CASES_BUILT_FORMAL_USE_BLOCKED`。

本轮没有修改 `data/raw`，没有读取 test/private 或外部 `../../3.数据集`，没有执行 D04，未安装或下载任何包。所有训练、开发、测试、派生发布、再分发资格仍为 `BLOCKED`；下一门禁是 source/version/license 审批、schema 映射、group split、泄漏审计和 gold 来源闭合。
