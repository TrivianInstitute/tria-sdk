from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

from .compat import CURRENT_PROJECTION_VERSION
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
    PolicyAuthorityRecord,
    PolicyDefinitionRecord,
    ReconsentRequirement,
)


@dataclass(frozen=True, slots=True)
class RelationalState:
    relationship_id: str
    participants: tuple[str, ...] = ()
    lifecycle: LifecycleState = LifecycleState.FORMING
    consent: dict[tuple[str, str], ConsentRecord] = field(default_factory=dict)
    permissions: dict[tuple[str, str, Capability], PermissionRecord] = field(default_factory=dict)
    policy_authorities: dict[tuple[str, str], PolicyAuthorityRecord] = field(default_factory=dict)
    policy_definitions: dict[tuple[str, str], PolicyDefinitionRecord] = field(default_factory=dict)
    policy_adoptions: dict[tuple[str, str], PolicyAdoptionRecord] = field(default_factory=dict)
    reconsent_requirements: dict[tuple[str, str], ReconsentRequirement] = field(default_factory=dict)
    claims: dict[str, Claim] = field(default_factory=dict)
    disagreements: dict[str, tuple[str, ...]] = field(default_factory=dict)
    last_event_id: str | None = None
    projection_version: str = CURRENT_PROJECTION_VERSION


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
            reconsent = dict(state.reconsent_requirements)
            reconsent.pop((record.actor, record.scope), None)
            state = replace(state, consent=consent, reconsent_requirements=reconsent, lifecycle=LifecycleState.ACTIVE, last_event_id=event.event_id)
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
            record = PermissionRecord(grantee=p["grantee"], resource=p["resource"], capability=capability, granted_by=p["granted_by"], purpose=p.get("purpose"), policy_version=event.policy_version, active=True)
            permissions[(record.grantee, record.resource, capability)] = record
            state = replace(state, permissions=permissions, last_event_id=event.event_id)
        elif event.event_type == "PermissionRevoked":
            permissions = dict(state.permissions)
            key = (p["grantee"], p["resource"], Capability(p["capability"]))
            prior = permissions.get(key)
            if prior is not None:
                permissions[key] = replace(prior, active=False)
            state = replace(state, permissions=permissions, last_event_id=event.event_id)
        elif event.event_type == "PolicyAuthorityGranted":
            authorities = dict(state.policy_authorities)
            record = PolicyAuthorityRecord(p["authority_holder"], p["authority_scope"], p["granted_by"], True)
            authorities[(record.authority_holder, record.authority_scope)] = record
            state = replace(state, policy_authorities=authorities, last_event_id=event.event_id)
        elif event.event_type == "PolicyAuthorityRevoked":
            authorities = dict(state.policy_authorities)
            key = (p["authority_holder"], p["authority_scope"])
            prior = authorities.get(key)
            if prior is not None:
                authorities[key] = replace(prior, active=False)
            state = replace(state, policy_authorities=authorities, last_event_id=event.event_id)
        elif event.event_type in ("PolicyRegistered", "PolicyAmended"):
            definitions = dict(state.policy_definitions)
            record = PolicyDefinitionRecord(
                policy_id=p["policy_id"], policy_version=p["policy_version"], authored_by=p["authored_by"],
                authority_scope=p["authority_scope"], provenance_refs=tuple(p.get("provenance_refs", ())),
                consent_impacting=bool(p.get("consent_impacting", False)), supersedes_version=p.get("supersedes_version"),
            )
            definitions[(record.policy_id, record.policy_version)] = record
            reconsent = dict(state.reconsent_requirements)
            if record.consent_impacting:
                for (actor, scope), consent_record in state.consent.items():
                    if scope == record.authority_scope and consent_record.active:
                        reconsent[(actor, scope)] = ReconsentRequirement(actor, scope, record.policy_id, record.policy_version, "Consent-impacting policy change requires renewed consent.")
            state = replace(state, policy_definitions=definitions, reconsent_requirements=reconsent, last_event_id=event.event_id)
        elif event.event_type == "PolicyAdopted":
            adoptions = dict(state.policy_adoptions)
            record = PolicyAdoptionRecord(policy_id=p["policy_id"], policy_version=p["policy_version"], adopted_by=p["adopted_by"], authority_scope=p["authority_scope"], active=True)
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
