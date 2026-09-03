from __future__ import annotations

from dataclasses import dataclass

from .state import RelationalState
from .types import GovernanceDecision, GovernanceOutcome


@dataclass(frozen=True, slots=True)
class Policy:
    policy_id: str
    version: str
    authored_by: str
    authority_scope: str


class GovernanceEngine:
    """Deterministic v0.1 governance surface.

    The engine intentionally contains only inspectable rules. Model-assisted
    governance can be layered above this interface later.
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
