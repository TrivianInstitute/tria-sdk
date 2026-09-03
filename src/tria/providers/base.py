from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from ..runtime import InvocationPlan, InvocationResult


class ProviderTranslationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    provider: str
    request_id: str
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    provider: str
    request_id: str
    status: str
    output_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_invocation_result(self) -> InvocationResult:
        return InvocationResult(
            request_id=self.request_id,
            produced_by=self.provider,
            status=self.status,
            output_ref=self.output_ref,
            metadata=dict(self.metadata),
        )


class ProviderAdapter(Protocol):
    provider_name: str

    def translate(self, plan: InvocationPlan, *, model: str, **options: Any) -> ProviderRequest: ...

    def normalize_response(self, request_id: str, response: Any) -> ProviderResponse: ...


def require_allowed_plan(plan: InvocationPlan) -> None:
    if not plan.allowed:
        raise ProviderTranslationError("Blocked invocation plans cannot be translated for provider execution.")
