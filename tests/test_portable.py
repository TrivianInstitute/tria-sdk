import json

from tria import (
    Capability,
    EpistemicType,
    Tria,
    export_replay_bundle,
    verify_replay_bundle,
)


def _relationship():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    claim = rel.register_claim(
        "human:a",
        EpistemicType.OBSERVATION,
        "Portable replay test.",
        source_refs=["test:source"],
    )
    rel.grant_permission("human:a", "agent:b", f"claim:{claim.claim_id}", Capability.READ)
    return rel


def test_exported_bundle_verifies_after_json_round_trip():
    bundle = export_replay_bundle(_relationship())
    decoded = json.loads(bundle.to_json())

    result = verify_replay_bundle(decoded)

    assert result.valid is True
    assert result.chain_valid is True
    assert result.relationship_valid is True
    assert result.projection_valid is True
    assert result.event_count == len(bundle.events)


def test_tampered_event_fails_bundle_verification():
    bundle = export_replay_bundle(_relationship()).to_dict()
    bundle["events"][0]["payload"]["participants"] = ["attacker"]

    result = verify_replay_bundle(bundle)

    assert result.valid is False
    assert result.chain_valid is False


def test_tampered_projection_fails_even_when_event_chain_is_valid():
    bundle = export_replay_bundle(_relationship()).to_dict()
    bundle["projection"]["participants"] = ["someone-else"]

    result = verify_replay_bundle(bundle)

    assert result.valid is False
    assert result.chain_valid is True
    assert result.projection_valid is False
