from datetime import datetime, timedelta, timezone

import pytest

from tria import (
    Capability,
    CapabilityRequirement,
    ConsentRequirement,
    GovernanceOutcome,
    InvocationRequest,
    Runtime,
    Tria,
)


def _past():
    return datetime.now(timezone.utc) - timedelta(days=1)


def _future():
    return datetime.now(timezone.utc) + timedelta(days=1)


def test_expired_consent_requires_renewed_consent():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_consent("human:a", "profile", expires_at=_past())

    decision = rel.require_consent("human:a", "profile")

    assert decision.outcome is GovernanceOutcome.REQUIRE_CONSENT
    assert decision.policy_id == "core.consent.expiry"


def test_consent_conditions_must_be_explicitly_satisfied():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_consent(
        "human:a",
        "profile",
        purpose="support",
        expires_at=_future(),
        conditions=("human_present", "private_session"),
    )

    missing = rel.require_consent(
        "human:a",
        "profile",
        purpose="support",
        satisfied_conditions=("human_present",),
    )
    allowed = rel.require_consent(
        "human:a",
        "profile",
        purpose="support",
        satisfied_conditions=("private_session", "human_present", "extra_context"),
    )

    assert missing.outcome is GovernanceOutcome.REQUIRE_CONSENT
    assert missing.policy_id == "core.consent.conditions"
    assert allowed.outcome is GovernanceOutcome.ALLOW


def test_expired_permission_blocks_even_when_purpose_matches():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_permission(
        "human:a",
        "agent:b",
        "claim:private",
        Capability.DERIVE,
        purpose="reasoning",
        expires_at=_past(),
    )

    decision = rel.check_capability(
        "agent:b",
        "claim:private",
        Capability.DERIVE,
        purpose="reasoning",
    )

    assert decision.outcome is GovernanceOutcome.BLOCK
    assert decision.policy_id == "core.permission.expiry"


def test_permission_conditions_are_opaque_and_fail_closed():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_permission(
        "human:a",
        "agent:b",
        "context:profile",
        Capability.READ,
        conditions=("private_session",),
    )

    assert rel.check_capability("agent:b", "context:profile", Capability.READ).outcome is GovernanceOutcome.BLOCK
    assert rel.check_capability(
        "agent:b",
        "context:profile",
        Capability.READ,
        satisfied_conditions=("private_session",),
    ).outcome is GovernanceOutcome.ALLOW


def test_runtime_enforces_time_purpose_and_conditions_together():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_consent(
        "human:a",
        "persistent_context",
        purpose="support",
        expires_at=_future(),
        conditions=("human_present",),
    )
    rel.grant_permission(
        "human:a",
        "agent:b",
        "context:profile",
        Capability.READ,
        purpose="support",
        expires_at=_future(),
        conditions=("human_present",),
    )

    blocked = Runtime().prepare(
        rel,
        InvocationRequest(
            requested_by="agent:b",
            action="help",
            target="model",
            requirements=(CapabilityRequirement("context:profile", Capability.READ, purpose="support"),),
            consent_requirements=(ConsentRequirement("human:a", "persistent_context", purpose="support"),),
        ),
    )
    allowed = Runtime().prepare(
        rel,
        InvocationRequest(
            requested_by="agent:b",
            action="help",
            target="model",
            requirements=(CapabilityRequirement("context:profile", Capability.READ, purpose="support", satisfied_conditions=("human_present",)),),
            consent_requirements=(ConsentRequirement("human:a", "persistent_context", purpose="support", satisfied_conditions=("human_present",)),),
        ),
    )

    assert blocked.allowed is False
    assert allowed.allowed is True


def test_expiry_must_be_timezone_aware():
    rel = Tria().create_relationship(["human:a", "agent:b"])

    with pytest.raises(ValueError, match="timezone-aware"):
        rel.grant_consent("human:a", "profile", expires_at=datetime.now())

    with pytest.raises(ValueError, match="timezone-aware"):
        rel.grant_permission("human:a", "agent:b", "context:profile", Capability.READ, expires_at=datetime.now())
