from tria import Capability, GovernanceOutcome, LifecycleState, Runtime, InvocationRequest, Tria


def test_capability_check_does_not_append_history():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_permission("human:a", "agent:b", "resource:x", Capability.READ)
    before = len(rel.events)

    decision = rel.check_capability("agent:b", "resource:x", Capability.READ)

    assert decision.outcome is GovernanceOutcome.ALLOW
    assert len(rel.events) == before


def test_consent_and_policy_checks_are_pure():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_consent("human:a", "scope:x")
    rel.grant_policy_authority("tria:system", "human:a", "scope:x")
    rel.register_policy("human:a", "policy:x", "1.0", "scope:x")
    rel.adopt_policy("human:a", "policy:x", "1.0", "scope:x")
    before = len(rel.events)

    assert rel.require_consent("human:a", "scope:x").outcome is GovernanceOutcome.ALLOW
    assert rel.check_policy_adoption("policy:x", "1.0").outcome is GovernanceOutcome.ALLOW
    assert rel.check_policy_authority("human:a", "scope:x").outcome is GovernanceOutcome.ALLOW
    assert len(rel.events) == before


def test_lifecycle_checks_are_pure():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_lifecycle_authority("tria:system", "human:a")
    before = len(rel.events)

    assert rel.check_lifecycle_authority("human:a").outcome is GovernanceOutcome.ALLOW
    assert rel.check_lifecycle_transition(LifecycleState.ACTIVE).outcome is GovernanceOutcome.ALLOW
    assert len(rel.events) == before


def test_explicit_audit_record_appends_governance_event():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_permission("human:a", "agent:b", "resource:x", Capability.READ)
    decision = rel.check_capability("agent:b", "resource:x", Capability.READ)
    before = len(rel.events)

    event = rel.record_governance_decision(
        decision,
        operation="manual-check",
        grantee="agent:b",
        resource="resource:x",
        capability=Capability.READ.value,
    )

    assert len(rel.events) == before + 1
    assert event.event_type == "GovernanceEvaluated"
    assert event.payload["operation"] == "manual-check"


def test_runtime_explicitly_records_its_governance_decisions():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    before = len(rel.events)

    plan = Runtime().prepare(
        rel,
        InvocationRequest(requested_by="agent:b", action="hello", target="executor:any"),
    )

    assert plan.allowed is True
    new_events = rel.events[before:]
    assert any(event.event_type == "GovernanceEvaluated" for event in new_events)
    assert any(event.event_type == "InvocationResolved" for event in new_events)
