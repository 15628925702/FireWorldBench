# FireWorldBench Literature Audit S072

Audit date: `2026-07-16 Asia/Shanghai`.

## Outcome

- Existing collection: 16 PDFs focused primarily on physical reasoning, VLMs
  and world models.
- Supplement downloaded this session: 28 PDFs in four categories.
- Total collection: 44 PDFs, 394,630,350 bytes, 44 unique SHA-256 values.
- All 28 new PDFs pass `pdfinfo`; every first page rendered successfully and was
  visually inspected in a contact sheet.
- PDF binaries remain outside Git under
  `../../1.参考文献/FireWorldBench_补充文献_2026-07-16/`.
- Machine manifest: `literature_manifest_S072.json`.
- BibTeX registry: `references_fireworldbench.bib`.

## Coverage added

1. Foundational physical reasoning: IntPhys, PHYRE, CLEVRER, PIQA and Physion.
2. Fire datasets/benchmarks: Multi-Scene Fire/Smoke, Sen2Fire, FireRisk, GWFP,
   partial-observability wildfire forecasting, DetectiumFire, Fire360,
   FIgLib/SmokeyNet, Boreal Forest Fire and the PolyU tunnel database paper.
3. Fire reasoning methods: CausalPhys, QuantiPhy and World Models in Words.
4. Simulation: FD-Gen NIST TN 2332 and FDS 6.11.1 user, technical,
   verification and validation guides.
5. Governance: Datasheets for Datasets, Model Cards and two benchmark
   contamination works.

## Full-text gaps

- D01 paper DOI `10.1016/j.eswa.2023.122251`: publisher version is paywalled and
  no legal OA manuscript was located.
- D-Fire cited paper DOI `10.1007/s00521-022-07467-z`: publisher version is
  paywalled and the official institutional manuscript host was unreachable.

These records are present in the bibliography and manifest but are not marked
as downloaded. No unauthorized mirror was used.

## Interpretation boundary

The pack supports related work, dataset semantics, FDS/FD-Gen methodology,
benchmark design and contamination controls. It does not by itself grant data
training, test or redistribution rights, and it does not remove formal-run
input, split, leak, model, calibration, runtime or budget gates.
