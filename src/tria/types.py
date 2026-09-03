from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EpistemicType(StrEnum):
    OBSERVATION = "OBSERVATION"
    INFERENCE = "INFERENCE"
    INTERPRETATION = "INTERPRETATION"
    SHARED_CLAIM = "SHARED_CLAIM"


class ClaimStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CONTESTED = "CONTESTED"
    REVISED = "REVISED"
    WITHDRAWN = "WITHDRAWN"
    SUPERSEDED = "SUPERSEDED"


class LifecycleState(StrEnum):
    FORMING = "FORMING"
    ACTIVE = "ACTIVE"
    RESTING = "RESTING"
    DORMANT = "DORMANT"
    RENEWING = "RENEWING"
    TRANSFORMING = "TRANSFORMING"
    DISSOLVING = "DISSOLVING"
    DISSOLVED = "DISSOLVED"


class Capability(StrEnum):
    STORE = "STORE"
    READ = "READ"
    DISCLOSE = "DISCLOSE"
    DERIVE = "DERIVE"
    ACT = "ACT"
    DELEGATE = "DELEGATE"


class GovernanceOutcome(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REQUIRE_CONSENT = "REQUIRE_CONSENT"
    ESCALATE = "ESCALATE"
    DEFER = "DEFER"
    PAUSE = "PAUSE"


@dataclass(frozen=True, slots=True)
class Claim:
    claim_id: str
    actor: str
    content: str
    epistemic_type: EpistemicType
    status: ClaimStatus = ClaimStatus.ACTIVE
    derived_from: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class ConsentRecord:
    actor: str
    scope: str
    purpose: str | None = None
    capability: Capability | None = None
    granted_at: datetime = field(default_factory=utcnow)
    expires_at: datetime | None = None
    conditions: tuple[str, ...] = ()
    policy_version: str = "0.1"
    active: bool = True


@dataclass(frozen=True, slots=True)
class PermissionRecord:
    grantee: str
    resource: str
    capability: Capability
    granted_by: str
    purpose: str | None = None
    policy_version: str = "0.1"
    active: bool = True


@dataclass(frozen=True, slots=True)
class PolicyAuthorityRecord:
    authority_holder: str
    authority_scope: str
    granted_by: str
    active: bool = True


@dataclass(frozen=True, slots=True)
class PolicyDefinitionRecord:
    policy_id: str
    policy_version: str
    authored_by: str
    authority_scope: str
    provenance_refs: tuple[str, ...] = ()
    consent_impacting: bool = False
    supersedes_version: str | None = None


@dataclass(frozen=True, slots=True)
class PolicyAdoptionRecord:
    policy_id: str
    policy_version: str
    adopted_by: str
    authority_scope: str
    active: bool = True


@dataclass(frozen=True, slots=True)
class ReconsentRequirement:
    actor: str
    scope: str
    policy_id: str
    policy_version: str
    reason: str
    active: bool = True


@dataclass(frozen=True, slots=True)
class GovernanceDecision:
    outcome: GovernanceOutcome
    policy_id: str
    policy_version: str
    reason: str
    evaluated_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
