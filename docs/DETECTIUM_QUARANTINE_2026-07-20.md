# Detectium Raw Quarantine

The local archive `raw/detectium/kaggle_detectiumfire/detectiumfire.zip` passed
an archive-integrity test on 2026-07-20. Its central directory, however,
contains `preference_dataset` and `synthetic_images/stable_diff_v15` trees.
This does not establish that it is the official DetectiumFire corpus, nor that
its labels, licensing, or image provenance support this benchmark.

Status: `QUARANTINED_WRONG_OR_UNVERIFIED_SOURCE`.

The archive is retained unchanged for forensic provenance. It must not be
extracted into formal assets or used for Events, QA, splits, reports, baselines,
or releases until official source identity, version, license, and annotation
semantics are independently verified.
