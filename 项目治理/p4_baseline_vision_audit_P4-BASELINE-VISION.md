# P4-BASELINE-VISION audit

## Decision

The visual baseline is formally `N/A`. No approved visual dataset, region-level
annotations, interference annotation protocol, or reproducible visual runtime
is available in the current project boundary. No visual score is fabricated.

The implementation keeps detection metrics separate from physical-reasoning
metrics. Both are `null` until the required resources are approved and frozen.
Region and interference slices are empty for the same reason.

## Boundary

- Only explicit `train_id` and `dev_id` samples are accepted.
- `test_id` samples and protected path components are refused.
- The implementation does not inspect or modify `../../3.数据集`.
- No test input, test gold, private mapping, or visual asset is read.

## Resource gaps

1. Approved visual dataset and provenance.
2. Region annotations and physical-object grounding labels.
3. Interference slice definition and annotation protocol.
4. Frozen visual baseline runtime and reproducible environment.

Until these gaps are closed, reports must state `N/A` and must not interpret it
as zero accuracy. Visual detection accuracy must not be presented as physical
reasoning accuracy.
