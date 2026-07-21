# FireWorldBench Model Card

状态：`NO_ACTIVE_MODEL_EXPERIMENT`

模型实验已按用户指令暂停。`openai/gpt-4o-mini` 的旧协议结果（S 57.50；I L1-3 68.94；
V unsupported）保留为 `legacy_protocol_calibration_evidence`，不能与新细粒度协议直接比较。

新协议要求：固定 exact model ID、实时 catalog metadata/hash、真实模态输入、严格 schema、
完整分母覆盖计分、raw response/failure 保存和成本上界。动态 alias、`openrouter/auto`、不稳定
`:free` alias、LLM judge 和字段自动修复均禁止。

文本、图像和视频套件可以使用不同模型；每个模型只对其明确参加的轨道负责。未参加轨道不计
missing，跨轨分数不得直接排序或平均。

在新 schema、challenge subset、scorer 和难度门禁验收前，不选择或调用任何模型。
