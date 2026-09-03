from tria import Capability, GovernanceOutcome, Tria


def test_store_does_not_imply_read_or_disclose():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_permission("human:a", "agent:b", "claim:1", Capability.STORE)

    assert rel.check_capability("agent:b", "claim:1", Capability.STORE).outcome is GovernanceOutcome.ALLOW
    assert rel.check_capability("agent:b", "claim:1", Capability.READ).outcome is GovernanceOutcome.BLOCK
    assert rel.check_capability("agent:b", "claim:1", Capability.DISCLOSE).outcome is GovernanceOutcome.BLOCK


def test_derivation_requires_explicit_permission():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_permission("human:a", "agent:b", "claim:private", Capability.READ)

    assert rel.check_capability("agent:b", "claim:private", Capability.READ).outcome is GovernanceOutcome.ALLOW
    assert rel.check_capability("agent:b", "claim:private", Capability.DERIVE).outcome is GovernanceOutcome.BLOCK

    rel.grant_permission("human:a", "agent:b", "claim:private", Capability.DERIVE, purpose="reasoning")
    assert rel.check_capability("agent:b", "claim:private", Capability.DERIVE, purpose="reasoning").outcome is GovernanceOutcome.ALLOW


def test_revoked_permission_fails_closed():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_permission("human:a", "agent:b", "resource:x", Capability.ACT)
    rel.revoke_permission("human:a", "agent:b", "resource:x", Capability.ACT)
    assert rel.check_capability("agent:b", "resource:x", Capability.ACT).outcome is GovernanceOutcome.BLOCK


def test_policy_must_be_actively_adopted():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    assert rel.check_policy_adoption("policy.relational-access", "1.0").outcome is GovernanceOutcome.BLOCK

    rel.grant_policy_authority("tria:system", "human:a", "relationship")
    rel.register_policy("human:a", "policy.relational-access", "1.0", "relationship")
    rel.adopt_policy("human:a", "policy.relational-access", "1.0", "relationship")
    assert rel.check_policy_adoption("policy.relational-access", "1.0").outcome is GovernanceOutcome.ALLOW

    rel.revoke_policy("human:a", "policy.relational-access", "1.0")
    assert rel.check_policy_adoption("policy.relational-access", "1.0").outcome is GovernanceOutcome.BLOCK
