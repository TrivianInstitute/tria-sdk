from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from .core import Relationship
from .providers.base import ProviderAdapter, ProviderRequest, ProviderResponse
from .runtime import InvocationPlan, InvocationRequest, InvocationResult, Runtime


class Executor(Protocol):
    def __call__(self, request: ProviderRequest) -> Any: ...


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    plan: InvocationPlan
    provider_request: ProviderRequest | None
    provider_response: ProviderResponse | None
    result: InvocationResult | None

    @property
    def executed(self) -> bool:
        return self.provider_request is not None and self.result is not None


class ExecutionBridge:
    """Compose Runtime governance, provider translation, and caller-owned execution.

    TRIA never owns credentials or network transport. The caller supplies an
    executor callable that accepts a ProviderRequest and returns a provider-native
    response. Blocked plans are returned without invoking the executor.
    """

    def __init__(self, runtime: Runtime | None = None) -> None:
        self.runtime = runtime or Runtime()

    def prepare(
        self,
        relationship: Relationship,
        request: InvocationRequest,
        adapter: ProviderAdapter,
        *,
        model: str,
        **options: Any,
    ) -> ExecutionReceipt:
        plan = self.runtime.prepare(relationship, request)
        if not plan.allowed:
            return ExecutionReceipt(plan=plan, provider_request=None, provider_response=None, result=None)
        provider_request = adapter.translate(plan, model=model, **options)
        return ExecutionReceipt(plan=plan, provider_request=provider_request, provider_response=None, result=None)

    def execute(
        self,
        relationship: Relationship,
        request: InvocationRequest,
        adapter: ProviderAdapter,
        executor: Executor | Callable[[ProviderRequest], Any],
        *,
        model: str,
        **options: Any,
    ) -> ExecutionReceipt:
        prepared = self.prepare(relationship, request, adapter, model=model, **options)
        if not prepared.plan.allowed or prepared.provider_request is None:
            return prepared

        native_response = executor(prepared.provider_request)
        provider_response = adapter.normalize_response(prepared.provider_request.request_id, native_response)
        result = provider_response.to_invocation_result()
        self.runtime.record_result(relationship, result)
        return ExecutionReceipt(
            plan=prepared.plan,
            provider_request=prepared.provider_request,
            provider_response=provider_response,
            result=result,
        )
