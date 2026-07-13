# P6-PAPER-FIGURES-001 audit

## Decision

Figure export is formally `BLOCKED_NO_FIGURE_SOURCE`. No frozen result source
exists, so no figure data, plotting script, PDF, PNG, or caption fact is
generated. No points or values are hand-edited.

## Future render gate

Future figures must use the same frozen result source as tables, retain source
SHA-256 and plot specs, require vector output or at least 300 DPI raster output,
and map every caption fact to provenance. Test access remains
`NO_ACCESS_CONFIRMED`.
