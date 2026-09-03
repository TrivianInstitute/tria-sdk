from tria import (
    Capability,
    CapabilityRequirement,
    EpistemicType,
    GovernanceOutcome,
    InvocationRequest,
    InvocationResult,
    Runtime,
    Tria,
)


def _relationship_with_claim():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    claim = rel.register_claim(
        "human:a",
        EpistemicType.OBSERVATION,
        "The participant selected option A.",
        source_refs=["ui:selection:1"],
    )
    return rel, claim


def test_runtime_fails_closed_without_read_permission():
    rel, claim = _relationship_with_claim()
    resource = f"claim:{claim.claim_id}"
    request = InvocationRequest(
        requested_by="agent:b",
        action="reason",
        target="executor:any",
        context_resources=(resource,),
    )

    plan = Runtime().prepare(rel, request)

    assert plan.allowed is False
    assert plan.outcome is GovernanceOutcome.BLOCK
    assert plan.context == ()


def test_runtime_exposes_only_explicit_read_authorized_context():
    rel, claim = _relationship_with_claim()
    resource = f"claim:{claim.claim_id}"
    rel.grant_permission("human:a", "agent:b", resource, Capability.READ)

    plan = Runtime().prepare(
        rel,
        InvocationRequest(
            requested_by="agent:b",
            action="reason",
            target="executor:any",
            context_resources=(resource,),
        ),
    )

    assert plan.allowed is True
    assert len(plan.context) == 1
    assert plan.context[0].resource == resource
    assert plan.context[0].value == "The participant selected option A."
    assert plan.context[0].epistemic_type == "OBSERVATION"


def test_read_permission_does_not_satisfy_derive_requirement():
    rel, claim = _relationship_with_claim()
    resource = f"claim:{claim.claim_id}"
    rel.grant_permission("human:a", "agent:b", resource, Capability.READ)

    plan = Runtime().prepare(
        rel,
        InvocationRequest(
            requested_by="agent:b",
            action="infer",
            target="executor:any",
            context_resources=(resource,),
            requirements=(CapabilityRequirement(resource, Capability.DERIVE),),
        ),
    )

    assert plan.allowed is False
    assert plan.outcome is GovernanceOutcome.BLOCK
    assert plan.context == ()


def test_runtime_records_proposal_resolution_and_result_without_provider_concepts():
    rel, claim = _relationship_with_claim()
    resource = f"claim:{claim.claim_id}"
    rel.grant_permission("human:a", "agent:b", resource, Capability.READ)
    runtime = Runtime()
    request = InvocationRequest(
        requested_by="agent:b",
        action="summarize",
        target="executor:local",
        context_resources=(resource,),
    )

    plan = runtime.prepare(rel, request)
    assert plan.allowed is True

    runtime.record_result(
        rel,
        InvocationResult(
            request_id=request.request_id,
            produced_by="executor:local",
            status="COMPLETED",
            output_ref="artifact:summary:1",
        ),
    )

    event_types = [event.event_type for event in rel.events]
    assert "InvocationProposed" in event_types
    assert "InvocationResolved" in event_types
    assert "InvocationResultRecorded" in event_types
    assert rel.audit()["chain_valid"] is True
