from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from .core import Relationship
from .governance import GovernanceEngine
from .types import Capability, GovernanceDecision, GovernanceOutcome


@dataclass(frozen=True, slots=True)
class CapabilityRequirement:
    resource: str
    capability: Capability
    purpose: str | None = None


@dataclass(frozen=True, slots=True)
class ConsentRequirement:
    actor: str
    scope: str
    purpose: str | None = None


@dataclass(frozen=True, slots=True)
class InvocationRequest:
    requested_by: str
    action: str
    target: str
    context_resources: tuple[str, ...] = ()
    requirements: tuple[CapabilityRequirement, ...] = ()
    consent_requirements: tuple[ConsentRequirement, ...] = ()
    request_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)
    action_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ContextItem:
    resource: str
    value: Any
    epistemic_type: str | None = None
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class InvocationPlan:
    request: InvocationRequest
    outcome: GovernanceOutcome
    decisions: tuple[GovernanceDecision, ...]
    context: tuple[ContextItem, ...] = ()
    reason: str = ""

    @property
    def allowed(self) -> bool:
        return self.outcome is GovernanceOutcome.ALLOW


@dataclass(frozen=True, slots=True)
class InvocationResult:
    request_id: str
    produced_by: str
    status: str
    output_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Runtime:
    """Model-agnostic boundary between governed relationship state and execution."""

    def prepare(self, relationship: Relationship, request: InvocationRequest) -> InvocationPlan:
        relationship.record_invocation_proposed(request)
        decisions: list[GovernanceDecision] = []

        lifecycle_decision = GovernanceEngine().require_runtime_execution(relationship.state)
        decisions.append(lifecycle_decision)
        if lifecycle_decision.outcome is not GovernanceOutcome.ALLOW:
            relationship.record_invocation_resolution(request.requested_by, request.request_id, "BLOCKED", reason=lifecycle_decision.reason)
            return InvocationPlan(request=request, outcome=lifecycle_decision.outcome, decisions=tuple(decisions), reason=lifecycle_decision.reason)

        for requirement in request.consent_requirements:
            decision = relationship.require_consent(requirement.actor, requirement.scope, purpose=requirement.purpose)
            decisions.append(decision)
            if decision.outcome is not GovernanceOutcome.ALLOW:
                relationship.record_invocation_resolution(request.requested_by, request.request_id, "BLOCKED", reason=decision.reason)
                return InvocationPlan(request=request, outcome=decision.outcome, decisions=tuple(decisions), reason=decision.reason)

        requirements = list(request.requirements)
        for resource in request.context_resources:
            read_requirement = CapabilityRequirement(resource, Capability.READ)
            if not any(item.resource == resource and item.capability is Capability.READ for item in requirements):
                requirements.append(read_requirement)

        for requirement in requirements:
            decision = relationship.check_capability(request.requested_by, requirement.resource, requirement.capability, purpose=requirement.purpose)
            decisions.append(decision)
            if decision.outcome is not GovernanceOutcome.ALLOW:
                relationship.record_invocation_resolution(request.requested_by, request.request_id, "BLOCKED", reason=decision.reason)
                return InvocationPlan(request=request, outcome=decision.outcome, decisions=tuple(decisions), reason=decision.reason)

        context = tuple(self._resolve_context(relationship, resource) for resource in request.context_resources)
        relationship.record_invocation_resolution(request.requested_by, request.request_id, "AUTHORIZED", reason="Lifecycle, consent, capability, and purpose requirements are active.")
        return InvocationPlan(request=request, outcome=GovernanceOutcome.ALLOW, decisions=tuple(decisions), context=context, reason="Lifecycle, consent, capability, and purpose requirements are active.")

    def record_result(self, relationship: Relationship, result: InvocationResult) -> None:
        relationship.record_invocation_result(result)

    @staticmethod
    def _resolve_context(relationship: Relationship, resource: str) -> ContextItem:
        if resource.startswith("claim:"):
            claim_id = resource.split(":", 1)[1]
            claim = relationship.state.claims.get(claim_id)
            if claim is None:
                raise KeyError(f"Unknown context resource: {resource}")
            return ContextItem(resource=resource, value=claim.content, epistemic_type=claim.epistemic_type.value, provenance=claim.derived_from or claim.source_refs)
        return ContextItem(resource=resource, value=None)
