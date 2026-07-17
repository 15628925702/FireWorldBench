---
handoff_id: H-20260717-V2-ALIGN-001
handoff_state: READY
source_session: 2026-07-17_V2方案对齐与第一阶段重构.md
current_task: V2-A2-PILOT-PREP
---

# Next Session: 20-event Pilot Preparation

Read `AGENTS.md`, `PROJECT_CHARTER.md`, `docs/ARCHITECTURE_FREEZE.md`, `docs/PILOT_20_EVENTS.md`, and this handoff's source session.

First actions:

1. Detect local FDS, Smokeview, and FD-Gen executables and record exact versions without downloading or executing simulations.
2. Resolve or explicitly keep blocked the version, mesh, boundary, and exact 20-event matrix fields in `configs/fds_prototype.v2.json`.
3. Implement a dry-run manifest that proves 20 independent events and counterfactual family grouping before any run.
4. Implement representative task builders in order: L1-2, L2-1, L3-3, with S + I preferred.
5. Add candidate position, filename/path leakage, time matching, and external-domain exclusion tests.

Do not run 180 events, download large data, run model APIs, train models, add tasks, or reintroduce old T1/T2/T3/tool-agent definitions.
