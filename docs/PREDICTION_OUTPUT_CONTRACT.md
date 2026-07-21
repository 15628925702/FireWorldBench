# Prediction Output Contract v2

The machine authority is configs/prediction_contract.v2.json. The runner records
its SHA-256 in every run manifest. A run must fail closed if this file disagrees
with src/fireworld/contracts.py.

## Response boundary

The model returns exactly choice, fields, confidence, and evidence.
The runner binds schema_version, qa_id, and task_id from the frozen public QA
input. It never asks the model to invent identity or provenance fields and never
rewrites answer values.

| Task | Required fields | Allowed values |
| --- | --- | --- |
| L1-1 | class | fire, no_fire, ventilation_disturbance, sensor_fault |
| L1-2 | choice | A, B, C, D; answer.choice equals fields.choice |
| L1-3 | consistency, violation_type | consistent/inconsistent; frozen violation enum or null |
| L2-1 | source_region, stage | R1-R8; incipient, growth, developed, decay |
| L2-2 | risk_region, risk_level | R1-R8; low, moderate, high, critical |
| L2-3 | mechanism | six frozen mechanism labels |
| L3-1 | three trend fields | up, stable, down |
| L3-2 | first_high_risk_region | R1-R8, none |
| L3-3 | comparison | A, B, same |

## Mandatory gates

1. Validate the contract file against all nine active task definitions.
2. Run schema, semantic, scorer, and model-runner contract tests.
3. Run one public S-track item per task with the fixed model and seed.
4. Require 9/9 valid predictions and zero failures before a full run.
5. Save raw responses and checkpoint every 25 processed items.
6. Reject missing, extra, aliased, out-of-enum, or cross-field-inconsistent output.
7. Do not use failed predictions, automatic answer rewriting, or an LLM judge in
   leaderboard results.