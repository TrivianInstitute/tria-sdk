from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

from .events import RelationalEvent
from .types import (
    Capability,
    Claim,
    ClaimStatus,
    ConsentRecord,
    EpistemicType,
    LifecycleState,
    PermissionRecord,
    PolicyAdoptionRecord,
)


@dataclass(frozen=True, slots=True)
class RelationalState:
    relationship_id: str
    participants: tuple[str, ...] = ()
    lifecycle: LifecycleState = LifecycleState.FORMING
    consent: dict[tuple[str, str], ConsentRecord] = field(default_factory=dict)
    permissions: dict[tuple[str, str, Capability], PermissionRecord] = field(default_factory=dict)
    policy_adoptions: dict[tuple[str, str], PolicyAdoptionRecord] = field(default_factory=dict)
    claims: dict[str, Claim] = field(default_factory=dict)
    disagreements: dict[str, tuple[str, ...]] = field(default_factory=dict)
    last_event_id: str | None = None
    projection_version: str = "0.2"


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
        elif event.event_type == "PermissionGranted":
            permissions = dict(state.permissions)
            capability = Capability(p["capability"])
            record = PermissionRecord(
                grantee=p["grantee"],
                resource=p["resource"],
                capability=capability,
                granted_by=p["granted_by"],
                purpose=p.get("purpose"),
                policy_version=event.policy_version,
                active=True,
            )
            permissions[(record.grantee, record.resource, capability)] = record
            state = replace(state, permissions=permissions, last_event_id=event.event_id)
        elif event.event_type == "PermissionRevoked":
            permissions = dict(state.permissions)
            key = (p["grantee"], p["resource"], Capability(p["capability"]))
            prior = permissions.get(key)
            if prior is not None:
                permissions[key] = replace(prior, active=False)
            state = replace(state, permissions=permissions, last_event_id=event.event_id)
        elif event.event_type == "PolicyAdopted":
            adoptions = dict(state.policy_adoptions)
            record = PolicyAdoptionRecord(
                policy_id=p["policy_id"],
                policy_version=p["policy_version"],
                adopted_by=p["adopted_by"],
                authority_scope=p["authority_scope"],
                active=True,
            )
            adoptions[(record.policy_id, record.policy_version)] = record
            state = replace(state, policy_adoptions=adoptions, last_event_id=event.event_id)
        elif event.event_type == "PolicyRevoked":
            adoptions = dict(state.policy_adoptions)
            key = (p["policy_id"], p["policy_version"])
            prior = adoptions.get(key)
            if prior is not None:
                adoptions[key] = replace(prior, active=False)
            state = replace(state, policy_adoptions=adoptions, last_event_id=event.event_id)
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
