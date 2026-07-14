# P5-MAIN-RUN

主实验门禁审计结果为 `BLOCKED_NO_APPROVED_MAIN_INPUTS`。当前没有批准模型矩阵、冻结校准 manifest、可复现 runtime、paper-ready 输入 manifest 或 run index；因此没有启动 batch harness，没有生成模型输出、成本、时延、失败率或论文数字。

本轮未读取 test/private 资产，未运行模型，未下载/安装依赖，也未把 11 个 planning candidate cases 直接变成正式输入。只有完成模型批准、train/dev 校准、来源资格、schema/group split/leak audit 和输入 hash 后，才能启动 main run。
