# P6-EXPORT-001 audit

## Decision

The paper export is formally `BLOCKED_NO_FROZEN_RESULTS`. No approved frozen
run, complete result provenance, or paper-ready table/figure/text source is
available. Therefore no public or private root, release ID, manifest,
checksum file, or reconstructed paper package is generated.

## Export contract

The implementation freezes two independent roots with independent manifests
and checksums. `manifest.json` is excluded from its own hash entry, while the
checksums file covers the manifest and every other file in that root. The
public leak gate rejects private roots, test gold, private identity mappings,
restricted references, secrets, and absolute paths. Any repair must use a new
release ID and must not overwrite an older export.

Test access remains `NO_ACCESS_CONFIRMED`; no test/private asset or external
dataset file was read or modified.
