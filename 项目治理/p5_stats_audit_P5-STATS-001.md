# P5-STATS-001 audit

## Decision

Statistics are formally `BLOCKED_NO_RAW_OUTPUT`. No immutable raw prediction
file exists because the main matrix did not run. Therefore no sample/case/pair
score, confidence interval, effect size, multiple-comparison result, cost, or
failure metric is produced.

## Contract

When raw outputs exist, scoring must recompute all fields from the raw file and
record its SHA-256. The report retains sample, case, and pair units; 95% CI,
effect size, multiple-comparison, cost, and failure fields are separate. Manual
metric edits are forbidden.

Test access remains `NO_ACCESS_CONFIRMED`; no test/private asset was read.
