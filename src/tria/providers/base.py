from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

import json
from ..immutability import deep_freeze, deep_thaw
from ..errors import InputValidationError, text_field
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


    def to_transport_payload(self) -> dict[str, Any]:
        """Detached JSON-ready payload; never mutates the authorized snapshot."""
        try:
            return json.loads(json.dumps(deep_thaw(self.payload), allow_nan=False))
        except (TypeError, ValueError):
            raise ProviderTranslationError("Transport payload must contain JSON-compatible values; remove unsupported host configuration.") from None


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


def validate_options(options, allowed):
    if set(options) - set(allowed):
        raise ProviderTranslationError("Unsupported adapter option; prompt/context overrides are prohibited. Use documented host configuration fields only.")
