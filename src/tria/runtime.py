from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from .core import Relationship
from .governance import GovernanceEngine
from .errors import InputValidationError, UnknownResourceError, text_field, enum_field, conditions_field, content_field
from .immutability import deep_freeze
from .types import Capability, GovernanceDecision, GovernanceOutcome


@dataclass(frozen=True, slots=True)
class CapabilityRequirement:
    resource: str
    capability: Capability
    purpose: str | None = None
    satisfied_conditions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        text_field(self.resource, "resource")
        enum_field(self.capability, Capability, "capability")
        object.__setattr__(self, "satisfied_conditions", conditions_field(self.satisfied_conditions, "satisfied_conditions"))
        if self.purpose is not None:
            text_field(self.purpose, "purpose")
        for condition in self.satisfied_conditions:
            text_field(condition, "condition")


@dataclass(frozen=True, slots=True)
class ConsentRequirement:
    actor: str
    scope: str
    purpose: str | None = None
    satisfied_conditions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        text_field(self.actor, "actor")
        text_field(self.scope, "scope")
        object.__setattr__(self, "satisfied_conditions", conditions_field(self.satisfied_conditions, "satisfied_conditions"))
        if self.purpose is not None:
            text_field(self.purpose, "purpose")
        for condition in self.satisfied_conditions:
            text_field(condition, "condition")


@dataclass(frozen=True, slots=True)
class InvocationRequest:
    requested_by: str
    action: str
    target: str
    context_resources: tuple[str, ...] = ()
    requirements: tuple[CapabilityRequirement, ...] = ()
    consent_requirements: tuple[ConsentRequirement, ...] = ()
    request_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: Mapping[str, Any] = field(default_factory=dict)
    action_ref: str | None = None

    def __post_init__(self) -> None:
        content_field(self.action, "action")
        if not isinstance(self.metadata, Mapping):
            raise InputValidationError("metadata must be a mapping.")
        for name in ("requested_by", "target", "request_id"):
            text_field(getattr(self, name), name)
        for name, kind in (("context_resources", str), ("requirements", CapabilityRequirement), ("consent_requirements", ConsentRequirement)):
            values = getattr(self, name)
            if not isinstance(values, (list, tuple)) or any(not isinstance(v, kind) for v in values):
                raise InputValidationError(f"{name} must be a sequence of {kind.__name__} values.")
        for resource in self.context_resources:
            text_field(resource, "context resource")
        object.__setattr__(self, "context_resources", tuple(self.context_resources))
        object.__setattr__(self, "requirements", tuple(self.requirements))
        object.__setattr__(self, "consent_requirements", tuple(self.consent_requirements))
        object.__setattr__(self, "metadata", deep_freeze(self.metadata))


@dataclass(frozen=True, slots=True)
class ContextItem:
    resource: str
    value: Any
    epistemic_type: str | None = None
    provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        text_field(self.resource, "resource")
        object.__setattr__(self, "value", deep_freeze(self.value))
        object.__setattr__(self, "provenance", tuple(self.provenance))


@dataclass(frozen=True, slots=True)
class InvocationPlan:
    request: InvocationRequest
    outcome: GovernanceOutcome
    decisions: tuple[GovernanceDecision, ...]
    context: tuple[ContextItem, ...] = ()
    reason: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "decisions", tuple(self.decisions))
        object.__setattr__(self, "context", tuple(self.context))

    @property
    def allowed(self) -> bool:
        return self.outcome is GovernanceOutcome.ALLOW


@dataclass(frozen=True, slots=True)
class InvocationResult:
    request_id: str
    produced_by: str
    status: str
    output_ref: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", deep_freeze(self.metadata))


