# 贡献规范

## 开始前

阅读 `AGENTS.md`，从 `进度跟进记录/CURRENT_STATUS.md` 领取唯一任务。若任务会改变任务定义、数据资格、划分、指标或论文主张，先提交决策记录，不得直接改实现。

## 分支与提交

- 分支建议：`feat/<task-id>-<slug>`、`fix/<task-id>-<slug>`、`docs/<task-id>-<slug>`。
- 提交标题：`<type>(<scope>): <task-id> <summary>`。
- 一个提交只承载一个可回退的逻辑变更；生成数据、模型权重和运行缓存不得进入 Git。
- 不使用真实来源文件名作为公开 case ID，不在提交信息中写密钥、个人路径或双盲身份。

## 合并前检查

```powershell
conda run -n fireworldbench-v1 python scripts/check_project.py
conda run -n fireworldbench-v1 python -m pytest
conda run -n fireworldbench-v1 python -m ruff check .
conda run -n fireworldbench-v1 python -m mypy src
```

变更还必须满足 `开发要求约束/Definition_of_Done.md`。任何跳过项都要在会话记录中给出原因、风险和补测任务，不能写成“暂时忽略”。
