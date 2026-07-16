# D01 complete ingestion and four-dimensional event model audit

This is a planning-only, research-only artifact. Raw files remain unchanged and are not promoted to the formal benchmark.

## Evidence-based result

D01 staging contains 192 FDS `*_devc.csv` files. Each file has 921 columns: a unit row, a sensor-name row, and a time series. The filename encodes six fire-source/lane combinations (`70/100/130` and `M/U`) and 32 extraction configurations. The staged files provide simulator state at sensor channels and a time axis; they do not provide a mesh, sensor coordinates, tunnel geometry, HRR, or continuous 3-D fields.

Therefore the model is four-dimensional only in the benchmark contract sense: case, time, available sensor channels, and physical variables. Its spatial capability is `Level_1_sensor_points_only`; unknown geometry is represented as `spatial_unknown`, never imputed.

## Outputs

- `artifacts/d01/d01_complete_manifest.json`: every raw file, size, SHA-256, source URL, upstream commit, acquisition evidence and redistribution gate.
- `artifacts/d01/d01_canonical_cases.json`: one canonical case per raw FDS output with explicit observed/unknown fields.
- `artifacts/d01/d01_prototype_samples.json`: five cases x T1/T2/T3, linked by `case_uid`; research-only and no formal gold.

The adapter records simulator values as `simulator_state`, not real-world ground truth. T1/T2/T3 labels are not asserted where the evidence is absent. No counterfactual pair is claimed: changing source location and extraction configuration simultaneously is a configuration comparison, not a single-variable counterfactual.

## Capability boundary

Supported now: reproducible case grouping, filename-derived fire-source/extraction identifiers, sensor-channel field dictionary, common t0, sampling interval, duration, raw references, provenance and deterministic prototype sample construction.

Not supported from D01 alone: full geometry/grid tensors, coordinate-aware fields, HRR labels, ventilation vectors, physically complete event phases, formal benchmark gold, public redistribution, or hidden-test material. FDS/FD-Gen regeneration would be required for a controlled spatial field or single-variable intervention; that work is intentionally not run in this round.
