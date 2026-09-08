# Public API reference

Import from `tria`. Start with [Quickstart](quickstart.md) and use the [complete
application](complete-governed-application.md) before advanced composition.

| Entry point | Contract |
|---|---|
| Tria(store=None) | Defaults to InMemoryEventStore; host owns this object |
| create_relationship(participants) | Nonempty unique identifiers; tria: reserved; returns Relationship |
| load_relationship(relationship_id) | Existing history only; RelationshipNotFoundError otherwise |
| restore_relationship(bundle) | Current-version verified bundle into empty destination; ReplayImportError on invalid input |
| Relationship.admin | HostAdministration; grant_permission(granted_by, grantee, resource, capability, **bounds), revoke_permission(actor, grantee, resource, capability, causal_parents=()) |
| grant_consent(actor, scope, purpose=None, *, expires_at=None, conditions=()) | Registered participant; expiry must be timezone-aware datetime |
| revoke_consent(actor, scope) | Registered participant and nonempty scope |
| check_capability(grantee, resource, capability, purpose=None, *, satisfied_conditions=()) | Pure current decision; includes derived causal ambiguity; Capability enum required |
| require_consent(actor, scope, purpose=None, *, satisfied_conditions=()) | Pure current decision; does not grant permission |
| delegate_permission(delegated_by, grantee, resource, capability, purpose=None, *, expires_at=None, conditions=(), satisfied_conditions=(), causal_parents=()) | Requires active DELEGATE; host must bind actor |
| register_claim(actor, epistemic_type, content, *, derived_from=None, source_refs=None) | EpistemicType enum; OBSERVATION needs source_refs, inference/interpretation need derived_from |
| dispute_claim(actor, claim_id, alternative) | Appends contestation; does not overwrite source |
| grant_lifecycle_authority(granted_by, authority_holder), revoke_lifecycle_authority(actor, authority_holder) | Trusted bootstrap or active authority required |
| transition(actor, to) | Requires lifecycle authority and valid graph; LifecycleState enum |
| grant_policy_authority(granted_by, authority_holder, authority_scope) | Trusted system bootstrap or scope authority |
| register_policy(actor, policy_id, policy_version, authority_scope, *, provenance_refs=(), consent_impacting=False) | Scope authority required; consent-impacting change requires renewed consent |
| adopt_policy(actor, policy_id, policy_version, authority_scope), revoke_policy(actor, policy_id, policy_version) | Registered policy and scoped authority |
| CapabilityRequirement(resource, capability, purpose=None, satisfied_conditions=()) | Explicit resource/capability check |
| ConsentRequirement(actor, scope, purpose=None, satisfied_conditions=()) | Explicit affected-participant consent check |
| InvocationRequest(requested_by, action, target, context_resources=(), requirements=(), consent_requirements=(), request_id=generated, metadata={}, action_ref=None) | Immutable input; use fresh ID for each intentional attempt; complete requirements are host responsibility |
| Runtime(resource_resolver=None).prepare(relationship, request) | Returns InvocationPlan; authorized context only; no executor |
| Runtime.record_result(relationship, InvocationResult(...)) | Advanced host-only recording; bridge does this automatically |
| ExecutionBridge(runtime=None).prepare(rel, request, adapter, *, model, **options) | Inspection receipt, no consequence authority token |
| ExecutionBridge.execute(rel, request, adapter, executor, *, model, **options) | Guarded final check and synchronous local handoff |
| ProviderRequest.to_transport_payload() | Detached recursively JSON-ready payload |
| rel.state / rel.events / rel.audit() | Projection / chronological event list / integrity summary; raw host-only access |
| state_to_dict(state) | Portable JSON-friendly projection, not a governed export |
| export_replay_bundle(rel, *, actor, purpose=None, satisfied_conditions=()) | DISCLOSE-gated complete history; bundle.to_json() serializes |
| verify_replay_bundle(bundle) | Integrity/compatibility report, not source authenticity or truth |
| SQLiteEventStore(path), close(), context manager | Shared local process guard; atomic compare-and-append; see persistence guide |

The advanced EventStore protocol requires append(event), append_many(events),
list(relationship_id), and execution_guard() used by both writes and execution.
Public event/state constructors are trusted infrastructure, not authenticated inputs.
For extension guarantees see [Modularity and trust](modularity-and-trust.md).

## Errors and recovery

InputValidationError names the invalid public field/type. UnknownParticipantError
requires binding a registered identity. RelationshipNotFoundError requires a correct
persisted ID or explicit creation. UnknownResourceError requires a configured host
resolver or valid claim ID. ConcurrentWriteError requires reload and reassessment;
PersistenceError requires correcting store ownership/path/lifetime or recovering
verified history. UnsupportedStoreError requires a guard-capable store/platform.

Governance denial normally returns a plan/receipt, not an exception. Inspect
plan.outcome and plan.reason; PAUSE is not BLOCK. LifecycleTransitionError and
LifecycleAuthorityError distinguish graph and authority failures. ReplayExportError
includes the actual governance reason, including lifecycle denial. ExecutionError
carries an UNKNOWN_EFFECT receipt; reconcile effects before retry. Never infer
completion from missing results or a reserved invocation ID.
