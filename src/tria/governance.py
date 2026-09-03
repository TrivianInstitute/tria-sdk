from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .state import RelationalState
from .types import GovernanceDecision, GovernanceOutcome, utcnow


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
    """Deterministic v0.1 governance surface.

    Rules remain inspectable and versioned. Determinism does not establish
    legitimacy; policy authorship, authority, and adoption remain attributable.
    """

    def require_active_consent(self, state: RelationalState, actor: str, scope: str) -> GovernanceDecision:
        record = state.consent.get((actor, scope))
        if record and record.active:
            return GovernanceDecision(
                outcome=GovernanceOutcome.ALLOW,
                policy_id="core.consent.active",
                policy_version="0.1",
                reason=f"Active consent exists for {actor!r} scope {scope!r}.",
            )
        return GovernanceDecision(
            outcome=GovernanceOutcome.REQUIRE_CONSENT,
            policy_id="core.consent.active",
            policy_version="0.1",
            reason=f"No active consent exists for {actor!r} scope {scope!r}.",
        )
