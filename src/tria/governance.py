from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .state import RelationalState
from .types import Capability, GovernanceDecision, GovernanceOutcome, LifecycleState, utcnow


@dataclass(frozen=True, slots=True)
class Policy:
    policy_id: str
    version: str
    authored_by: str
    authority_scope: str
    provenance_refs: tuple[str, ...] = ()
    consent_impacting: bool = False


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

    @staticmethod
    def _purpose_matches(bound_purpose: str | None, requested_purpose: str | None) -> bool:
        if bound_purpose is None:
            return True
        return requested_purpose == bound_purpose

    @staticmethod
    def _conditions_match(bound_conditions: tuple[str, ...], satisfied_conditions: tuple[str, ...]) -> bool:
        return set(bound_conditions).issubset(set(satisfied_conditions))

    @staticmethod
    def _expired(expires_at: datetime | None, evaluated_at: datetime) -> bool:
        return expires_at is not None and evaluated_at >= expires_at

    def require_active_consent(
        self,
        state: RelationalState,
        actor: str,
        scope: str,
        purpose: str | None = None,
        *,
        satisfied_conditions: tuple[str, ...] = (),
        evaluated_at: datetime | None = None,
    ) -> GovernanceDecision:
        evaluated_at = evaluated_at or utcnow()
        if (actor, scope) in state.reconsent_requirements:
            return GovernanceDecision(GovernanceOutcome.REQUIRE_CONSENT, "core.consent.reconsent", "0.1", f"Renewed consent is required for {actor!r} scope {scope!r} after a consent-impacting policy change.", evaluated_at=evaluated_at)
        record = state.consent.get((actor, scope))
        if record and record.active:
            if self._expired(record.expires_at, evaluated_at):
                return GovernanceDecision(GovernanceOutcome.REQUIRE_CONSENT, "core.consent.expiry", "0.1", f"Consent for {actor!r} scope {scope!r} expired at {record.expires_at.isoformat()}.", evaluated_at=evaluated_at)
            if not self._purpose_matches(record.purpose, purpose):
                return GovernanceDecision(GovernanceOutcome.REQUIRE_CONSENT, "core.consent.purpose", "0.1", f"Active consent for {actor!r} scope {scope!r} is bound to purpose {record.purpose!r}; requested purpose {purpose!r} is not authorized.", evaluated_at=evaluated_at)
            if not self._conditions_match(record.conditions, satisfied_conditions):
                missing = sorted(set(record.conditions) - set(satisfied_conditions))
                return GovernanceDecision(GovernanceOutcome.REQUIRE_CONSENT, "core.consent.conditions", "0.1", f"Consent conditions are not satisfied for {actor!r} scope {scope!r}: {missing!r}.", evaluated_at=evaluated_at)
            return GovernanceDecision(GovernanceOutcome.ALLOW, "core.consent.active", "0.1", f"Active consent exists for {actor!r} scope {scope!r} with requested purpose and conditions.", evaluated_at=evaluated_at)
        return GovernanceDecision(GovernanceOutcome.REQUIRE_CONSENT, "core.consent.active", "0.1", f"No active consent exists for {actor!r} scope {scope!r}.", evaluated_at=evaluated_at)

    def require_capability(
        self,
        state: RelationalState,
        grantee: str,
        resource: str,
        capability: Capability,
        purpose: str | None = None,
        *,
        satisfied_conditions: tuple[str, ...] = (),
        evaluated_at: datetime | None = None,
    ) -> GovernanceDecision:
        evaluated_at = evaluated_at or utcnow()
        lifecycle = self.require_lifecycle_capability(state, capability)
        if lifecycle.outcome is not GovernanceOutcome.ALLOW:
            return lifecycle
        record = state.permissions.get((grantee, resource, capability))
        if record and record.active:
            if self._expired(record.expires_at, evaluated_at):
                return GovernanceDecision(GovernanceOutcome.BLOCK, "core.permission.expiry", "0.1", f"{capability.value} permission for {grantee!r} on {resource!r} expired at {record.expires_at.isoformat()}.", evaluated_at=evaluated_at)
            if not self._purpose_matches(record.purpose, purpose):
                return GovernanceDecision(GovernanceOutcome.BLOCK, "core.permission.purpose", "0.1", f"{grantee!r} has {capability.value} permission for {resource!r}, but it is bound to purpose {record.purpose!r}; requested purpose {purpose!r} is not authorized.", evaluated_at=evaluated_at)
            if not self._conditions_match(record.conditions, satisfied_conditions):
                missing = sorted(set(record.conditions) - set(satisfied_conditions))
                return GovernanceDecision(GovernanceOutcome.BLOCK, "core.permission.conditions", "0.1", f"{capability.value} permission conditions are not satisfied for {grantee!r} on {resource!r}: {missing!r}.", evaluated_at=evaluated_at)
            return GovernanceDecision(GovernanceOutcome.ALLOW, "core.permission.active", "0.1", f"{grantee!r} has active {capability.value} permission for {resource!r} with requested purpose and conditions.", evaluated_at=evaluated_at)
        return GovernanceDecision(GovernanceOutcome.BLOCK, "core.permission.active", "0.1", f"No active {capability.value} permission exists for {grantee!r} on {resource!r}.", evaluated_at=evaluated_at)

    def require_lifecycle_capability(self, state: RelationalState, capability: Capability) -> GovernanceDecision:
        allowed: dict[LifecycleState, frozenset[Capability]] = {
            LifecycleState.FORMING: frozenset(Capability),
            LifecycleState.ACTIVE: frozenset(Capability),
            LifecycleState.RENEWING: frozenset(Capability),
            LifecycleState.TRANSFORMING: frozenset(Capability),
            LifecycleState.RESTING: frozenset({Capability.READ, Capability.STORE}),
            LifecycleState.DORMANT: frozenset({Capability.READ}),
            LifecycleState.DISSOLVING: frozenset({Capability.READ}),
            LifecycleState.DISSOLVED: frozenset(),
        }
        if capability in allowed[state.lifecycle]:
            return GovernanceDecision(GovernanceOutcome.ALLOW, "core.lifecycle.capability", "0.1", f"{capability.value} is permitted while relationship is {state.lifecycle.value}.")
        return GovernanceDecision(GovernanceOutcome.BLOCK, "core.lifecycle.capability", "0.1", f"{capability.value} is blocked while relationship is {state.lifecycle.value}.")

    def require_lifecycle_authority(self, state: RelationalState, actor: str) -> GovernanceDecision:
        record = state.lifecycle_authorities.get(actor)
        if record and record.active:
            return GovernanceDecision(GovernanceOutcome.ALLOW, "core.lifecycle.authority", "0.1", f"{actor!r} has active lifecycle authority for this relationship.")
        return GovernanceDecision(GovernanceOutcome.BLOCK, "core.lifecycle.authority", "0.1", f"{actor!r} lacks active lifecycle authority for this relationship.")

    def require_lifecycle_transition(self, state: RelationalState, to: LifecycleState) -> GovernanceDecision:
        allowed: dict[LifecycleState, frozenset[LifecycleState]] = {
            LifecycleState.FORMING: frozenset({LifecycleState.ACTIVE, LifecycleState.DISSOLVING}),
            LifecycleState.ACTIVE: frozenset({LifecycleState.RESTING, LifecycleState.RENEWING, LifecycleState.TRANSFORMING, LifecycleState.DISSOLVING}),
            LifecycleState.RESTING: frozenset({LifecycleState.ACTIVE, LifecycleState.DORMANT, LifecycleState.DISSOLVING}),
            LifecycleState.DORMANT: frozenset({LifecycleState.RENEWING, LifecycleState.DISSOLVING}),
            LifecycleState.RENEWING: frozenset({LifecycleState.ACTIVE, LifecycleState.TRANSFORMING, LifecycleState.DISSOLVING}),
            LifecycleState.TRANSFORMING: frozenset({LifecycleState.ACTIVE, LifecycleState.RESTING, LifecycleState.DISSOLVING}),
            LifecycleState.DISSOLVING: frozenset({LifecycleState.ACTIVE, LifecycleState.DISSOLVED}),
            LifecycleState.DISSOLVED: frozenset(),
        }
        if to in allowed[state.lifecycle]:
            return GovernanceDecision(GovernanceOutcome.ALLOW, "core.lifecycle.transition", "0.1", f"Lifecycle transition {state.lifecycle.value} -> {to.value} is permitted.")
        return GovernanceDecision(GovernanceOutcome.BLOCK, "core.lifecycle.transition", "0.1", f"Lifecycle transition {state.lifecycle.value} -> {to.value} is not permitted.")

    def require_runtime_execution(self, state: RelationalState) -> GovernanceDecision:
        if state.lifecycle in {LifecycleState.FORMING, LifecycleState.ACTIVE, LifecycleState.RENEWING, LifecycleState.TRANSFORMING}:
            return GovernanceDecision(GovernanceOutcome.ALLOW, "core.lifecycle.runtime", "0.1", f"Runtime execution is permitted while relationship is {state.lifecycle.value}.")
        outcome = GovernanceOutcome.BLOCK if state.lifecycle is LifecycleState.DISSOLVED else GovernanceOutcome.PAUSE
        return GovernanceDecision(outcome, "core.lifecycle.runtime", "0.1", f"Runtime execution is not permitted while relationship is {state.lifecycle.value}.")

    def require_policy_authority(self, state: RelationalState, actor: str, authority_scope: str) -> GovernanceDecision:
        record = state.policy_authorities.get((actor, authority_scope))
        if record and record.active:
            return GovernanceDecision(GovernanceOutcome.ALLOW, "core.policy.authority", "0.1", f"{actor!r} has active policy authority for {authority_scope!r}.")
        return GovernanceDecision(GovernanceOutcome.BLOCK, "core.policy.authority", "0.1", f"{actor!r} lacks active policy authority for {authority_scope!r}.")

    def require_policy_adoption(self, state: RelationalState, policy_id: str, policy_version: str) -> GovernanceDecision:
        record = state.policy_adoptions.get((policy_id, policy_version))
        if record and record.active:
            return GovernanceDecision(GovernanceOutcome.ALLOW, "core.policy.adopted", "0.1", f"Policy {policy_id}@{policy_version} is actively adopted.")
        return GovernanceDecision(GovernanceOutcome.BLOCK, "core.policy.adopted", "0.1", f"Policy {policy_id}@{policy_version} is not actively adopted.")
