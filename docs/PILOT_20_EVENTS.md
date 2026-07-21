# 20 Fire Event Pilot Plan

> Status: `LEGACY-PILOT-PLAN`. This plan does not authorize a new experiment
> after the 2026-07-21 user-directed task/metric redesign. Future pilot work must
> use `docs/FINE_GRAINED_TASK_METRIC_REDESIGN.md`, a vNext schema, a frozen
> challenge subset and the new support/difficulty gates.

状态：`PLANNED-NOT-GENERATED`。本文件不声称已生成任何 FDS event。

## 1. 目标

用 20 个独立 FDS Fire Events 验证运行成本、存储、标签稳定性、S/I/V 派生、困难负例和事件级 split，再决定是否扩展到约 180 events。

## 2. 最小场景矩阵

| Event class | Count | Purpose |
|---|---:|---|
| Fire events | 14 | 覆盖至少 2 种几何、4 个区域、3 档增长曲线和 3 类通风/排烟的代表组合 |
| No-fire normal | 2 | L1 困难负例与背景基线 |
| Ventilation disturbance | 2 | 无火条件下切换风机/开口 |
| Non-fire heat/smoke-like disturbance | 2 | 匹配亮度/烟量外观的困难负例 |
| Total | 20 | 每行均为独立 run/event，不是相邻切片 |

精确组合由 `configs/fds_prototype.yaml` 冻结。pilot 不追求覆盖正式 4 x 4 x 3 x 3 全因子。

## 3. 代表任务

- `L1-2`：S 当前窗口 + 4 个未来摘要；I 2-3 个前序帧 + 4 个下一帧候选。正例同一 event 的 `t+delta`；负例同几何/视角/时间跨度且烟量相近。
- `L2-1`：S 和 I，从统一 8 区域布局恢复 `source_region` 与 `stage`；阶段边界设缓冲区并排除歧义。
- `L3-3`：S 为 A/B 数值摘要；I 可在视觉差异可识别时加入。A/B 仅改变一个控制变量，几何、camera、seed、采样保持一致。

最低要求两个轨道。优先冻结 S + I；V 派生可用于成本验证，但不作为 pilot 通过的必需条件，除非配置明确升级。

## 4. 自动标签与稳定性

- L1-2：由同一事件未来时间和候选 provenance 确定。
- L2-1 source：由 FDS 配置区域确定；stage 由 HRR 曲线及变化率规则确定。
- L3-3：由未来轨迹直接比较；差异小于冻结阈值的 pair 进入 ambiguous。
- 对阈值上下扰动、时间采样和区域聚合方法执行稳定性分析；标签翻转率必须报告。

## 5. Split 建议

pilot 的目的不是论文估计量。先保留完整 counterfactual family，再以 `event_group` 分配建议的 `train=12/dev=4/test_iid=4`；实际分配需满足 family 不拆分。外部来源不进入该 20-event split。

## 6. Baseline

- L1-2：四选一 chance baseline 和最邻近趋势规则。
- L2-1：训练 split 的 source/stage majority，以及基于首响应传感器/HRR 斜率的规则。
- L3-3：三选一 chance/majority 和单变量方向规则。

baseline 只用于验证评分闭环，不宣称正式模型结果。

## 7. Pilot 验收报告

必须包含：

- 独立 events、QA、task、track、source、split 数量；
- 每 event wall/CPU time、峰值内存、原始 FDS 大小、S/I/V 派生大小；
- FDS 成功/失败/异常数值/渲染错误；
- Schema 通过率、跨 split 泄漏、标签泄漏、选项位置分布；
- 阶段边界率、区域并列率、反事实微小差异率、标签翻转率；
- 困难负例人工抽检与领域复核状态；
- 扩展到 180 events 的 CPU-hour 和存储区间估计，以及 go/no-go 决定。