class Runtime:
    """Prepare context; ALLOW is a snapshot, never an executor authorization token.

    A host resolver is optional: callable(resource: str) -> ContextItem. It is
    invoked only for authorized non-claim resources. ExecutionBridge revalidates
    after all preparation callbacks.
    """
    def __init__(self, resource_resolver=None):
        if resource_resolver is not None and not callable(resource_resolver):
            raise InputValidationError("resource_resolver must be callable or None.")
        self.resource_resolver = resource_resolver

    @staticmethod
    def _resolution_status(outcome):
        return "PAUSED" if outcome is GovernanceOutcome.PAUSE else "BLOCKED"

    @staticmethod
    def evaluate(relationship, request):
        """Shared pure checks, always including core floors; no context callback."""
        if not isinstance(request, InvocationRequest):
            raise InputValidationError("Runtime requires an InvocationRequest.")
        state = relationship.state
        decisions = []
        core = GovernanceEngine()
        lifecycle = core.require_runtime_execution(state)
        if lifecycle.outcome is GovernanceOutcome.ALLOW:
            lifecycle = relationship._governance.require_runtime_execution(state)
        decisions.append(lifecycle)
        if lifecycle.outcome is GovernanceOutcome.ALLOW and request.requested_by not in state.participants:
            decisions.append(GovernanceDecision(GovernanceOutcome.BLOCK, "core.participant", "0.1", "Requester is not a registered participant; bind an authenticated participant in the host."))
        if all(d.outcome is GovernanceOutcome.ALLOW for d in decisions):
            for requirement in request.consent_requirements:
                d = relationship.require_consent(requirement.actor, requirement.scope, purpose=requirement.purpose, satisfied_conditions=requirement.satisfied_conditions)
                decisions.append(d)
                if d.outcome is not GovernanceOutcome.ALLOW:
                    break
        if all(d.outcome is GovernanceOutcome.ALLOW for d in decisions):
            requirements = list(request.requirements)
            for resource in request.context_resources:
                if not any(x.resource == resource and x.capability is Capability.READ for x in requirements):
                    requirements.append(CapabilityRequirement(resource, Capability.READ))
            for requirement in requirements:
                d = relationship.check_capability(request.requested_by, requirement.resource, requirement.capability, purpose=requirement.purpose, satisfied_conditions=requirement.satisfied_conditions)
                decisions.append(d)
                if d.outcome is not GovernanceOutcome.ALLOW:
                    break
        denied = next((d for d in decisions if d.outcome is not GovernanceOutcome.ALLOW), None)
        return InvocationPlan(request, denied.outcome if denied else GovernanceOutcome.ALLOW, tuple(decisions), reason=denied.reason if denied else "Declared lifecycle, consent, capability, purpose, expiry and condition requirements are active.")

    @staticmethod
    def record_plan(relationship, plan, *, operation):
        ids = []
        for d in plan.decisions:
            e = relationship.record_governance_decision(d, operation=operation, request_id=plan.request.request_id, requested_by=plan.request.requested_by)
            ids.append(e.event_id)
        e = relationship.record_invocation_resolution(plan.request.requested_by, plan.request.request_id, "AUTHORIZED" if plan.allowed else Runtime._resolution_status(plan.outcome), reason=plan.reason)
        ids.append(e.event_id)
        return ids

    def prepare(self, relationship, request):
        if not isinstance(request, InvocationRequest):
            raise InputValidationError("Runtime requires an InvocationRequest.")
        relationship.record_invocation_proposed(request)
        plan = Runtime.evaluate(relationship, request)
        if not plan.allowed:
            Runtime.record_plan(relationship, plan, operation="runtime.prepare")
            return plan
        try:
            context = tuple(self._resolve_context(relationship, r) for r in request.context_resources)
        except Exception:
            relationship.record_invocation_resolution(request.requested_by, request.request_id, "FAILED", reason="Context preparation failed; check resource resolver configuration.")
            raise
        Runtime.record_plan(relationship, plan, operation="runtime.prepare")
        return InvocationPlan(request, plan.outcome, plan.decisions, context, plan.reason)

    def record_result(self, relationship, result):
        relationship.record_invocation_result(result)

    def _resolve_context(self, relationship, resource):
        if resource.startswith("claim:"):
            claim = relationship.state.claims.get(resource.split(":", 1)[1])
            if claim is None:
                raise UnknownResourceError("Claim context does not exist; verify its claim identifier before requesting it.")
            return ContextItem(resource, claim.content, claim.epistemic_type.value, claim.derived_from or claim.source_refs)
        if self.resource_resolver is None:
            raise UnknownResourceError("External context requires Runtime(resource_resolver=callable); permission does not supply data.")
        item = self.resource_resolver(resource)
        if not isinstance(item, ContextItem) or item.resource != resource:
            raise UnknownResourceError("Resolver must return a ContextItem for exactly the requested resource.")
        return item
