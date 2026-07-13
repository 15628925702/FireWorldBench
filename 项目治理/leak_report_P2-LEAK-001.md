# P2-LEAK-001 匿名 ID 与泄漏审计

审计时间：`2026-07-14 Asia/Shanghai`。本轮使用 P1 manifest、P2 split groups、P2 v2 Schema 和公开 payload validator；未修改 `../../3.数据集`，未生成私有 salt 或 reverse mapping。

## 1. Opaque ID 策略

- 公开格式：`FWB-{benchmark_version}-{task}-{split}-{opaque_id}`。
- `opaque_id`：HMAC-SHA256 截断 16 位；输入包含私有 case key，密钥来自 `FWB_PRIVATE_ID_SALT` secret store/environment。
- 私有 salt、source case key、reverse mapping、gold 和 scoring metadata 永不进入公开 payload、模型上下文或仓库。
- 正常开发环境没有 salt，因此生成真实 ID 的命令会明确输出 `BLOCKED`，避免误生成可逆映射。

## 2. 扫描结果

| 检查 | 结果 | 处置 |
|---|---|---|
| 精确 SHA-256 重复 | P1 manifest 中发现 1 组：`04_FD-Gen/example_preview.png` 与 `04_FD-Gen/FD-Gen-main/images/Picture1.png` | 认定为同一演示图副本；两者都不进入 benchmark 数据 |
| 感知重复 | `BLOCKED/NOT_RUN` | 当前未获批准的图像解码/感知 hash 依赖；P2-FREEZE 前必须在授权环境补跑 |
| D10 邻帧/序列 | 已由 split group 规则按 sequence/stem 绑定 | 不允许相邻帧跨 split |
| D01 family | 由 `split_groups_P2-SPLIT-001.json` 按位置+车道绑定 | 不允许同 family 跨 split |
| D04 template/generator | D04 仅 generator/template inventory，无正式生成结果 | template/project/seed family 必须整体隔离 |
| 原始文件名/路径 | release scanner 拒绝原始 source token、绝对路径和路径样式 | 使用 opaque public ID 和 package-relative content ref |
| 私有 prediction 字段 | scanner 拒绝 `gold`、`gold_ref`、`physical_trace`、`scoring_metadata`、`source_case_key` 等 | prediction 只允许公开答案、evidence、uncertainty、missing_information |
| 元数据答案词 | scanner 拒绝 `70U01`、`130M08`、source 名称等已知答案键 | 正式 release 前执行 fail-closed 扫描 |

## 3. Split 与泄漏关系

- group-first 已在 P2-SPLIT-001 完成：先按 case/family/sequence/template，再切窗。
- sample ID 不承载 raw source case key；source/family/template 只保存在私有 mapping 或审核 manifest。
- 测试 gold/scoring metadata 不能进入 prediction，也不能进入公开 sample payload。
- `P1` 许可门禁仍然有效；本轮泄漏扫描通过不等于数据获得训练或发布授权。

## 4. 失败闭合规则

- 任意一个公开 ID 不是 opaque 格式：`FAIL`。
- 任意一个公开 payload 含私有字段、原始 source token、绝对路径或可直接答案的文件名：`FAIL`。
- 感知重复未执行：不能标记“重复为零”，正式 freeze 保持 `BLOCKED`。
- 任何 group/family/sequence 交集非零：`FAIL`，不得继续切窗或评测。

## 5. 后续要求

1. 在获授权环境补充图像感知 hash，并与精确 hash/sequence stem 合并。
2. P2-EVAL-001 只接受 opaque sample IDs 和公开 prediction Schema。
3. P2-FREEZE-001 前保留无访问确认、private mapping 位置和 release scan 日志；不把私有映射放入 Git。

下一任务：`P2-EVAL-001`。
