from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .events import EventProposal, RelationalEvent, verify_event_chain
from .governance import GovernanceEngine
from .state import RelationalState, reduce_events
from .store import EventStore, InMemoryEventStore
from .types import EpistemicType, LifecycleState


class EpistemicAdmissionError(ValueError):
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
        proposal = EventProposal(relationship_id=self.relationship_id, event_type=event_type, actor_id=actor, payload=payload, actor_sequence=self._next_actor_sequence(actor), causal_parents=causal_parents)
        event = RelationalEvent.commit(proposal, previous_event_hash=prior)
        self._store.append(event)
        return event

    def grant_consent(self, actor: str, scope: str, purpose: str | None = None) -> RelationalEvent:
        return self._commit("ConsentGranted", actor, {"actor": actor, "scope": scope, "purpose": purpose})

    def revoke_consent(self, actor: str, scope: str) -> RelationalEvent:
        return self._commit("ConsentRevoked", actor, {"actor": actor, "scope": scope})

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
        return self._commit("LifecycleTransitioned", actor, {"to": to.value})

    def require_consent(self, actor: str, scope: str):
        decision = self._governance.require_active_consent(self.state, actor, scope)
        self._commit("GovernanceEvaluated", "tria:governance", {"outcome": decision.outcome.value, "policy_id": decision.policy_id, "policy_version": decision.policy_version, "reason": decision.reason, "actor": actor, "scope": scope})
        return decision

    def audit(self) -> dict:
        events = self.events
        last_event_id = events[-1].event_id if events else None
        return {
            "relationship_id": self.relationship_id,
            "event_count": len(events),
            "hashes_valid": all(e.verify_hash() for e in events),
            "chain_valid": verify_event_chain(events),
            "last_event_id": last_event_id,
            "reconstructable": self.state.last_event_id == last_event_id,
        }


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
