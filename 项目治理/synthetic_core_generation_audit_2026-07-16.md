# FireWorldBench synthetic core generation audit

## Current status

`BLOCKED_FDS_RUNTIME`. The repository contains FD-Gen v1.0.0 (NIST software license) and its source/examples, but no FDS executable was found on `PATH`; Smokeview was also not found. The local FD-Gen snapshot and FDS version are not frozen in the approved generation plan, and the generation approval gates remain open.

This round therefore generated only six deterministic FDS input fixtures and a machine-readable case manifest. It did not run a simulator, produce slice/mesh/CSV/HDF5/NetCDF fields, or create simulator-derived gold. The fixture output is not a dataset and is not formal benchmark input.

## Fixture design

`configs/synthetic_core_v1.json` defines a small tunnel family with Cartesian geometry, 1 m mesh, 30 s duration, 1 s output interval, explicit fire source coordinates, HRR, ventilation, extraction, walls, open boundaries and two sensor layouts. It includes three baseline cases, one no-fire control, one degraded-observation case, and one extraction pair. The pair validator classifies the extraction pair as a strict `counterfactual` because all registered axes and the seed are identical except `extraction`; this remains a claim about the input design until FDS outputs are generated and validated.

`scripts/generate_synthetic_core.py` writes FDS inputs only. `scripts/validate_synthetic_core.py` checks bounds, unique case IDs and pair claims. Both are deterministic and retain provenance/config hashes.

## Required gate before physical generation

Install or authorize a versioned FDS runtime, record its executable SHA-256 and license/use scope, freeze the generation-plan hash and approved pilot count, then run FDS on the six fixtures. Only after successful field-shape, unit, sensor-projection, event-label and physical-constraint checks may the pilot expand to 100 cases. Generated fields must remain outside Git and be referenced by hashes/manifests.
