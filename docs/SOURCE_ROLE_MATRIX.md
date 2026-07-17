# Data Source Role Matrix

此矩阵按核心 PDF 冻结。`eligible` 必须同时满足可访问、版本、许可、字段和标签可靠性门禁。

| Domain | Role | Allowed tasks/tracks | Leaderboard | Prohibited |
|---|---|---|---|---|
| `fds` | 核心主数据、真值、反事实 | 全九任务；按充分性发布 S/I/V | Main + IID/OOD | 完整 4D 场作为常规 MLLM 输入 |
| `immersed_tunnel` | 外部 CFD 数值验证 | L1-1, L2-1, L3-1, L3-2, L3-3；S | External-CFD only | 假定有 RGB 视频；与 FDS CSV 随机混合 |
| `polyu` | 实验桥接 | L2-3, L3-1, 部分 L3-3；S | Experiment only | 从温度造 CO/soot/完整场标签 |
| `dfire` | 真实图像 OOD | L1-1 的 I；有限视觉风险分析 | Real-Image OOD only | 机制、趋势、反事实、精确物理状态 |
| `fire360` | 真实视频 OOD | L1-3 与可靠的有限 L2 视觉理解；V | Real-Video OOD only | 精确火源/HRR/CO/未来场标签 |
| `detectium` | 可选视觉补充 | 仅实际内容和标签支持的 I/V | External OOD only | 在许可或标签不明时计分 |

旧来源 `fds_exp`、`figlib`、MS-FSDB、DFS、Boreal 等未列入核心 PDF 的正式分工，不进入 v2 主数据或当前 pilot。未来若要加入，必须先获得用户设计变更授权，不能由工程实现自行扩展任务或来源。

每个 source record 至少包含：来源 URL、获取日期、精确版本/commit、逐文件哈希、许可证据、允许训练/评测/派生/再发布范围、引用、字段字典、可用标签和不允许推断的标签。
