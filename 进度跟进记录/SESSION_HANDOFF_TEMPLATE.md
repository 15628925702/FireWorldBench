---
handoff_id: {{H-YYYYMMDD-SNNN-NNN}}
handoff_state: {{WORKING|READY}}
session_id: {{YYYY-MM-DD_SNNN}}
task_id: {{TASK_ID}}
next_task: {{NEXT_TASK_ID_OR_TBD}}
---

# {{DATE}}_{{SESSION_ID}}_{{SLUG}}

> 完成后移除所有 `{{...}}` 占位符。记录一旦交接即视为追加式证据；事实变化写新记录，不回写旧记录。

## 1. 会话元数据

- 任务 ID：`{{TASK_ID}}`
- 状态：`{{TODO|IN_PROGRESS|BLOCKED|DONE|SUPERSEDED}}`
- 开始/结束：`{{ISO_DATETIME_WITH_TIMEZONE}}`
- 执行者：`{{HUMAN_OR_AGENT}}`
- Git branch：`{{BRANCH}}`
- Git HEAD：`{{COMMIT_OR_UNBORN}}`
- Git remote：`{{FETCH_AND_PUSH_URLS}}`
- 基线快照时间：`{{ISO_DATETIME_WITH_TIMEZONE}}`
- 基线 staged/unstaged/untracked：`{{COUNTS_AND_PATHS}}`
- 结束 staged/unstaged/untracked：`{{COUNTS_AND_PATHS}}`
- 工作区既有改动：`{{PATHS_AND_KNOWN_OR_UNKNOWN_OWNERSHIP}}`
- 源码基线 ID：`{{CLEAN_COMMIT_OR_SOURCE_ARCHIVE_SHA256}}`
- staged/unstaged diff：`{{PATCH_PATHS_AND_SHA256_OR_NONE}}`
- 未跟踪文件 manifest：`{{PATH_AND_SHA256_OR_NONE}}`

## 2. 目标与验收

- 本轮目标：{{ONE_SENTENCE_GOAL}}
- 明确不做：{{OUT_OF_SCOPE}}
- 验收标准：
  - [{{PASS|FAIL|NOT_RUN|BLOCKED}}] {{ACCEPTANCE_1}}：{{EVIDENCE}}
  - [{{PASS|FAIL|NOT_RUN|BLOCKED}}] {{ACCEPTANCE_2}}：{{EVIDENCE}}

## 3. 输入与依据

- 必读文件：{{FILES}}
- 数据/配置版本：{{MANIFEST_AND_HASH}}
- 决策/需求 ID：{{DECISION_AND_REQUIREMENT_IDS}}
- 关键假设：{{ASSUMPTIONS}}

## 4. 实际完成

只写已经落地且可核验的内容：

- {{CHANGE_WITH_PATH}}

## 5. 未完成与偏差

- {{ITEM_OR_NONE}}
- 原因：{{ROOT_CAUSE}}
- 影响：{{IMPACT}}

## 6. 验证证据

| 状态 | 时间 | 执行环境/版本 | 命令/检查 | 退出码 | 关键结果 | 证据路径 |
|---|---|---|---|---:|---|---|
| `{{PASS|FAIL|NOT_RUN|BLOCKED}}` | {{TIME}} | {{ENV_AND_VERSION}} | `{{COMMAND}}` | `{{CODE_OR_NA}}` | {{RESULT}} | `{{PATH_OR_NA}}` |

未运行的检查及原因：{{NOT_RUN_AND_REASON_OR_NONE}}

## 7. 变更清单

- 新增：{{FILES}}
- 修改：{{FILES}}
- 删除：{{FILES_OR_NONE}}
- 生成但不进 Git：{{ARTIFACTS_OR_NONE}}

## 8. 运行中进程与部分产物

- 运行中命令/PID/session：{{NONE_OR_DETAILS}}
- 最后安全点：{{LAST_REPRODUCIBLE_STEP}}
- 可复用部分产物：{{PATHS_AND_WHY_TRUSTED}}
- 不完整/不可信产物：{{PATHS_AND_DELETE_OR_REBUILD_ACTION}}

## 9. 决策、风险和问题

- 新/更新决策：{{D_IDS_OR_NONE}}
- 新/更新风险：{{R_IDS_OR_NONE}}
- 新/更新开放问题：{{Q_IDS_OR_NONE}}
- 需要用户决定：{{EXACT_QUESTION_OR_NONE}}

## 10. 下一轮交接

- 唯一下一任务：`{{NEXT_TASK_ID}} - {{NEXT_TASK}}`
- 第一条命令/动作：{{FIRST_ACTION}}
- 必须复用：{{REUSABLE_OUTPUTS}}
- 禁止重复/禁止做：{{DO_NOT_REPEAT_OR_EXPAND}}
- 完成标准：{{NEXT_ACCEPTANCE}}
