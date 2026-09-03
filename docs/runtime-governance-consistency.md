# Runtime governance consistency

TRIA Runtime must evaluate execution against the governance engine attached to the `Relationship` being executed.

A relationship may be constructed with caller-supplied governance behavior. Runtime must not silently replace that behavior with a fresh default `GovernanceEngine`, because doing so would create two governance realities for the same relationship.

Lifecycle outcomes also retain their meaning in the invocation audit trail:

- `ALLOW` may proceed to the remaining authorization checks.
- `PAUSE` records `InvocationResolved.status = "PAUSED"`.
- other non-allow lifecycle outcomes record `InvocationResolved.status = "BLOCKED"`.

`PAUSE` and `BLOCK` are intentionally distinct. A paused relationship is not equivalent to a prohibited or dissolved relationship; it represents an operational state in which execution should wait without erasing the possibility of continuation.

This build changes no event schema, projection version, or bundle format. It aligns Runtime with governance semantics already present in Core.
