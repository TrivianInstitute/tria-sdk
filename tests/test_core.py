from tria import EpistemicAdmissionError, EpistemicType, GovernanceOutcome, InMemoryEventStore, Tria


def test_state_is_reconstructed_from_events():
    store = InMemoryEventStore()
    tria = Tria(store)
    rel = tria.create_relationship(["human:a", "agent:b"])
    rel.grant_consent("human:a", "persistent_context")
    rid = rel.relationship_id
    reloaded = Tria(store).load_relationship(rid)
    assert reloaded.state.participants == ("human:a", "agent:b")
    assert reloaded.state.consent[("human:a", "persistent_context")].active is True
    assert reloaded.audit()["reconstructable"] is True


def test_meaning_never_overwrites_occurrence():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    obs = rel.register_claim("agent:b", EpistemicType.OBSERVATION, "Latency increased.", source_refs=["sensor:latency"])
    interp = rel.register_claim("agent:b", EpistemicType.INTERPRETATION, "Human may be disengaged.", derived_from=[obs.claim_id])
    rel.dispute_claim("human:a", interp.claim_id, "I was concentrating.")
    state = rel.state
    assert state.claims[obs.claim_id].content == "Latency increased."
    assert state.claims[interp.claim_id].status.value == "CONTESTED"
    assert state.disagreements[interp.claim_id] == ("I was concentrating.",)


def test_observation_requires_source_provenance():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    try:
        rel.register_claim("agent:b", EpistemicType.OBSERVATION, "Human was uncomfortable.")
    except EpistemicAdmissionError:
        pass
    else:
        raise AssertionError("Observation without source provenance should be rejected")


def test_consent_revocation_changes_governance():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    assert rel.require_consent("human:a", "memory").outcome is GovernanceOutcome.REQUIRE_CONSENT
    rel.grant_consent("human:a", "memory")
    assert rel.require_consent("human:a", "memory").outcome is GovernanceOutcome.ALLOW
    rel.revoke_consent("human:a", "memory")
    assert rel.require_consent("human:a", "memory").outcome is GovernanceOutcome.REQUIRE_CONSENT


def test_event_hashes_are_tamper_evident():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.grant_consent("human:a", "memory")
    assert rel.audit()["hashes_valid"] is True
