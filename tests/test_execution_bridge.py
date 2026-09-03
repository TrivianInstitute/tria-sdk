from tria import (
    Capability,
    EpistemicType,
    ExecutionBridge,
    InvocationRequest,
    OpenAIResponsesAdapter,
    Tria,
)


def _relationship_with_readable_claim():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    obs = rel.register_claim(
        "agent:b",
        EpistemicType.OBSERVATION,
        "Latency increased.",
        source_refs=["sensor:latency"],
    )
    resource = f"claim:{obs.claim_id}"
    rel.grant_permission("human:a", "agent:b", resource, Capability.READ)
    return rel, resource


def test_execution_bridge_calls_injected_executor_and_records_result():
    rel, resource = _relationship_with_readable_claim()
    request = InvocationRequest(
        requested_by="agent:b",
        action="Assess the observation.",
        target="model",
        context_resources=(resource,),
    )
    calls = []

    def fake_executor(provider_request):
        calls.append(provider_request)
        return {"id": "resp_123", "status": "completed"}

    receipt = ExecutionBridge().execute(
        rel,
        request,
        OpenAIResponsesAdapter(),
        fake_executor,
        model="example-model",
    )

    assert receipt.executed is True
    assert len(calls) == 1
    assert receipt.result is not None
    assert receipt.result.output_ref == "resp_123"
    assert any(event.event_type == "InvocationResultRecorded" for event in rel.events)


def test_blocked_plan_never_calls_executor():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    obs = rel.register_claim(
        "agent:b",
        EpistemicType.OBSERVATION,
        "Latency increased.",
        source_refs=["sensor:latency"],
    )
    request = InvocationRequest(
        requested_by="agent:b",
        action="Assess the observation.",
        target="model",
        context_resources=(f"claim:{obs.claim_id}",),
    )
    called = False

    def fake_executor(provider_request):
        nonlocal called
        called = True
        return {"id": "should-not-run"}

    receipt = ExecutionBridge().execute(
        rel,
        request,
        OpenAIResponsesAdapter(),
        fake_executor,
        model="example-model",
    )

    assert receipt.executed is False
    assert called is False
    assert receipt.provider_request is None


def test_prepare_supports_manual_network_handoff():
    rel, resource = _relationship_with_readable_claim()
    request = InvocationRequest(
        requested_by="agent:b",
        action="Assess the observation.",
        target="model",
        context_resources=(resource,),
    )

    receipt = ExecutionBridge().prepare(
        rel,
        request,
        OpenAIResponsesAdapter(),
        model="example-model",
    )

    assert receipt.plan.allowed is True
    assert receipt.provider_request is not None
    assert receipt.executed is False
