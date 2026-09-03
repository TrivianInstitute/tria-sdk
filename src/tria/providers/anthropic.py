from __future__ import annotations

from typing import Any

from .base import ProviderRequest, ProviderResponse, require_allowed_plan
from ..runtime import InvocationPlan


class AnthropicMessagesAdapter:
    """Translate an authorized TRIA plan into an Anthropic Messages-style payload.

    This adapter performs no network I/O and imports no Anthropic SDK objects.
    """

    provider_name = "anthropic"

    def translate(self, plan: InvocationPlan, *, model: str, **options: Any) -> ProviderRequest:
        require_allowed_plan(plan)
        system = None
        if plan.context:
            system = _context_text(plan)
        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": int(options.pop("max_tokens", 1024)),
            "messages": [{"role": "user", "content": plan.request.action}],
        }
        if system is not None:
            payload["system"] = system
        payload.update(options)
        return ProviderRequest(provider=self.provider_name, request_id=plan.request.request_id, payload=payload)

    def normalize_response(self, request_id: str, response: Any) -> ProviderResponse:
        response_id = _get(response, "id")
        stop_reason = _get(response, "stop_reason")
        status = "completed" if stop_reason else "unknown"
        return ProviderResponse(
            provider=self.provider_name,
            request_id=request_id,
            status=status,
            output_ref=str(response_id) if response_id else None,
            metadata={"stop_reason": stop_reason} if stop_reason else {},
        )


def _get(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _context_text(plan: InvocationPlan) -> str:
    lines = ["Governed relational context follows. Preserve epistemic labels and provenance."]
    for item in plan.context:
        lines.append(f"[{item.resource}] {item.epistemic_type or 'UNCLASSIFIED'}: {item.value!s}")
        if item.provenance:
            lines.append(f"provenance: {', '.join(item.provenance)}")
    return "\n".join(lines)
