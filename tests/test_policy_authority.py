import pytest

from tria import GovernanceOutcome, PolicyAuthorityError, Tria


def test_policy_adoption_requires_active_authority_and_registered_policy():
    rel = Tria().create_relationship(["human:owner", "agent:demo"])
    with pytest.raises(PolicyAuthorityError):
        rel.register_policy("human:owner", "memory", "1", "persistent_context")

    rel.grant_policy_authority("human:owner", "human:owner", "persistent_context")
    rel.register_policy("human:owner", "memory", "1", "persistent_context", provenance_refs=("spec:memory-v1",))
    rel.adopt_policy("human:owner", "memory", "1", "persistent_context")
    assert rel.check_policy_adoption("memory", "1").outcome is GovernanceOutcome.ALLOW


def test_consent_impacting_policy_amendment_requires_reconsent():
    rel = Tria().create_relationship(["human:user", "human:owner"])
    rel.grant_policy_authority("human:owner", "human:owner", "persistent_context")
    rel.register_policy("human:owner", "memory", "1", "persistent_context")
    rel.adopt_policy("human:owner", "memory", "1", "persistent_context")
    rel.grant_consent("human:user", "persistent_context")
    assert rel.require_consent("human:user", "persistent_context").outcome is GovernanceOutcome.ALLOW

    rel.amend_policy(
        "human:owner", "memory", "2", "persistent_context",
        supersedes_version="1", consent_impacting=True,
    )
    assert rel.require_consent("human:user", "persistent_context").outcome is GovernanceOutcome.REQUIRE_CONSENT

    rel.grant_consent("human:user", "persistent_context")
    assert rel.require_consent("human:user", "persistent_context").outcome is GovernanceOutcome.ALLOW


def test_revoked_policy_authority_blocks_future_policy_change():
    rel = Tria().create_relationship(["human:owner"])
    rel.grant_policy_authority("human:owner", "human:owner", "scope:x")
    rel.revoke_policy_authority("human:owner", "human:owner", "scope:x")
    with pytest.raises(PolicyAuthorityError):
        rel.register_policy("human:owner", "p", "1", "scope:x")
