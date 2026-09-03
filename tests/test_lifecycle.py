import pytest

from tria import (
    Capability,
    GovernanceOutcome,
    InvocationRequest,
    LifecycleAuthorityError,
    LifecycleState,
    LifecycleTransitionError,
    Runtime,
    Tria,
)


def _relationship():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_lifecycle_authority("tria:system", "human:a")
    return rel


def _activate(rel):
    rel.transition("human:a", LifecycleState.ACTIVE)


def _dissolve(rel):
    if rel.state.lifecycle is LifecycleState.FORMING:
        rel.transition("human:a", LifecycleState.DISSOLVING)
    elif rel.state.lifecycle is not LifecycleState.DISSOLVING:
        rel.transition("human:a", LifecycleState.DISSOLVING)
    rel.transition("human:a", LifecycleState.DISSOLVED)


def test_resting_preserves_read_but_blocks_action():
    rel = _relationship()
    rel.grant_permission("human:a", "agent:b", "resource:x", Capability.READ)
    rel.grant_permission("human:a", "agent:b", "resource:x", Capability.ACT)
    _activate(rel)
    rel.transition("human:a", LifecycleState.RESTING)

    assert rel.check_capability("agent:b", "resource:x", Capability.READ).outcome is GovernanceOutcome.ALLOW
    assert rel.check_capability("agent:b", "resource:x", Capability.ACT).outcome is GovernanceOutcome.BLOCK


def test_dormant_and_dissolving_block_derivation():
    dormant = _relationship()
    dormant.grant_permission("human:a", "agent:b", "resource:x", Capability.DERIVE)
    _activate(dormant)
    dormant.transition("human:a", LifecycleState.RESTING)
    dormant.transition("human:a", LifecycleState.DORMANT)
    assert dormant.check_capability("agent:b", "resource:x", Capability.DERIVE).outcome is GovernanceOutcome.BLOCK

    dissolving = _relationship()
    dissolving.grant_permission("human:a", "agent:b", "resource:x", Capability.DERIVE)
    dissolving.transition("human:a", LifecycleState.DISSOLVING)
    assert dissolving.check_capability("agent:b", "resource:x", Capability.DERIVE).outcome is GovernanceOutcome.BLOCK


def test_dissolved_relationship_blocks_all_capabilities():
    rel = _relationship()
    for capability in Capability:
        rel.grant_permission("human:a", "agent:b", "resource:x", capability)
    _dissolve(rel)

    for capability in Capability:
        assert rel.check_capability("agent:b", "resource:x", capability).outcome is GovernanceOutcome.BLOCK


def test_runtime_pauses_when_relationship_is_resting_even_without_requirements():
    rel = _relationship()
    _activate(rel)
    rel.transition("human:a", LifecycleState.RESTING)

    plan = Runtime().prepare(rel, InvocationRequest(requested_by="agent:b", action="say hello", target="executor:any"))

    assert plan.allowed is False
    assert plan.outcome is GovernanceOutcome.PAUSE
    assert plan.context == ()


def test_runtime_blocks_after_dissolution():
    rel = _relationship()
    _dissolve(rel)

    plan = Runtime().prepare(rel, InvocationRequest(requested_by="agent:b", action="continue", target="executor:any"))

    assert plan.allowed is False
    assert plan.outcome is GovernanceOutcome.BLOCK


def test_unauthorized_actor_cannot_change_lifecycle():
    rel = _relationship()
    with pytest.raises(LifecycleAuthorityError):
        rel.transition("agent:b", LifecycleState.ACTIVE)
    assert rel.state.lifecycle is LifecycleState.FORMING


def test_lifecycle_authority_is_event_sourced_and_revocable():
    rel = _relationship()
    assert rel.state.lifecycle_authorities["human:a"].active is True
    rel.revoke_lifecycle_authority("human:a", "human:a")
    assert rel.state.lifecycle_authorities["human:a"].active is False
    with pytest.raises(LifecycleAuthorityError):
        rel.transition("human:a", LifecycleState.ACTIVE)


def test_illegal_transition_fails_closed():
    rel = _relationship()
    with pytest.raises(LifecycleTransitionError):
        rel.transition("human:a", LifecycleState.DISSOLVED)
    assert rel.state.lifecycle is LifecycleState.FORMING


def test_dissolved_is_terminal():
    rel = _relationship()
    _dissolve(rel)
    with pytest.raises(LifecycleTransitionError):
        rel.transition("human:a", LifecycleState.ACTIVE)
    assert rel.state.lifecycle is LifecycleState.DISSOLVED


def test_consent_does_not_change_lifecycle():
    rel = _relationship()
    rel.grant_consent("human:a", "persistent_context")
    assert rel.state.lifecycle is LifecycleState.FORMING
    assert rel.require_consent("human:a", "persistent_context").outcome is GovernanceOutcome.ALLOW
