from __future__ import annotations

from typing import Any

from .base import ProviderRequest, ProviderResponse, require_allowed_plan
from ..runtime import InvocationPlan


class OpenAIResponsesAdapter:
    """Translate an authorized TRIA plan into an OpenAI Responses-style payload.

    This adapter performs no network I/O and imports no OpenAI SDK objects.
    """

    provider_name = "openai"

    def translate(self, plan: InvocationPlan, *, model: str, **options: Any) -> ProviderRequest:
        require_allowed_plan(plan)
        context = [
            {
                "resource": item.resource,
                "value": item.value,
                "epistemic_type": item.epistemic_type,
                "provenance": list(item.provenance),
            }
            for item in plan.context
        ]
        input_items = []
        if context:
            input_items.append({"role": "developer", "content": [{"type": "input_text", "text": _context_text(context)}]})
        input_items.append({"role": "user", "content": [{"type": "input_text", "text": plan.request.action}]})
        payload: dict[str, Any] = {"model": model, "input": input_items}
        payload.update(options)
        return ProviderRequest(provider=self.provider_name, request_id=plan.request.request_id, payload=payload)

    def normalize_response(self, request_id: str, response: Any) -> ProviderResponse:
        response_id = _get(response, "id")
        status = _get(response, "status") or "completed"
        return ProviderResponse(
            provider=self.provider_name,
            request_id=request_id,
            status=str(status),
            output_ref=str(response_id) if response_id else None,
        )


def _get(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _context_text(context: list[dict[str, Any]]) -> str:
    lines = ["Governed relational context follows. Preserve epistemic labels and provenance."]
    for item in context:
        lines.append(f"[{item['resource']}] {item['epistemic_type'] or 'UNCLASSIFIED'}: {item['value']!s}")
        if item["provenance"]:
            lines.append(f"provenance: {', '.join(item['provenance'])}")
    return "\n".join(lines)
