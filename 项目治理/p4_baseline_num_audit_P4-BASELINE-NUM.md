# P4-BASELINE-NUM 数值与时间序列 baseline 审计

日期：2026-07-14  
任务状态：DONE_WITH_BLOCKED_EXTERNAL_DATA

## 实现内容

- `src/fireworldbench/baseline.py` 提供 seeded chance、train-only majority、domain threshold、traditional ML 接口和预注册 temporal persistence baseline。
- 所有 baseline 统一输出 prediction、config hash、seed、失败记录和 `test_tuning=false`。
- test split 直接拒绝；majority 不读取 test label；threshold 只接受 train/calibration 来源；temporal baseline 不根据 test 表现改规则。
- CLI 新增 `fwb baseline-run --strategy ...`。

## 边界与验证

本轮未读取 test input/gold/private mapping，没有修改 `../../3.数据集`，没有模型排名或正式 test 结果。seed 确定性、majority train-only、temporal persistence 和 test split 拒绝测试通过。

下一任务：`P4-BASELINE-VISION`。
