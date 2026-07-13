# P6-PAPER-TABLES-001 audit

## Decision

Paper-table export is formally `BLOCKED_NO_FROZEN_RESULTS`. The P5 result
freeze manifest contains no run IDs, result hashes, or raw prediction hashes.
No CSV, JSON, or LaTeX metric table is generated, and no number is copied from
chat or manually edited.

## Future export gate

When frozen result files exist, the exporter must trace every cell to sample
scores/raw runs through a run-metric mapping and retain the source SHA-256.
Main and appendix table specs must come from the same result source.

Test access remains `NO_ACCESS_CONFIRMED`; no test/private asset was read.
