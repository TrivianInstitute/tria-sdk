from __future__ import annotations

from dataclasses import dataclass
import hashlib
from uuid import uuid4

from .events import EventProposal, RelationalEvent, verify_event_chain
from .governance import GovernanceEngine
from .state import RelationalState, reduce_events
from .store import EventStore, InMemoryEventStore
from .types import Capability, EpistemicType, GovernanceDecision, GovernanceOutcome, LifecycleState


class EpistemicAdmissionError(ValueError):
    pass


class PolicyAuthorityError(PermissionError):
    pass


class DelegationError(PermissionError):
    pass


class LifecycleAuthorityError(PermissionError):
    pass


class LifecycleTransitionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ClaimHandle:
    claim_id: str


class Relationship:
    def __init__(self, relationship_id: str, store: EventStore, governance: GovernanceEngine | None = None) -> None:
        self.relationship_id = relationship_id
        self._store = store
        self._governance = governance or GovernanceEngine()

    @property
    def events(self) -> list[RelationalEvent]:
        return self._store.list(self.relationship_id)

    @property
    def state(self) -> RelationalState:
        return reduce_events(self.relationship_id, self.events)

    def _next_actor_sequence(self, actor: str) -> int:
        return 1 + max((e.actor_sequence for e in self.events if e.actor_id == actor), default=0)

    def _commit(self, event_type: str, actor: str, payload: dict, causal_parents: tuple[str, ...] = ()) -> RelationalEvent:
        prior = self.events[-1].event_hash if self.events else None
        proposal = EventProposal(self.relationship_id, event_type, actor, payload, self._next_actor_sequence(actor), causal_parents)
        event = RelationalEvent.commit(proposal, previous_event_hash=prior)
        self._store.append(event)
        return event

    def _event_by_id(self, event_id: str) -> RelationalEvent | None:
        return next((event for event in self.events if event.event_id == event_id), None)

    def _causally_precedes(self, left: RelationalEvent, right: RelationalEvent) -> bool:
        if left.actor_id == right.actor_id and left.actor_sequence < right.actor_sequence:
            return True
        pending = list(right.causal_parents)
        seen: set[str] = set()
        while pending:
            event_id = pending.pop()
            if event_id in seen:
                continue
            seen.add(event_id)
            if event_id == left.event_id:
                return True
            parent = self._event_by_id(event_id)
            if parent is not None:
                pending.extend(parent.causal_parents)
        return False

    def _permission_race_is_ambiguous(self, grantee: str, resource: str, capability: Capability) -> bool:
        relevant = [event for event in self.events if event.event_type in {"PermissionGranted", "PermissionRevoked"} and event.payload.get("grantee") == grantee and event.payload.get("resource") == resource and event.payload.get("capability") == capability.value]
        grants = [event for event in relevant if event.event_type == "PermissionGranted"]
        revokes = [event for event in relevant if event.event_type == "PermissionRevoked"]
        if not grants or not revokes:
            return False
        grant = grants[-1]
        revoke = revokes[-1]
        return not self._causally_precedes(grant, revoke) and not self._causally_precedes(revoke, grant)

    def grant_consent(self, actor: str, scope: str, purpose: str | None = None) -> RelationalEvent:
        return self._commit("ConsentGranted", actor, {"actor": actor, "scope": scope, "purpose": purpose})

    def revoke_consent(self, actor: str, scope: str) -> RelationalEvent:
        return self._commit("ConsentRevoked", actor, {"actor": actor, "scope": scope})

    def grant_permission(self, granted_by: str, grantee: str, resource: str, capability: Capability, purpose: str | None = None, *, causal_parents: tuple[str, ...] = ()) -> RelationalEvent:
        return self._commit("PermissionGranted", granted_by, {"granted_by": granted_by, "grantee": grantee, "resource": resource, "capability": capability.value, "purpose": purpose, "delegated": False}, causal_parents)

    def delegate_permission(self, delegated_by: str, grantee: str, resource: str, capability: Capability, purpose: str | None = None, *, causal_parents: tuple[str, ...] = ()) -> RelationalEvent:
        decision = self.check_capability(delegated_by, resource, Capability.DELEGATE)
        if decision.outcome is not GovernanceOutcome.ALLOW:
            raise DelegationError(f"{delegated_by!r} cannot delegate permissions for {resource!r} without active DELEGATE authority.")
        return self._commit("PermissionGranted", delegated_by, {"granted_by": delegated_by, "grantee": grantee, "resource": resource, "capability": capability.value, "purpose": purpose, "delegated": True}, causal_parents)

    def revoke_permission(self, actor: str, grantee: str, resource: str, capability: Capability, *, causal_parents: tuple[str, ...] = ()) -> RelationalEvent:
        return self._commit("PermissionRevoked", actor, {"grantee": grantee, "resource": resource, "capability": capability.value}, causal_parents)

    def check_capability(self, grantee: str, resource: str, capability: Capability) -> GovernanceDecision:
        if self._permission_race_is_ambiguous(grantee, resource, capability):
            decision = GovernanceDecision(GovernanceOutcome.BLOCK, "core.permission.race", "0.1", f"Permission state for {grantee!r} on {resource!r} is causally ambiguous; revocation dominates until order is established.")
        else:
            decision = self._governance.require_capability(self.state, grantee, resource, capability)
        self._commit("GovernanceEvaluated", "tria:governance", {"outcome": decision.outcome.value, "policy_id": decision.policy_id, "policy_version": decision.policy_version, "reason": decision.reason, "grantee": grantee, "resource": resource, "capability": capability.value})
        return decision

    def grant_lifecycle_authority(self, granted_by: str, authority_holder: str) -> RelationalEvent:
        if granted_by != "tria:system":
            self._require_lifecycle_authority(granted_by)
        return self._commit("LifecycleAuthorityGranted", granted_by, {"granted_by": granted_by, "authority_holder": authority_holder})

    def revoke_lifecycle_authority(self, actor: str, authority_holder: str) -> RelationalEvent:
        if actor != "tria:system":
            self._require_lifecycle_authority(actor)
        return self._commit("LifecycleAuthorityRevoked", actor, {"authority_holder": authority_holder})

    def _require_lifecycle_authority(self, actor: str) -> None:
        decision = self._governance.require_lifecycle_authority(self.state, actor)
        self._commit("GovernanceEvaluated", "tria:governance", {"outcome": decision.outcome.value, "policy_id": decision.policy_id, "policy_version": decision.policy_version, "reason": decision.reason, "actor": actor, "relationship_id": self.relationship_id})
        if decision.outcome is not GovernanceOutcome.ALLOW:
            raise LifecycleAuthorityError(decision.reason)

    def grant_policy_authority(self, granted_by: str, authority_holder: str, authority_scope: str) -> RelationalEvent:
        if granted_by != "tria:system":
            self._require_policy_authority(granted_by, authority_scope)
        return self._commit("PolicyAuthorityGranted", granted_by, {"granted_by": granted_by, "authority_holder": authority_holder, "authority_scope": authority_scope})

    def revoke_policy_authority(self, actor: str, authority_holder: str, authority_scope: str) -> RelationalEvent:
        if actor != "tria:system":
            self._require_policy_authority(actor, authority_scope)
        return self._commit("PolicyAuthorityRevoked", actor, {"authority_holder": authority_holder, "authority_scope": authority_scope})

    def _require_policy_authority(self, actor: str, authority_scope: str) -> None:
        decision = self._governance.require_policy_authority(self.state, actor, authority_scope)
        self._commit("GovernanceEvaluated", "tria:governance", {"outcome": decision.outcome.value, "policy_id": decision.policy_id, "policy_version": decision.policy_version, "reason": decision.reason, "actor": actor, "authority_scope": authority_scope})
        if decision.outcome is not GovernanceOutcome.ALLOW:
            raise PolicyAuthorityError(decision.reason)

    def register_policy(self, actor: str, policy_id: str, policy_version: str, authority_scope: str, *, provenance_refs: tuple[str, ...] = (), consent_impacting: bool = False) -> RelationalEvent:
        self._require_policy_authority(actor, authority_scope)
        return self._commit("PolicyRegistered", actor, {"policy_id": policy_id, "policy_version": policy_version, "authored_by": actor, "authority_scope": authority_scope, "provenance_refs": list(provenance_refs), "consent_impacting": consent_impacting})

    def amend_policy(self, actor: str, policy_id: str, policy_version: str, authority_scope: str, *, supersedes_version: str, provenance_refs: tuple[str, ...] = (), consent_impacting: bool = False) -> RelationalEvent:
        self._require_policy_authority(actor, authority_scope)
        return self._commit("PolicyAmended", actor, {"policy_id": policy_id, "policy_version": policy_version, "authored_by": actor, "authority_scope": authority_scope, "provenance_refs": list(provenance_refs), "consent_impacting": consent_impacting, "supersedes_version": supersedes_version})

    def adopt_policy(self, actor: str, policy_id: str, policy_version: str, authority_scope: str) -> RelationalEvent:
        self._require_policy_authority(actor, authority_scope)
        if (policy_id, policy_version) not in self.state.policy_definitions:
            raise ValueError(f"Policy {policy_id}@{policy_version} must be registered before adoption.")
        return self._commit("PolicyAdopted", actor, {"policy_id": policy_id, "policy_version": policy_version, "adopted_by": actor, "authority_scope": authority_scope})

    def revoke_policy(self, actor: str, policy_id: str, policy_version: str) -> RelationalEvent:
        record = self.state.policy_adoptions.get((policy_id, policy_version))
        if record is None:
            raise ValueError(f"Policy {policy_id}@{policy_version} is not adopted.")
        self._require_policy_authority(actor, record.authority_scope)
        return self._commit("PolicyRevoked", actor, {"policy_id": policy_id, "policy_version": policy_version})

    def check_policy_adoption(self, policy_id: str, policy_version: str):
        decision = self._governance.require_policy_adoption(self.state, policy_id, policy_version)
        self._commit("GovernanceEvaluated", "tria:governance", {"outcome": decision.outcome.value, "policy_id": decision.policy_id, "policy_version": decision.policy_version, "reason": decision.reason, "checked_policy_id": policy_id, "checked_policy_version": policy_version})
        return decision

    def register_claim(self, actor: str, epistemic_type: EpistemicType, content: str, *, derived_from: list[str] | None = None, source_refs: list[str] | None = None) -> ClaimHandle:
        derived_from = derived_from or []
        source_refs = source_refs or []
        if epistemic_type is EpistemicType.OBSERVATION and not source_refs:
            raise EpistemicAdmissionError("OBSERVATION requires at least one source_ref; provenance is not truth, but source attribution is mandatory.")
        if epistemic_type in (EpistemicType.INFERENCE, EpistemicType.INTERPRETATION) and not derived_from:
            raise EpistemicAdmissionError(f"{epistemic_type} requires derived_from provenance.")
        claim_id = str(uuid4())
        self._commit("ClaimRegistered", actor, {"claim_id": claim_id, "actor": actor, "content": content, "epistemic_type": epistemic_type.value, "derived_from": derived_from, "source_refs": source_refs})
        return ClaimHandle(claim_id)

    def dispute_claim(self, actor: str, claim_id: str, alternative: str) -> RelationalEvent:
        return self._commit("ClaimDisputed", actor, {"claim_id": claim_id, "alternative": alternative})

    def transition(self, actor: str, to: LifecycleState) -> RelationalEvent:
        self._require_lifecycle_authority(actor)
        decision = self._governance.require_lifecycle_transition(self.state, to)
        self._commit("GovernanceEvaluated", "tria:governance", {"outcome": decision.outcome.value, "policy_id": decision.policy_id, "policy_version": decision.policy_version, "reason": decision.reason, "actor": actor, "from": self.state.lifecycle.value, "to": to.value})
        if decision.outcome is not GovernanceOutcome.ALLOW:
            raise LifecycleTransitionError(decision.reason)
        return self._commit("LifecycleTransitioned", actor, {"from": self.state.lifecycle.value, "to": to.value})

    def require_consent(self, actor: str, scope: str):
        decision = self._governance.require_active_consent(self.state, actor, scope)
        self._commit("GovernanceEvaluated", "tria:governance", {"outcome": decision.outcome.value, "policy_id": decision.policy_id, "policy_version": decision.policy_version, "reason": decision.reason, "actor": actor, "scope": scope})
        return decision

    def record_invocation_proposed(self, request) -> RelationalEvent:
        action_digest = hashlib.sha256(request.action.encode("utf-8")).hexdigest()
        return self._commit("InvocationProposed", request.requested_by, {"request_id": request.request_id, "action_digest": action_digest, "action_ref": request.action_ref, "target": request.target, "context_resources": list(request.context_resources), "requirements": [{"resource": item.resource, "capability": item.capability.value} for item in request.requirements], "consent_requirements": [{"actor": item.actor, "scope": item.scope} for item in request.consent_requirements]})

    def record_invocation_resolution(self, actor: str, request_id: str, status: str, *, reason: str) -> RelationalEvent:
        return self._commit("InvocationResolved", "tria:governance", {"request_id": request_id, "requested_by": actor, "status": status, "reason": reason})

    def record_invocation_result(self, result) -> RelationalEvent:
        return self._commit("InvocationResultRecorded", result.produced_by, {"request_id": result.request_id, "status": result.status, "output_ref": result.output_ref})

    def audit(self) -> dict:
        events = self.events
        last_event_id = events[-1].event_id if events else None
        return {"relationship_id": self.relationship_id, "event_count": len(events), "hashes_valid": all(e.verify_hash() for e in events), "chain_valid": verify_event_chain(events), "last_event_id": last_event_id, "reconstructable": self.state.last_event_id == last_event_id}


class Tria:
    def __init__(self, store: EventStore | None = None) -> None:
        self.store = store or InMemoryEventStore()

    def create_relationship(self, participants: list[str]) -> Relationship:
        relationship_id = str(uuid4())
        rel = Relationship(relationship_id, self.store)
        rel._commit("RelationshipCreated", "tria:system", {"participants": participants})
        return rel

    def load_relationship(self, relationship_id: str) -> Relationship:
        return Relationship(relationship_id, self.store)

    def restore_relationship(self, bundle) -> Relationship:
        from .portable import import_replay_bundle
        relationship_id = import_replay_bundle(self.store, bundle)
        return Relationship(relationship_id, self.store)
