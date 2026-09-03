# Consent and metadata boundary

TRIA treats permission and consent as distinct governed conditions. A capability grant answers whether an actor may perform a class of operation on a resource. Consent answers whether an affected participant has authorized the relevant relational use. When an invocation declares both, both must be active; permission never substitutes for consent, and consent never substitutes for capability.

`InvocationRequest.consent_requirements` makes this intersection explicit rather than inferred from resource names. Runtime evaluates consent before materializing context. Missing, revoked, or re-consent-pending consent blocks the invocation before context is exposed.

Core also minimizes execution data by default. The live `action` and arbitrary request/provider metadata remain transient at the runtime/provider boundary. `InvocationProposed` persists an action digest, optional caller-owned `action_ref`, target, requested resources, capability requirements, and consent requirements. `InvocationResultRecorded` persists status and an optional output reference, but not arbitrary provider metadata or raw response bodies.

This separation preserves auditability without turning the relational event stream into a transcript store. Applications that need raw prompts, outputs, or provider diagnostics should retain them in a separately governed store and reference them from TRIA rather than embedding them in Core events.
