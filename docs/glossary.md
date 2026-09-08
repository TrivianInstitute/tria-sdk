# Concepts mapped to operations

| Concept | Meaning / public operation |
|---|---|
| Relationship | Ongoing aggregate of participants and immutable events; Tria.create_relationship |
| Participant | Host-bound actor identifier, not credentials or automatic capability; requester must be registered |
| Consent | Affected participant's scoped relational authorization; grant_consent / revoke_consent |
| Permission | Resource/capability authority; host rel.admin.grant_permission / revoke_permission |
| Requirement | Explicit capability or consent check attached to InvocationRequest; neither is inferred from prose |
| Scope / resource / purpose | Consent use category / governed resource identifier / exact declared reason for use |
| Conditions | Host assertions of satisfied labels; not sensors or independently verified facts |
| Capability | STORE, READ, DISCLOSE, DERIVE, ACT, DELEGATE are independent enum values |
| Lifecycle | Operational restriction; FORMING allows evaluation, RESTING pauses Runtime, DISSOLVED blocks |
| Plan | Historical preparation decision and filtered context; never permanent authority |
| Executor | Trusted synchronous host callable; receives ProviderRequest and owns any external effect |
| Receipt | Plan plus optional provider request/response and result; executed means entry, not success |
| State | Fresh immutable projection; state_to_dict makes a JSON-friendly representation |
| Audit / history | audit() summarizes structural integrity; events preserves occurrence; neither proves truth or legitimate consent |
| Provenance | Attributed reference, not verification of source existence or truth |
| Causal ambiguity | Unordered cross-actor permission grant/revoke; shared engine blocks until order is established |
| Replay | Export needs DISCLOSE; restore checks integrity, not permission for custody or transfer |
