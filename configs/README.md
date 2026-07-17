# Configuration Status

`tasks.v2.json`、`sources.v2.json`、`splits.v2.json`、`evaluation.v2.json` 和 `fds_prototype.v2.json` 是当前 v2 配置。

其余配置属于旧 T1/T2/T3 P0-P7 实现，状态为 `LEGACY-NONCOMPARABLE`。旧 CLI 可读取它们做历史审计，但新 `fireworld` 代码不得隐式回退到这些文件。
