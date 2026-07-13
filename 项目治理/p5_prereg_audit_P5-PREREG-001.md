# P5-PREREG-001 audit

## Decision

The preregistration plan is frozen as a machine-readable contract, but its
execution status is `BLOCKED_PENDING_APPROVAL` because the model slots and
paper-ready data inputs remain unavailable. The plan freezes hypotheses,
primary/secondary metrics, statistical families, model/track matrix,
ablations, repetitions, exclusions, stopping rules, and post-freeze changes.

## Test embargo

The access ledger is `NO_ACCESS_CONFIRMED`. Test input, test gold, and private
mapping are all explicitly false. Future test scoring requires an isolated
custodian path; ordinary development and model runners must not access those
assets.

No test-based model, prompt, threshold, or track selection is allowed. Any
change after this freeze requires a new preregistration version and an
exploratory label.
