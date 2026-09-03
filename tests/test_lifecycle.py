from tria import Capability, GovernanceOutcome, InvocationRequest, LifecycleState, Runtime, Tria


def test_resting_preserves_read_but_blocks_action():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_permission("human:a", "agent:b", "resource:x", Capability.READ)
    rel.grant_permission("human:a", "agent:b", "resource:x", Capability.ACT)
    rel.transition("human:a", LifecycleState.RESTING)

    assert rel.check_capability("agent:b", "resource:x", Capability.READ).outcome is GovernanceOutcome.ALLOW
    assert rel.check_capability("agent:b", "resource:x", Capability.ACT).outcome is GovernanceOutcome.BLOCK


def test_dormant_and_dissolving_block_derivation():
    for state in (LifecycleState.DORMANT, LifecycleState.DISSOLVING):
        rel = Tria().create_relationship(["human:a", "agent:b"])
        rel.grant_permission("human:a", "agent:b", "resource:x", Capability.DERIVE)
        rel.transition("human:a", state)
        assert rel.check_capability("agent:b", "resource:x", Capability.DERIVE).outcome is GovernanceOutcome.BLOCK


def test_dissolved_relationship_blocks_all_capabilities():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    for capability in Capability:
        rel.grant_permission("human:a", "agent:b", "resource:x", capability)
    rel.transition("human:a", LifecycleState.DISSOLVED)

    for capability in Capability:
        assert rel.check_capability("agent:b", "resource:x", capability).outcome is GovernanceOutcome.BLOCK


def test_runtime_pauses_when_relationship_is_resting_even_without_requirements():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.transition("human:a", LifecycleState.RESTING)

    plan = Runtime().prepare(
        rel,
        InvocationRequest(requested_by="agent:b", action="say hello", target="executor:any"),
    )

    assert plan.allowed is False
    assert plan.outcome is GovernanceOutcome.PAUSE
    assert plan.context == ()


def test_runtime_blocks_after_dissolution():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.transition("human:a", LifecycleState.DISSOLVED)

    plan = Runtime().prepare(
        rel,
        InvocationRequest(requested_by="agent:b", action="continue", target="executor:any"),
    )

    assert plan.allowed is False
    assert plan.outcome is GovernanceOutcome.BLOCK
