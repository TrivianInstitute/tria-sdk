from dataclasses import replace

import pytest

from tria import EventProposal, RelationalEvent, SchemaCompatibilityError


def test_supported_event_schema_commits_and_hydrates():
    proposal = EventProposal(
        relationship_id="rel:test",
        event_type="RelationshipCreated",
        actor_id="tria:system",
        payload={"participants": ["human:a", "agent:b"]},
        actor_sequence=1,
    )
    event = RelationalEvent.commit(proposal, previous_event_hash=None)
    hydrated = RelationalEvent.from_dict(event.to_dict())
    assert hydrated == event


def test_unsupported_schema_fails_closed_on_commit():
    proposal = EventProposal(
        relationship_id="rel:test",
        event_type="RelationshipCreated",
        actor_id="tria:system",
        payload={"participants": []},
        actor_sequence=1,
        schema_version="9.9",
    )
    with pytest.raises(SchemaCompatibilityError):
        RelationalEvent.commit(proposal, previous_event_hash=None)


def test_unsupported_schema_fails_closed_on_hydration():
    proposal = EventProposal(
        relationship_id="rel:test",
        event_type="RelationshipCreated",
        actor_id="tria:system",
        payload={"participants": []},
        actor_sequence=1,
    )
    event = RelationalEvent.commit(proposal, previous_event_hash=None)
    data = event.to_dict()
    data["schema_version"] = "9.9"
    with pytest.raises(SchemaCompatibilityError):
        RelationalEvent.from_dict(data)
