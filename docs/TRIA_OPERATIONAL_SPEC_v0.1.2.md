# TRIA operational specification 0.1.2

This is the current operational contract for 0.1.0a5. The conceptual
TRIA_CORE_SPEC_v0.1.1.md remains the historical pre-implementation baseline;
implementation behavior is governed by this specification and linked contracts.
The read-only Diagnostic Interface v0.1 adds inspection capability without changing
these governance semantics or creating new authority.

A relationship must have one valid created root, nonempty unique participants,
a valid hash chain and a supported event schema before Runtime authorizes.
Nonparticipant requesters fail closed. Host-held administration authenticates and
binds identities outside the SDK; actor labels alone are not credentials.

Causal permission ambiguity is a derived projection field consumed by the shared
GovernanceEngine, including direct composition. Custom restrictions cannot remove
core capability, consent or runtime floors. Caller-fabricated state is trusted
infrastructure, not authenticated proof of authority.

Consequential execution is governed at the final local handoff after preparation,
under the shared store guard. The original request's requirements must still allow.
An invocation reservation is durable intent and does not assert entry or completion.
A reused reservation is rejected; missing result means reconcile, not retry blindly.
A prior diagnostic report, including `clear`, never substitutes for this final check.

See [Execution boundary](execution-bridge.md), [Modularity and trust](modularity-and-trust.md),
[Persistence](persistence.md), [Provider transport](provider-adapters.md),
[Diagnostic Interface](TRIA_DIAGNOSTIC_INTERFACE_v0.1.md), and
[Compatibility](compatibility.md) for enforceable limits and exact API responsibilities.
Full replay export still requires DISCLOSE. DISSOLVING permits READ but not DISCLOSE;
inspect local history, or return to ACTIVE under lifecycle authority before export.

These rules strengthen encoded governance; they do not establish scientific,
legal, authenticity or deployment-safety claims. The frozen 0.1.0a3 audit remains
historical evidence and has not been revised.
