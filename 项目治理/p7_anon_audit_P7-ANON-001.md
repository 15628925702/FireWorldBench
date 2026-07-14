# P7-ANON-001 audit

## Decision

The anonymous release audit is formally `BLOCKED_NO_EXPORT`. No paper export
root exists, so no anonymous package, public asset table, excluded asset table,
or third-party redistribution declaration can be accepted. The scanner only
accepts an explicit export root and does not sweep the repository history or
the external dataset directory.

## Leak gates

An explicit export root is scanned for author/username identity, absolute
paths, private URLs, secrets, Git metadata, test gold/private mappings, and
restricted third-party references. A clean text scan is insufficient without
an explicit license/source-version declaration; assets remain excluded until
that declaration is resolved. No test/private asset or external dataset file
was read or modified, and test access remains `NO_ACCESS_CONFIRMED`.
