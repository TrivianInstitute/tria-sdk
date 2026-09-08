# Current compatibility contract

Current prerelease: **0.1.0a4**, experimental alpha.

- event schema: `0.2`
- projection: `0.5`
- replay bundle: `0.1`
- operational specification: `0.1.2`

The new event envelope explicitly separates invocation reservations and execution
outcome semantics from the audited alpha. Projection 0.5 adds history validity and
causal permission ambiguity and freezes nested state containers. Hash construction
algorithm and bundle container shape are unchanged, but new events use schema 0.2.

Only this envelope is operationally supported. Old 0.1 events / 0.4 bundles are
rejected rather than silently reinterpreted. No automatic migration is provided.
Keep historical data immutable and verify it using its pinned old SDK in an isolated
read-only workflow. Use a separate new database for the remediated prerelease.
Migration requires a separately reviewed explicit conversion preserving lineage;
never edit historical hashes or version headers to make import pass.

The frozen clean-room audit applies to **0.1.0a3 at
463ce26b8af7d52d38796888cf5717948df1e331**, verdict NOT YET. It is not overwritten by
new results. Current validation applies only to the separately recorded remediation
commit. A tagged release, live provider support, production readiness and security
certification are not implied. The current license remains PolyForm Noncommercial
1.0.0 with separate commercial licensing; this remediation does not relicense TRIA.
