from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from ..immutability import deep_freeze
from ..runtime import InvocationPlan, InvocationResult


class ProviderTranslationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    provider: str
    request_id: str
    payload: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", deep_freeze(self.payload))
        object.__setattr__(self, "metadata", deep_freeze(self.metadata))


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    provider: str
    request_id: str
    status: str
    output_ref: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", deep_freeze(self.metadata))

    def to_invocation_result(self) -> InvocationResult:
        return InvocationResult(
            request_id=self.request_id,
            produced_by=self.provider,
            status=self.status,
            output_ref=self.output_ref,
            metadata=self.metadata,
        )


class ProviderAdapter(Protocol):
    provider_name: str

    def translate(self, plan: InvocationPlan, *, model: str, **options: Any) -> ProviderRequest: ...

    def normalize_response(self, request_id: str, response: Any) -> ProviderResponse: ...


def require_allowed_plan(plan: InvocationPlan) -> None:
    if not plan.allowed:
        raise ProviderTranslationError("Blocked invocation plans cannot be translated for provider execution.")
