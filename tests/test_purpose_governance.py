from tria import (
    Capability,
    CapabilityRequirement,
    ConsentRequirement,
    GovernanceOutcome,
    InvocationRequest,
    Runtime,
    Tria,
)


def test_purpose_bound_permission_requires_exact_purpose():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_permission("human:a", "agent:b", "profile:x", Capability.READ, purpose="support")

    assert rel.check_capability("agent:b", "profile:x", Capability.READ, purpose="support").outcome is GovernanceOutcome.ALLOW
    assert rel.check_capability("agent:b", "profile:x", Capability.READ, purpose="marketing").outcome is GovernanceOutcome.BLOCK
    assert rel.check_capability("agent:b", "profile:x", Capability.READ).outcome is GovernanceOutcome.BLOCK


def test_unbound_permission_remains_general():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_permission("human:a", "agent:b", "profile:x", Capability.READ)

    assert rel.check_capability("agent:b", "profile:x", Capability.READ, purpose="support").outcome is GovernanceOutcome.ALLOW
    assert rel.check_capability("agent:b", "profile:x", Capability.READ).outcome is GovernanceOutcome.ALLOW


def test_purpose_bound_consent_requires_exact_purpose():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_consent("human:a", "persistent_context", purpose="support")

    assert rel.require_consent("human:a", "persistent_context", purpose="support").outcome is GovernanceOutcome.ALLOW
    assert rel.require_consent("human:a", "persistent_context", purpose="research").outcome is GovernanceOutcome.REQUIRE_CONSENT
    assert rel.require_consent("human:a", "persistent_context").outcome is GovernanceOutcome.REQUIRE_CONSENT


def test_runtime_enforces_declared_purpose_for_consent_and_capability():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_consent("human:a", "persistent_context", purpose="support")
    rel.grant_permission("human:a", "agent:b", "profile:x", Capability.READ, purpose="support")

    allowed = Runtime().prepare(
        rel,
        InvocationRequest(
            requested_by="agent:b",
            action="Use the profile for support.",
            target="executor:any",
            requirements=(CapabilityRequirement("profile:x", Capability.READ, purpose="support"),),
            consent_requirements=(ConsentRequirement("human:a", "persistent_context", purpose="support"),),
        ),
    )
    assert allowed.allowed is True

    blocked = Runtime().prepare(
        rel,
        InvocationRequest(
            requested_by="agent:b",
            action="Use the profile for marketing.",
            target="executor:any",
            requirements=(CapabilityRequirement("profile:x", Capability.READ, purpose="marketing"),),
            consent_requirements=(ConsentRequirement("human:a", "persistent_context", purpose="marketing"),),
        ),
    )
    assert blocked.allowed is False
    assert blocked.outcome is GovernanceOutcome.REQUIRE_CONSENT


def test_invocation_event_preserves_declared_purpose_without_inference():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    request = InvocationRequest(
        requested_by="agent:b",
        action="Do something whose text should not define its purpose.",
        target="executor:any",
        requirements=(CapabilityRequirement("profile:x", Capability.READ, purpose="support"),),
        consent_requirements=(ConsentRequirement("human:a", "persistent_context", purpose="support"),),
    )
    rel.record_invocation_proposed(request)

    event = rel.events[-1]
    assert event.payload["requirements"][0]["purpose"] == "support"
    assert event.payload["consent_requirements"][0]["purpose"] == "support"
