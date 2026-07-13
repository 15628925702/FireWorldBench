# 进度跟进与跨对话交接规范

本目录解决两个问题：当前到底做到哪里，以及下一次对话如何在不重做背景研究的情况下继续。

## 文件职责

- `CURRENT_STATUS.md`：可覆盖更新的唯一当前状态，不保留长篇历史。
- `YYYY-MM-DD_SNNN_<slug>.md`：每轮追加一份、完成后不回写的证据记录。
- `SESSION_HANDOFF_TEMPLATE.md`：会话记录模板与必填规则。
- `NEXT_SESSION_PROMPT.md`：已经填好的下一轮启动提示词，只包含一个主任务。
- `多窗口开发执行手册.md`：最省 token 的长期推进方法和阶段冻结点。
- `任务指令库_从P0到论文数据导出.md`：从源码基线到最终发布的逐任务指令。
- `窗口切换与中断恢复模板.md`：正常收尾、中断、异常恢复和阻塞提问话术。

## 会话编号和状态

- 编号：北京时间日期 + 当日三位序号，例如 `2026-07-14_S001`。
- 任务状态仅允许：`TODO`、`IN_PROGRESS`、`BLOCKED`、`DONE`、`SUPERSEDED`。
- `DONE` 必须满足 `开发要求约束/Definition_of_Done.md`。
- `IN_PROGRESS` 表示已有可继续工作；`BLOCKED` 只表示缺少外部决定/资源导致无法推进，不能用来代替“尚未做完”。

## 开始一轮对话

1. 读取 `AGENTS.md` 和 `CURRENT_STATUS.md`。
2. 读取最近会话记录、开放问题和关联设计/约束。
3. 检查 Git 状态，区分既有改动与本轮改动。
4. 立即从模板创建本轮 `IN_PROGRESS` 草稿，记录 branch、HEAD/UNBORN、remote、staged/unstaged/untracked、开始时间和既有改动。
5. 用一句话确认任务 ID、交付物和验收标准；若可合理推进则直接执行。

## 结束一轮对话

1. 完成实现和相称验证；不得留下仍在运行的必要进程。
2. 从模板新建会话记录，写清“实际完成/未完成/证据/风险/下一步”。
3. 更新 `CURRENT_STATUS.md`，只保留最新事实。
4. 更新 `NEXT_SESSION_PROMPT.md`，下一轮必须可直接复制启动。
5. 若没有通过验收，状态不得写 `DONE`。
6. 中断场景还必须使用 `窗口切换与中断恢复模板.md` 记录最后安全点、部分产物和运行进程。

## 提示词规则

- 必须使用绝对路径、任务 ID 和明确的“不要做”。
- 必须要求先读现状再改，保护用户已有改动。
- 必须给出可检查的完成标准，而不是“继续完善”。
- 一次只指定一个主任务；相关小步骤可列在同一任务包内。
- 禁止让下一轮自行读取 `4.升级拓展` 或扩大研究范围。
- `NEXT_SESSION_PROMPT.md` 只保存任务增量：任务 ID、目标、输入、交付物、门禁和第一动作；通用规则由 `AGENTS.md` 统一承担。

## 原子交接协议

三份交接文件必须共享同一个 `handoff_id`，且最终均为 `handoff_state: READY`。写入顺序固定：

1. 先完成本轮会话记录，写入 handoff ID、真实状态、证据和下一任务，状态设为 `READY`。
2. 再写 `NEXT_SESSION_PROMPT.md`，使用同一 ID/下一任务并设为 `READY`。
3. 最后更新 `CURRENT_STATUS.md`，切换唯一下一任务并设为 `READY`。
4. 运行 handoff 一致性检查；ID、状态、source session 或 task 任一不一致，新窗口必须进入恢复模式，不得开始任务。

由于 `CURRENT_STATUS.md` 最后写，前两步中断时当前任务不会被提前切走；只有三者完整一致时新窗口才可推进。

## 源码快照规则

- 会话基线必须记录 clean commit SHA；UNBORN/dirty 时额外记录 staged/unstaged diff 文件和 SHA-256、未跟踪文件 manifest/hash。
- 文件存在不等于可恢复；部分产物必须说明其父输入和验证证据。
- P3 正式构建及以后要求 clean commit。任何 dirty 正式 run 都必须 fail closed，除非 freeze 决策批准了不可变源码归档并记录其 hash。
