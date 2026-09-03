from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .state import RelationalState
from .types import Capability, GovernanceDecision, GovernanceOutcome, utcnow


@dataclass(frozen=True, slots=True)
class Policy:
    policy_id: str
    version: str
    authored_by: str
    authority_scope: str
    provenance_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PolicyAdoption:
    policy_id: str
    policy_version: str
    adopted_by: str
    authority_scope: str
    adopted_at: datetime = field(default_factory=utcnow)
    consent_required: bool = False


class GovernanceEngine:
    """Deterministic, inspectable governance rules."""

    def require_active_consent(self, state: RelationalState, actor: str, scope: str) -> GovernanceDecision:
        record = state.consent.get((actor, scope))
        if record and record.active:
            return GovernanceDecision(GovernanceOutcome.ALLOW, "core.consent.active", "0.1", f"Active consent exists for {actor!r} scope {scope!r}.")
        return GovernanceDecision(GovernanceOutcome.REQUIRE_CONSENT, "core.consent.active", "0.1", f"No active consent exists for {actor!r} scope {scope!r}.")

    def require_capability(self, state: RelationalState, grantee: str, resource: str, capability: Capability) -> GovernanceDecision:
        record = state.permissions.get((grantee, resource, capability))
        if record and record.active:
            return GovernanceDecision(GovernanceOutcome.ALLOW, "core.permission.active", "0.1", f"{grantee!r} has active {capability.value} permission for {resource!r}.")
        return GovernanceDecision(GovernanceOutcome.BLOCK, "core.permission.active", "0.1", f"No active {capability.value} permission exists for {grantee!r} on {resource!r}.")

    def require_policy_adoption(self, state: RelationalState, policy_id: str, policy_version: str) -> GovernanceDecision:
        record = state.policy_adoptions.get((policy_id, policy_version))
        if record and record.active:
            return GovernanceDecision(GovernanceOutcome.ALLOW, "core.policy.adopted", "0.1", f"Policy {policy_id}@{policy_version} is actively adopted.")
        return GovernanceDecision(GovernanceOutcome.BLOCK, "core.policy.adopted", "0.1", f"Policy {policy_id}@{policy_version} is not actively adopted.")
