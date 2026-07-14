# P7-REPRO-001 audit

## Decision

Clean-room reproduction is formally `BLOCKED_NO_RELEASE_INPUT`. No legal
paper release root or release README is available, so no new environment was
created, no package was installed or downloaded, and no benchmark, baseline,
or paper-number registry was rebuilt. Reproduction hashes and deviations stay
empty rather than being inferred from the development checkout.

## Reproduction gate

When a release root exists, the audit requires a README hash, a clean
environment lock, legal inputs, rebuild logs for all three targets, hashes,
and an explicit deviation report. Test/private assets and the external
dataset remain outside the reproduction input boundary; test access remains
`NO_ACCESS_CONFIRMED`.
