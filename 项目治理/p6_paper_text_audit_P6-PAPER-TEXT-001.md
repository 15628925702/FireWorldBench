# P6-PAPER-TEXT-001 audit

## Decision

The manuscript number registry is formally `BLOCKED_NO_FROZEN_RESULTS`.
P5 has no frozen statistics with run IDs, so the registry contains no paper
result numbers, no fabricated percentage, confidence interval, p-value, cost,
or failure-rate value, and no `text_number_map.csv` is emitted.

## Number gates

The registry schema requires value, unit, run ID, metric, rounding, and
provenance for every future number. An explicit manuscript path can be scanned
for numeric tokens; every token is `UNMAPPED` until it is either mapped to a
frozen run/metric or entered in the provenance-backed non-result allowlist.
The gate rejects unmapped manuscript numbers and manual text copying.

Test access remains `NO_ACCESS_CONFIRMED`; no test/private asset or external
dataset file was read or modified.
