# Current compatibility contract

Current prerelease: **0.1.0a5**, experimental alpha.

- event schema: `0.2`
- projection: `0.5`
- replay bundle: `0.1`
- operational specification: `0.1.2`
- diagnostic interface: `0.1`

The event envelope continues to separate invocation reservations and execution
outcome semantics from the audited alpha. Projection 0.5 adds history validity and
causal permission ambiguity and freezes nested state containers. Hash construction
algorithm and bundle container shape are unchanged, and events remain schema 0.2.

The 0.1.0a5 diagnostic interface is read-only. It adds no event types, does not alter
projection or replay semantics, and does not create new governance authority. A
`clear` diagnostic report is descriptive only and never substitutes for the final
`ExecutionBridge` re-authorization check.

Only this compatibility envelope is operationally supported. Old 0.1 events / 0.4
bundles are rejected rather than silently reinterpreted. No automatic migration is
provided. Keep historical data immutable and verify it using its pinned old SDK in
an isolated read-only workflow. Use a separate new database for the remediated
prerelease. Migration requires a separately reviewed explicit conversion preserving
lineage; never edit historical hashes or version headers to make import pass.

The frozen clean-room audit applies to **0.1.0a3 at
463ce26b8af7d52d38796888cf5717948df1e331**, verdict NOT YET. It is not overwritten by
new results. The 0.1.0a4 remediation evidence remains historical evidence for that
candidate; 0.1.0a5 adds a separate diagnostic surface and does not retroactively
change prior audit claims. A tagged release, live provider support, production
readiness and security certification are not implied.

Current software licensing is **Mozilla Public License 2.0 (MPL-2.0)**. Documentation,
specifications, diagrams, and research prose are licensed under **CC BY-SA 4.0** unless
a specific file or third-party notice states otherwise. Consult `LICENSE.md`,
`LICENSE-MPL-2.0.txt`, and `LICENSE-DOCUMENTATION.md` for controlling scope and terms.
