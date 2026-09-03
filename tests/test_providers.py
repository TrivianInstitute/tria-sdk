import pytest

from tria import (
    AnthropicMessagesAdapter,
    Capability,
    EpistemicType,
    InvocationRequest,
    OpenAIResponsesAdapter,
    ProviderTranslationError,
    Runtime,
    Tria,
)


def _allowed_plan():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    claim = rel.register_claim(
        "human:a",
        EpistemicType.OBSERVATION,
        "Preferred language is concise English.",
        source_refs=["participant:self-report"],
    )
    resource = f"claim:{claim.claim_id}"
    rel.grant_permission("human:a", "agent:b", resource, Capability.READ)
    request = InvocationRequest(
        requested_by="agent:b",
        action="Draft a short reply.",
        target="language-model",
        context_resources=(resource,),
    )
    return Runtime().prepare(rel, request)


def test_openai_adapter_translates_only_allowed_plan():
    plan = _allowed_plan()
    request = OpenAIResponsesAdapter().translate(plan, model="gpt-test")
    assert request.provider == "openai"
    assert request.payload["model"] == "gpt-test"
    assert request.payload["input"][-1]["role"] == "user"
    assert "Preferred language is concise English." in request.payload["input"][0]["content"][0]["text"]


def test_anthropic_adapter_translates_only_allowed_plan():
    plan = _allowed_plan()
    request = AnthropicMessagesAdapter().translate(plan, model="claude-test", max_tokens=256)
    assert request.provider == "anthropic"
    assert request.payload["model"] == "claude-test"
    assert request.payload["max_tokens"] == 256
    assert "Preferred language is concise English." in request.payload["system"]


def test_blocked_plan_cannot_reach_provider_adapter():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    claim = rel.register_claim(
        "human:a",
        EpistemicType.OBSERVATION,
        "Private context.",
        source_refs=["participant:self-report"],
    )
    plan = Runtime().prepare(
        rel,
        InvocationRequest(
            requested_by="agent:b",
            action="Use private context.",
            target="language-model",
            context_resources=(f"claim:{claim.claim_id}",),
        ),
    )
    assert not plan.allowed
    with pytest.raises(ProviderTranslationError):
        OpenAIResponsesAdapter().translate(plan, model="gpt-test")


def test_provider_response_normalizes_to_generic_result():
    response = OpenAIResponsesAdapter().normalize_response("req-1", {"id": "resp-1", "status": "completed"})
    result = response.to_invocation_result()
    assert result.request_id == "req-1"
    assert result.produced_by == "openai"
    assert result.output_ref == "resp-1"


def test_anthropic_response_normalizes_without_sdk_dependency():
    response = AnthropicMessagesAdapter().normalize_response("req-2", {"id": "msg-1", "stop_reason": "end_turn"})
    result = response.to_invocation_result()
    assert result.produced_by == "anthropic"
    assert result.output_ref == "msg-1"
    assert result.metadata["stop_reason"] == "end_turn"
