# P5-FINAL-CALIBRATION-001 audit

## Decision

Final calibration is formally `BLOCKED`. There is no paper-ready benchmark
addendum with approved train/dev inputs, no approved model ID/configuration,
and no approved calibration runtime. No checkpoint, prompt adaptation,
threshold fit, or calibration score is fabricated.

## Frozen boundary

- The model set and primary metrics are unchanged from the P4 freeze.
- Only train/dev manifests are accepted; test split or protected path inputs are refused.
- The selection log, checkpoint manifest, prompt hashes, and calibration results
  remain empty until the required approvals and inputs exist.
- The sealed run plan points back to `P4-PILOT-FREEZE-001` and forbids test-based selection.
- Test access ledger is `NO_ACCESS_CONFIRMED`.

## Gate to calibration

Provide a complete paper-ready train/dev manifest, approved model IDs and
configuration, and a reproducible runtime. Then run calibration under the
frozen P4 protocol and record all choices before any test access.
