# Modularity and trust model

TRIA is an in-process library. Possession of a Tria, Relationship or store object
is trusted-host access, not an authenticated participant session. Actor strings
are attribution identifiers. The host authenticates callers, binds their identity,
selects their permissible operations, and supplies all applicable requirements.
Never let a model choose another actor, omit mandatory consent, or call host
administrative methods directly. A participant is an identity in the relationship;
registration alone does not grant READ, ACT, DISCLOSE or delegation authority.

`rel.admin` is an explicit host administrative capability for permission grant and
revocation. The legacy `rel.grant_permission`/`revoke_permission` aliases have the
same administrative semantics and validation, not agent authority semantics.
Lifecycle/policy bootstrap with `tria:system`, relationship creation/restoration,
consent recording on behalf of an authenticated participant, stores and raw history
are also host-only operations. Do not expose whole objects as agent tools. Build
narrow endpoints that bind actor and requirements in trusted code.

| Component / category | Provides | Does not provide / caller obligations | Recommended path |
|---|---|---|---|
| Tria / Relationship: governed aggregate | Valid creation/loading, event-derived state, shared causal checks, explicit administration | Host authentication and API exposure controls; raw state is not capability-filtered | Start here; give agents narrow host wrappers |
| ExecutionBridge: governed handoff | Rechecks original declared requirements after preparation under a shared store guard | Remote transaction atomicity, cancellation after entry, transport retries; executor is trusted | Use execute for consequences, not prepare plus direct send |
| Runtime: advanced composition | Request checks and governed context preparation | ALLOW plan freshness; no network | Use through ExecutionBridge; final core checks cannot be replaced by a custom Runtime |
| GovernanceEngine: advanced evaluation | Same projection-derived causal ambiguity and core rules as Relationship | Authenticated provenance of a caller-created state, history freshness, execution or automatic audit | Pass a fresh Relationship.state; record decisions if used outside Runtime |
| RelationalState: infrastructure snapshot | Immutable projection; created/valid history marker and ambiguity set | Not a credential; trusted Python can construct fabricated objects | Obtain from Relationship, serialize with state_to_dict |
| EventStore: infrastructure protocol | Built-ins atomically reject stale predecessor/sequence appends; execution guard | Semantic authorization of arbitrary caller-constructed events | Use built-ins; custom stores must implement atomic append and shared guard |
| SQLiteEventStore | One owning process per file, synchronized local instances, atomic transactions | Direct SQL writers, cross-process live ownership, remote databases | Context manager; handle conflicts, do not blindly retry |
| Event constructors | Hashable attributable immutable values | Authority to commit the claimed event, authenticated actor identity | Advanced trusted infrastructure only |
| Provider translators | Translate allowed plans; immutable request objects | Fresh authorization, network execution or trusted configuration inference | Bridge plus host executor; never use as authority tokens |
| Replay helpers | DISCLOSE-gated export, integrity-gated restore | Consent inference, authorization of later transfers, signatures or truth | Authorize export and separately govern artifact custody |

Critical causal logic is derived once into the projection and checked by the shared
engine. Custom governance may add restrictions; Relationship/Runtime retain core
floors. Custom stores/adapters remain trusted implementations, not sandboxed code.
A store without the shared guard fails at execution. A malicious host with raw
Python, file or database access can bypass the library; no local SDK can revoke
that host's access to its own process memory.

A nonexistent ID raises RelationshipNotFoundError. A raw empty Relationship or
caller-created default RelationalState cannot authorize. An invalid persisted
history remains auditable but is not operational. No external-principal or
participant-removal model is implemented in this prerelease.
