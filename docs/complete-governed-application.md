# Complete governed application

Start with [Quickstart](quickstart.md), then run
`python examples/governed_assistant.py`. The full runnable application is
[examples/governed_assistant.py](../examples/governed_assistant.py), not an internal
test or an implementation module. Read or copy that public example to build your
application. It runs in an editable install or against a built wheel.

The example records a human's meeting preference as a provenance-bearing claim,
grants purpose-bound consent and READ permission to an assistant, and declares
both requirements. A local executor reads the prepared preference exactly once.
A second attempt after permission revocation and a third after consent revocation
are blocked. The example asserts the call count, inspects current state and
chronological events, closes SQLite, then reopens and verifies the same relationship.

## Public calls used

- `Tria(store).create_relationship(['human:user', 'agent:assistant'])` creates a relationship.
- `rel.register_claim(actor, EpistemicType.OBSERVATION, content, source_refs=[...])` returns a handle; use `claim:<claim_id>` as context resource.
- `rel.grant_consent(actor, scope, purpose='scheduling')` records affected-participant consent.
- `rel.admin.grant_permission(granted_by, grantee, resource, Capability.READ, purpose='scheduling')` is a trusted-host administrative action.
- `CapabilityRequirement(resource, Capability.READ, purpose='scheduling')` declares the resource operation.
- `ConsentRequirement(actor, scope, purpose='scheduling')` separately declares consent.
- `InvocationRequest(requested_by=..., action=..., target=..., context_resources=(resource,), requirements=(...), consent_requirements=(...))` describes an attempt. Use one-element tuples with a trailing comma.
- `ExecutionBridge(Runtime()).execute(rel, request, adapter, executor, model='local-mock')` performs preparation, final resolution and local handoff.
- `rel.admin.revoke_permission(actor, grantee, resource, Capability.READ)` revokes resource authority.
- `rel.revoke_consent(actor, scope)` revokes consent independently.
- `receipt.plan.allowed` and `receipt.plan.reason` explain governance. `receipt.executed` means executor entry, not proof of a remote effect.
- `rel.state` is a fresh immutable projection. `rel.audit()` is a structural integrity summary. `rel.events` contains the chronological history; event payloads are immutable.
- `Tria(store).load_relationship(id)` reopens an existing relationship; missing IDs raise RelationshipNotFoundError.

Never infer consent or ACT/DISCLOSE requirements from action text. The host must
construct the complete declared requirements. The tutorial's toy operation only
reads context locally. A real external disclosure or action requires its own
capability requirements and authenticated host policy.

`prepare()` alone is inspection, not an execution token. Do not send a cached
provider payload yourself while assuming it is still authorized. Submit a fresh
request through `execute()` at the actual handoff. See [Execution boundary](execution-bridge.md).
