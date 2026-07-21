# FireWorldBench v2 Finalization Acceptance

状态：`PAUSED_REDESIGN_NOT_ACCEPTED`

## Immutable evidence

- FDS Core v3.3.1：180/180 strict Events、4,039 QA，保持只读。
- 外部 formal Events/QA：0；现有 candidate/substitute/quarantine/gap 不变。
- 旧协议模型和 baseline 结果仅为历史难度证据。

## Redesign acceptance gates

- [ ] 用户确认 `FWB-FINEGRAIN-v1` 九任务与答案空间。
- [ ] QA/prediction schema vNext 冻结且不覆盖旧 schema。
- [ ] horizon/difficulty/violation/risk-driver/time-bin/pairing metadata 冻结。
- [ ] 新 semantic validators、scorer 和 focused/full tests 通过。
- [ ] challenge subset manifest、hash、support 和 event_group 泄漏审计通过。
- [ ] missing/malformed/schema-invalid 在完整分母中计 0。
- [ ] 每任务 support 满足排名门禁；不足任务标记 not ranked。
- [ ] 专家可回答性与代表模型难度校准通过。
- [ ] S/I/V 输入适配无伪模态；V 不可用时不生成分数。
- [ ] 成本和请求上界先于任何 API 调用冻结。

在以上项目完成前，不得宣布新 benchmark 设计完成，不得启动正式或 pilot 模型实验，也不得
把任何新结果写入 FDS Core v3.3.1 或正式主榜。
