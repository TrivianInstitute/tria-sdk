import pytest

from tria import Capability, DelegationError, GovernanceOutcome, PolicyAuthorityError, Tria


def test_permission_delegation_requires_delegate_capability():
    rel = Tria().create_relationship(["human:a", "agent:b", "agent:c"])

    with pytest.raises(DelegationError):
        rel.delegate_permission("agent:b", "agent:c", "resource:x", Capability.READ)

    rel.grant_permission("human:a", "agent:b", "resource:x", Capability.DELEGATE)
    rel.delegate_permission("agent:b", "agent:c", "resource:x", Capability.READ)

    assert rel.check_capability("agent:c", "resource:x", Capability.READ).outcome is GovernanceOutcome.ALLOW


def test_policy_authority_can_only_be_delegated_by_authorized_actor():
    rel = Tria().create_relationship(["human:a", "human:b"])

    with pytest.raises(PolicyAuthorityError):
        rel.grant_policy_authority("human:a", "human:b", "relationship")

    rel.grant_policy_authority("tria:system", "human:a", "relationship")
    rel.grant_policy_authority("human:a", "human:b", "relationship")

    assert rel.state.policy_authorities[("human:b", "relationship")].active is True


def test_cross_actor_permission_race_fails_closed_when_causally_ambiguous():
    rel = Tria().create_relationship(["human:a", "human:b", "agent:c"])

    rel.revoke_permission("human:b", "agent:c", "resource:x", Capability.READ)
    rel.grant_permission("human:a", "agent:c", "resource:x", Capability.READ)

    decision = rel.check_capability("agent:c", "resource:x", Capability.READ)
    assert decision.outcome is GovernanceOutcome.BLOCK
    assert decision.policy_id == "core.permission.race"


def test_causal_parent_resolves_cross_actor_permission_order():
    rel = Tria().create_relationship(["human:a", "human:b", "agent:c"])

    revoke = rel.revoke_permission("human:b", "agent:c", "resource:x", Capability.READ)
    rel.grant_permission(
        "human:a",
        "agent:c",
        "resource:x",
        Capability.READ,
        causal_parents=(revoke.event_id,),
    )

    assert rel.check_capability("agent:c", "resource:x", Capability.READ).outcome is GovernanceOutcome.ALLOW


def test_same_actor_sequence_resolves_permission_order_without_explicit_parent():
    rel = Tria().create_relationship(["human:a", "agent:b"])

    rel.grant_permission("human:a", "agent:b", "resource:x", Capability.READ)
    rel.revoke_permission("human:a", "agent:b", "resource:x", Capability.READ)

    assert rel.check_capability("agent:b", "resource:x", Capability.READ).outcome is GovernanceOutcome.BLOCK
