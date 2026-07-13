# P1-DATA-001 数据许可与用途资格审计

审计时间：`2026-07-14 Asia/Shanghai`。本地输入仅为仓库外只读目录 `../../3.数据集`；原始文件未修改。逐文件清单见 [`data_manifest_P1-DATA-001.json`](data_manifest_P1-DATA-001.json)，其 SHA-256 见 [`data_manifest_P1-DATA-001.json.sha256`](data_manifest_P1-DATA-001.json.sha256)。

## 清单结果

| ID | 本地文件数 | 总字节 | 版本/获取日期证据 | 官方许可证据 | 训练 | 开发 | 测试 | 派生发布 | 再分发 |
|---|---:|---:|---|---|---|---|---|---|---|
| D01 | 12 | 71,158,490 | 官方 GitHub URL 见 `_manifests/download_manifest.md`；版本、获取日期未记录 | 未发现 LICENSE/官方许可原文 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| D02 | 110 | 70,833,300 | 官方 GitHub URL；版本、获取日期未记录 | 未发现许可证原文；仓库含论文/实验整理表 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| D03 | 7 | 181,287 | 官方 GitHub URL；版本、获取日期未记录 | 未发现许可证原文 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| D04 | 50 | 85,736,781 | 官方 GitHub URL；版本、获取日期未记录 | [`04_FD-Gen/FD-Gen-main/LICENSE.md`](../../3.数据集/04_FD-Gen/FD-Gen-main/LICENSE.md) 为 NIST Software Licensing Statement；具体数据/结果再分发边界未单独确认 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| D05 | 8 | 643,012 | Kaggle metadata：version 1，2025-01-27；本地下载日期未记录 | `_manifests/D-Fire-kaggle-metadata.json` 声明 `CC0: Public Domain`；原始 D-Fire 与此 Kaggle 派生版本的权利链仍未核实 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| D06 | 103 | 14,316,777 | Kaggle metadata：version 6，2025-10-22；本地下载日期未记录 | `_manifests/DetectiumFire-kaggle-metadata.json` 声明 `CC BY-NC-ND 4.0` | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| D07 | 3 | 9,059,828 | 仅官方 poster/PDF 演示素材；无数据版本/获取日期 | 未发现数据许可证原文 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| D08 | 2 | 359,707 | 仅官方统计图；无数据版本/获取日期 | 未发现数据许可证原文 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| D09 | 4 | 1,333,120 | 官方分享清单记录于 `09_DFS-sample/official_share_inventory.json`；未下载原始归档 | 未发现许可证原文 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| D10 | 9 | 8,327,056 | 单序列抽样；版本、获取日期未记录 | 未发现许可证原文 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| D11 | 4 | 1,275,217 | 仅论文演示页图；无数据版本/获取日期 | 未发现许可证原文 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |

## 判定规则与结论

- `BLOCKED` 是故意的 fail-closed 结论：仅有来源 URL、论文引用、Kaggle 页面字段或本地样本，不能替代逐源官方许可和版本/获取证据。
- D07、D08、D09、D11 只有演示/统计/分享清单，不得转为训练、开发、测试、派生发布或再分发数据。
- D06 的 `CC BY-NC-ND 4.0` 至少阻断商业用途、衍生作品和未确认的再分发；本轮不作任何正向资格推断。
- D04 的软件许可证不自动授予其中生成结果、外部数据或本项目再分发权。
- D05 的 Kaggle 元数据声明不足以证明原始数据与全部图片的权利链，故所有用途仍 `BLOCKED`。

## 证据缺口

1. D01-D04、D07-D11：缺官方 LICENSE/terms 原文、不可变版本（tag/commit）和本地获取时间。
2. D05-D06：有平台元数据版本和许可证字段，但缺逐文件来源链、原始数据权利链和本地获取时间。
3. 本轮未安装、下载或访问新包/数据，也未执行远端 Git 写操作；官方网页核验未形成可用的本地证据，不能把网络推断写成 PASS。

## 审计证据

- 文件数与哈希：`项目治理/data_manifest_P1-DATA-001.json`。
- manifest 自身哈希：`d17133eb136301efda94bc80ece4d066ac142984c74a89d5550fa0acb32d774f`。
- 来源/下载记录：`../../3.数据集/_manifests/download_manifest.md`、`downloaded_files.tsv`。
- 平台版本/许可元数据：`../../3.数据集/_manifests/D-Fire-kaggle-metadata.json`、`DetectiumFire-kaggle-metadata.json`。
