# P1-PLANNING 数据下载预研与本地 staging 审计

审计时间：`2026-07-14 Asia/Shanghai`。

本轮目标是为后续 pipeline 预研确认本地 `data/raw` staging 输入、生成逐文件 SHA-256 manifest，并保持许可证与再分发状态 fail-closed。本轮未完成最终许可证核验，未产生训练/开发/测试资格，未产生任何模型实验结果。

## 结果摘要

| ID | 状态 | 文件数 | 总字节 | manifest | 与既有 P1 manifest 比对 |
|---|---|---:|---:|---|---|
| D01 | ALREADY_PRESENT | 12 | 71,158,490 | `项目治理/download_manifest_D01_planning.json` | MATCHED_BY_FILENAME_SIZE_SHA256 |
| D02 | ALREADY_PRESENT | 110 | 70,833,300 | `项目治理/download_manifest_D02_planning.json` | MATCHED_BY_FILENAME_SIZE_SHA256 |
| D03 | ALREADY_PRESENT | 7 | 181,287 | `项目治理/download_manifest_D03_planning.json` | MATCHED_BY_FILENAME_SIZE_SHA256 |
| D04 | ALREADY_PRESENT | 50 | 85,736,781 | `项目治理/download_manifest_D04_planning.json` | MATCHED_BY_FILENAME_SIZE_SHA256 |
| D05 | ALREADY_PRESENT | 8 | 643,012 | `项目治理/download_manifest_D05_planning.json` | MATCHED_BY_FILENAME_SIZE_SHA256 |
| D10 | ALREADY_PRESENT | 9 | 8,327,056 | `项目治理/download_manifest_D10_planning.json` | MATCHED_BY_FILENAME_SIZE_SHA256 |
| D06 | NOT_DOWNLOADED_BY_INSTRUCTION | 0 | 0 | N/A | N/A |
| D07 | NOT_DOWNLOADED_BY_INSTRUCTION | 0 | 0 | N/A | N/A |
| D08 | NOT_DOWNLOADED_BY_INSTRUCTION | 0 | 0 | N/A | N/A |
| D09 | NOT_DOWNLOADED_BY_INSTRUCTION | 0 | 0 | N/A | N/A |
| D11 | NOT_DOWNLOADED_BY_INSTRUCTION | 0 | 0 | N/A | N/A |

总登记见 `项目治理/download_staging_registry_P1-PLANNING.json`。

## 许可与用途边界

- 所有成功 staging 的数据集均保持 `license_status = UNKNOWN`、`redistribution_status = UNKNOWN`、`formal_benchmark_eligible = false`。
- 未把任何数据标记为正式可训练、可测试或可再分发；`configs/data_sources.toml` 中 `eligible = false` 保持不变。
- D05 仅作为视觉辅助预研数据，不作为正式 benchmark 结果来源。
- D10 仅作为野外火灾视觉 OOD 辅助预研数据；官方来源尚未在本轮闭合，source URL 保留 `UNKNOWN_OFFICIAL_SOURCE_NOT_REVERIFIED`。
- D06 因全量规模约 95GB 以上且许可/再分发范围不清楚，按指令不下载。
- D07/D08/D09/D11 按指令不下载，不作为正式数据集。

## 原始文件保护

- staging 文件位于 `data/raw/...`，原始文件未删除、清洗、重采样、改名覆盖或修改。
- 仓库外只读目录 `../../3.数据集` 未修改。
- 未读取或使用 `../../4.升级拓展`。
- 原始 staging 数据由 `.gitignore` 的 `data/raw/**` 排除，本轮提交只应包含 manifest、配置与审计记录。

## 生成与检查命令

- 数据目录文件清单：`Get-ChildItem data/raw -Recurse -File`
- 逐文件 SHA-256：manifest 生成脚本对每个 staging 文件执行 SHA-256。
- 既有 manifest 比对：按文件名、大小、SHA-256 与 `项目治理/data_manifest_P1-DATA-001.json` 比对；未发现不一致。
- 后续验证命令在会话交付记录中登记。

