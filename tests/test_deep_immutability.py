import pytest

from tria import (
    GovernanceDecision,
    GovernanceOutcome,
    InvocationRequest,
    ProviderRequest,
    Tria,
)


def test_relational_event_payload_is_an_immutable_snapshot():
    participants = ["human:a", "agent:b"]
    metadata = {"nested": {"labels": ["one"]}}
    rel = Tria().create_relationship(participants)
    event = rel._commit("TestEvent", "human:a", metadata)

    participants.append("attacker")
    metadata["nested"]["labels"].append("two")

    assert event.payload["nested"]["labels"] == ("one",)
    assert event.verify_hash() is True
    with pytest.raises(TypeError):
        event.payload["new"] = "value"
    with pytest.raises(TypeError):
        event.payload["nested"]["new"] = "value"


def test_invocation_request_metadata_is_deeply_immutable():
    source = {"trace": {"labels": ["alpha"]}}
    request = InvocationRequest("human:a", "act", "agent:b", metadata=source)

    source["trace"]["labels"].append("beta")

    assert request.metadata["trace"]["labels"] == ("alpha",)
    with pytest.raises(TypeError):
        request.metadata["trace"]["extra"] = True


def test_provider_request_payload_and_metadata_are_deeply_immutable():
    payload = {"input": [{"role": "user", "content": "hello"}]}
    metadata = {"attempt": {"number": 1}}
    request = ProviderRequest("provider:test", "req-1", payload, metadata)

    payload["input"][0]["content"] = "changed"
    metadata["attempt"]["number"] = 2

    assert request.payload["input"][0]["content"] == "hello"
    assert request.metadata["attempt"]["number"] == 1
    with pytest.raises(TypeError):
        request.payload["input"][0]["content"] = "mutate"


def test_governance_decision_metadata_is_deeply_immutable():
    source = {"evidence": {"refs": ["event:1"]}}
    decision = GovernanceDecision(
        GovernanceOutcome.ALLOW,
        "policy:test",
        "0.1",
        "Allowed.",
        metadata=source,
    )

    source["evidence"]["refs"].append("event:2")

    assert decision.metadata["evidence"]["refs"] == ("event:1",)
    with pytest.raises(TypeError):
        decision.metadata["evidence"]["new"] = "value"
