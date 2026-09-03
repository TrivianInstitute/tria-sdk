from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

from .events import RelationalEvent
from .types import Claim, ClaimStatus, ConsentRecord, EpistemicType, LifecycleState


@dataclass(frozen=True, slots=True)
class RelationalState:
    relationship_id: str
    participants: tuple[str, ...] = ()
    lifecycle: LifecycleState = LifecycleState.FORMING
    consent: dict[tuple[str, str], ConsentRecord] = field(default_factory=dict)
    claims: dict[str, Claim] = field(default_factory=dict)
    disagreements: dict[str, tuple[str, ...]] = field(default_factory=dict)
    last_event_id: str | None = None
    projection_version: str = "0.1"


def reduce_events(relationship_id: str, events: Iterable[RelationalEvent]) -> RelationalState:
    state = RelationalState(relationship_id=relationship_id)
    for event in events:
        p = event.payload
        if event.event_type == "RelationshipCreated":
            state = replace(state, participants=tuple(p["participants"]), lifecycle=LifecycleState.FORMING, last_event_id=event.event_id)
        elif event.event_type == "ConsentGranted":
            consent = dict(state.consent)
            record = ConsentRecord(actor=p["actor"], scope=p["scope"], purpose=p.get("purpose"), policy_version=event.policy_version, active=True)
            consent[(record.actor, record.scope)] = record
            state = replace(state, consent=consent, lifecycle=LifecycleState.ACTIVE, last_event_id=event.event_id)
        elif event.event_type == "ConsentRevoked":
            consent = dict(state.consent)
            key = (p["actor"], p["scope"])
            prior = consent.get(key)
            if prior is not None:
                consent[key] = replace(prior, active=False)
            state = replace(state, consent=consent, last_event_id=event.event_id)
        elif event.event_type == "ClaimRegistered":
            claims = dict(state.claims)
            claim = Claim(claim_id=p["claim_id"], actor=p["actor"], content=p["content"], epistemic_type=EpistemicType(p["epistemic_type"]), derived_from=tuple(p.get("derived_from", ())), source_refs=tuple(p.get("source_refs", ())))
            claims[claim.claim_id] = claim
            state = replace(state, claims=claims, last_event_id=event.event_id)
        elif event.event_type == "ClaimDisputed":
            claims = dict(state.claims)
            claim_id = p["claim_id"]
            if claim_id in claims:
                claims[claim_id] = replace(claims[claim_id], status=ClaimStatus.CONTESTED)
            disagreements = dict(state.disagreements)
            disagreements.setdefault(claim_id, tuple())
            disagreements[claim_id] = disagreements[claim_id] + (p["alternative"],)
            state = replace(state, claims=claims, disagreements=disagreements, last_event_id=event.event_id)
        elif event.event_type == "LifecycleTransitioned":
            state = replace(state, lifecycle=LifecycleState(p["to"]), last_event_id=event.event_id)
        else:
            state = replace(state, last_event_id=event.event_id)
    return state
