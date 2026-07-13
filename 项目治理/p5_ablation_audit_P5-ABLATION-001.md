# P5-ABLATION-001 audit

## Decision

The preregistered ablation structure is preserved, but execution is formally
`BLOCKED_NO_MAIN_RUN` because P5-MAIN-001 has no executable run index. No
ablation run, parameter difference, paired result, or performance claim is
fabricated.

## Factor isolation

The plan retains three one-factor-at-a-time factors: information budget,
evidence visibility, and uncertainty reporting. Every variant changes exactly
one declared factor. Any extra finding must be labelled exploratory and must
not enter the main hypothesis result.

Test access remains `NO_ACCESS_CONFIRMED`; no test/private asset or model test
result was read.
