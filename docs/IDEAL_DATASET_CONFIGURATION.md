# FireWorldBench Ideal Dataset Configuration

This document freezes the intended multi-source dataset layout. A substitute may count as
engineering evidence, but it must not be renamed as the target source or enter the FDS main leaderboard.

| Package | Ideal source | Intended role | FDS Main Overall |
|---|---|---|---|
| FWB-Core-FDS | NIST FDS + Smokeview + FD-Gen | authoritative physical events and S/I/V derivatives | yes |
| FWB-External-CFD | Immersed Tunnel CFD | external numerical transfer | no |
| FWB-Experiment | PolyUFire | experimental bridge | no |
| FWB-Real-Image-OOD | D-Fire | limited real-image OOD | no |
| FWB-Real-Video-OOD | Fire360 | real-video temporal OOD | no |
| FWB-Optional-Visual | DetectiumFire | optional visual supplement | no |

FURG, Kaggle, DeepQuest and other substitutes retain their own source names. Detectium and the incorrect
Fire360 mirror remain quarantined. FDS Core v3.3.1 remains the sole accepted formal package; this redesign
does not authorize downloading, migrating, extracting, cleaning, relabeling or promoting any dataset.

Every future package must retain immutable provenance, hashes, license state, field inventory, supported
tasks/tracks and exclusion reasons. Missing labels remain null. All external results remain outside FDS
Overall.
