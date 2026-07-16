# Source and License Evidence Supplement S072

Audit date: `2026-07-16 Asia/Shanghai`.

This supplement updates evidence precision without promoting any source to
`formal_benchmark_eligible=true`. Downloaded papers are citation evidence, not
dataset-license evidence.

## Verified upstream heads

| ID | Official source | Verified remote head |
|---|---|---|
| D01 | `babeteax/Immersed-Tunnel-Fire-Location-Detection-Data` | `00a81959b792fe013e2ac0468758b5fbedf3e68f` |
| D02 | `PolyUFire/Tunnel_Fire_Database` | `07a70c1540a7b797c049541209bb9120ea45d8bb` |
| D03 | `firemodels/exp` | `39d8b735870826430a69cfb95681db67cfd36bbf` |
| D04 | `usnistgov/FD-Gen` | `428a4153239efa9c4c4b6b20670990c52eaf926a` |
| D05 | `gaia-solutions-on-demand/DFireDataset` | `4bf9c31b18fadcd44d5f0b6d66f82bc56fa5e328` |

The heads above describe the official remotes observed on the audit date. They
do not prove that every local staging file is byte-identical to that commit;
local exact-snapshot matching remains pending where stated in
`configs/data_sources.toml`.

## License and use evidence

| ID | Evidence | Conclusion |
|---|---|---|
| D01 | No LICENSE/COPYING file found at the verified head; supporting paper DOI `10.1016/j.eswa.2023.122251` is paywalled | Data-use and redistribution remain `BLOCKED` |
| D02 | No LICENSE/COPYING file found at the verified head; institutional OA paper DOI `10.1016/j.tust.2020.103691` downloaded | Paper supports provenance/semantics, but data-use and redistribution remain `BLOCKED` |
| D03 | Commit-pinned NIST `LICENSE.md` permits use/copy/distribution of NIST-developed software | Repository data applicability is not explicit; formal data eligibility remains blocked pending scope review |
| D04 | Commit-pinned NIST software license plus NIST TN 2332 | FD-Gen software use is supported; generated-output eligibility depends on approved inputs, runtime and release scope |
| D05 | Official repository `LICENSE` applies CC0 1.0 to the D-Fire collection while expressly disclaiming clearance of third-party rights | Local research use has stronger evidence; public image redistribution remains subject to provenance/privacy review |
| D10 | Official HPWREN page states public availability and requires credit in derivative work | Local research use with attribution has evidence; independent redistribution terms remain unspecified |

## Local evidence snapshots outside Git

Stored under
`../../1.参考文献/FireWorldBench_补充文献_2026-07-16/05_许可与来源证据/`.

| File | SHA-256 |
|---|---|
| `D01_README_00a81959.md` | `8dc853b0d51a16d7b93f1e85c08256c53b88a0d63cd22af2cff3a304725996c3` |
| `D02_README_07a70c15.md` | `842ef4820119b63287fefdcc2209cde8b626d8b0ce506f4ee96568e49bb195f4` |
| `D03_LICENSE_39d8b735.md` | `38c542304b97afc4171a9b67866499eaf222509cab45c095ea69bf88d57755b7` |
| `D04_LICENSE_428a4153.md` | `777060f35baa90ababb6d4336f7e96c6a9d78f8c23fd136cb7b0bf1cd7e8cf9f` |
| `D04_README_428a4153.md` | `2865d93241fdba76ff403ee13cdf490a91c5a3b9802dc9b7808a4aceea1736c2` |
| `D05_LICENSE_4bf9c31b.txt` | `4620dc6794449f067b4b663a6d680e865191ba5057941a9e609b4c6bdd41205a` |
| `D05_README_4bf9c31b.md` | `c5395ce455e05f2b617c8c6de8193c143695b069c8d2dfa4367678c403741218` |
| `D10_HPWREN_FIgLib_terms_2026-07-16.html` | `ff150d6a0aff4bfea71bfe8e393feb52ef510418dd63573f12197f6eb8970b4f` |

## Remaining actions

1. Obtain explicit data-use/benchmark permission or an authoritative license
   from D01 and D02 maintainers.
2. Confirm whether D03's repository license applies to experimental data files,
   not only software.
3. Decide whether D05/D10 will be referenced remotely or redistributed; remote
   reference is safer until third-party/provenance review closes.
4. Do not promote any raw source file to the paper-ready formal input manifest
   based solely on this supplement.
