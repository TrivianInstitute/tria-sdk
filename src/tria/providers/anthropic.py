from __future__ import annotations

from typing import Any

from .base import ProviderTranslationError, ProviderRequest, ProviderResponse, require_allowed_plan, validate_options
from ..runtime import InvocationPlan


class AnthropicMessagesAdapter:
    """Translate an authorized TRIA plan into an Anthropic Messages-style payload.

    This adapter performs no network I/O and imports no Anthropic SDK objects.
    """

    provider_name = "anthropic"

    def translate(self, plan: InvocationPlan, *, model: str, **options: Any) -> ProviderRequest:
        require_allowed_plan(plan)
        validate_options(options, {"max_tokens", "temperature", "top_p", "top_k", "stop_sequences"})
        if not isinstance(options.get("max_tokens", 1024), int) or isinstance(options.get("max_tokens", 1024), bool) or options.get("max_tokens", 1024) <= 0:
            raise ProviderTranslationError("max_tokens must be a positive integer.")
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
        status = "COMPLETED" if response_id and stop_reason in {"end_turn", "max_tokens", "stop_sequence", "tool_use"} else "UNKNOWN_EFFECT"
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
