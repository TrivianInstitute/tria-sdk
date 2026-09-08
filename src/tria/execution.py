from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Any, Callable, Protocol

from .core import Relationship
from .providers.base import ProviderAdapter, ProviderRequest, ProviderResponse
from .runtime import InvocationPlan, InvocationRequest, InvocationResult, Runtime
from .types import GovernanceDecision, GovernanceOutcome
from .errors import InvocationAlreadyStartedError, ExecutionError, InputValidationError


class Executor(Protocol):
    def __call__(self, request: ProviderRequest) -> Any: ...


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    plan: InvocationPlan
    provider_request: ProviderRequest | None
    provider_response: ProviderResponse | None
    result: InvocationResult | None

    @property
    def executed(self):
        """Executor was entered; this does not assert remote completion."""
        return self.provider_request is not None and self.result is not None


class ExecutionBridge:
    """Synchronous guarded local handoff. See docs/execution-bridge.md.

    prepare() is inspection only. execute() always resolves the original request
    after translation, even with a custom Runtime. The host owns the executor.
    """
    def __init__(self, runtime: Runtime | None = None):
        self.runtime = runtime or Runtime()

    def prepare(self, relationship, request, adapter, *, model, **options):
        plan = self.runtime.prepare(relationship, request)
        if not plan.allowed:
            return ExecutionReceipt(plan, None, None, None)
        try:
            wire = adapter.translate(plan, model=model, **options)
        except Exception:
            relationship.record_invocation_resolution(request.requested_by, request.request_id, "FAILED", reason="Provider preparation failed before executor entry.")
            raise
        if not isinstance(wire, ProviderRequest) or wire.request_id != request.request_id:
            raise InputValidationError("Adapter must return a ProviderRequest with the original request_id.")
        return ExecutionReceipt(plan, wire, None, None)

    @staticmethod
    def _changed_plan(request):
        d = GovernanceDecision(GovernanceOutcome.BLOCK, "core.execution.changed", "0.1", "Relationship changed reentrantly during final authorization; submit a fresh attempt after resolving the change.")
        return InvocationPlan(request, d.outcome, (d,), reason=d.reason)

    def execute(self, relationship, request, adapter, executor, *, model, **options):
        if not callable(executor) or inspect.iscoroutinefunction(executor):
            raise InputValidationError("executor must be a synchronous callable accepting ProviderRequest.")
        prepared = self.prepare(relationship, request, adapter, model=model, **options)
        if not prepared.plan.allowed:
            return prepared
        with relationship.execution_guard():
            if any(e.event_type == "InvocationExecutionReserved" and e.payload.get("request_id") == request.request_id for e in relationship.events):
                relationship.record_invocation_resolution(request.requested_by, request.request_id, "BLOCKED", reason="Duplicate execution reservation; reconcile the earlier attempt.")
                raise InvocationAlreadyStartedError("This request_id already reserved an execution attempt; reconcile it before creating a new attempt.")
            relationship._commit("InvocationExecutionReserved", "tria:governance", {"request_id": request.request_id, "requested_by": request.requested_by})
            before = tuple(e.event_id for e in relationship.events)
            final = Runtime.evaluate(relationship, request)
            if tuple(e.event_id for e in relationship.events) != before:
                final = self._changed_plan(request)
            recorded = Runtime.record_plan(relationship, final, operation="execution.final")
            if final.allowed and tuple(e.event_id for e in relationship.events) != before + tuple(recorded):
                final = self._changed_plan(request)
                Runtime.record_plan(relationship, final, operation="execution.final")
            if not final.allowed:
                return ExecutionReceipt(final, None, None, None)
            # Last check follows ALL preparation and store callbacks. No further
            # writes or extension callbacks occur between this check and entry.
            head = tuple(e.event_id for e in relationship.events)
            final = Runtime.evaluate(relationship, request)
            if tuple(e.event_id for e in relationship.events) != head:
                final = self._changed_plan(request)
            if not final.allowed:
                Runtime.record_plan(relationship, final, operation="execution.final")
                return ExecutionReceipt(final, None, None, None)
            final = InvocationPlan(request, final.outcome, final.decisions, prepared.plan.context, final.reason)
            try:
                native = executor(prepared.provider_request)
                if inspect.isawaitable(native):
                    if inspect.iscoroutine(native):
                        native.close()
                    raise InputValidationError("Async executor response is unsupported; use a synchronous executor.")
                response = (ProviderResponse(prepared.provider_request.provider, request.request_id, "UNKNOWN_EFFECT")
                    if native is None else adapter.normalize_response(request.request_id, native))
                if not isinstance(response, ProviderResponse) or response.request_id != request.request_id:
                    raise InputValidationError("Normalizer must return a ProviderResponse with the original request_id.")
                result = response.to_invocation_result()
            except Exception:
                result = InvocationResult(request.request_id, "executor:host", "UNKNOWN_EFFECT")
                relationship.record_invocation_result(result)
                raise ExecutionError(ExecutionReceipt(final, prepared.provider_request, None, result)) from None
            relationship.record_invocation_result(result)
            return ExecutionReceipt(final, prepared.provider_request, response, result)
