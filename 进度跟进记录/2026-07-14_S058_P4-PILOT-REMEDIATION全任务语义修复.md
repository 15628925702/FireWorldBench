---
handoff_id: H-20260714-S058-001
handoff_state: READY
task_status: READY
session_id: 2026-07-14_S058
task_id: P4-PILOT-REMEDIATION
next_task: P5-MAIN-RUN
started_at: 2026-07-14 Asia/Shanghai
---

# P4-PILOT-REMEDIATION

## Objective

Repair the five small-N pilot gaps found in the full planning smoke test: interactive T1-C, documented state/mechanism rules, trace abstention contract, and a verified D01 single-variable pair. Re-run the same four-case split without increasing scale.

## Completion

- Rebuilt the same four-source-case, group-first split into 51 dev and 48 train samples using early/middle/late windows.
- Repaired T1-C query visibility, T2 state/mechanism boundaries, T3-C trace abstention, and valid D01 location pairs for T3-B.
- Initial DeepSeek batch had 10 transient network failures; a single targeted resume recovered all 10. The original failures and a duplicate checkpoint batch are retained in the accounting report.
- Final scored metrics: T1-A 0.167, T1-B 0.500, T1-C 0.825, T2-A 0.833, T2-B 1.000, T2-C 1.000, T3-A 0.333, T3-B 1.000, T3-C 1.000.
- The result proves end-to-end engineering readiness; D01-only planning labels and early-window/T3-A errors still prevent scientific scale-up claims.
- Next task: `P5-MAIN-RUN` planning-scale readiness decision.
