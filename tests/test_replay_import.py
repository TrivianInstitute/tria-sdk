import copy

import pytest

from tria import Capability, EpistemicType, InMemoryEventStore, ReplayImportError, SQLiteEventStore, Tria, export_replay_bundle, replay_export_resource


def _source_bundle():
    source = Tria()
    rel = source.create_relationship(["human:a", "agent:b"])
    rel.grant_consent("human:a", "persistent_context")
    rel.register_claim(
        "human:a",
        EpistemicType.OBSERVATION,
        "Portable history survives implementation boundaries.",
        source_refs=["test:portable"],
    )
    rel.grant_permission("human:a", "human:a", replay_export_resource(rel.relationship_id), Capability.DISCLOSE)
    return rel, export_replay_bundle(rel, actor="human:a")


def test_restore_relationship_preserves_event_identity_and_projection():
    source_rel, bundle = _source_bundle()
    target = Tria(InMemoryEventStore())

    restored = target.restore_relationship(bundle)

    assert restored.relationship_id == source_rel.relationship_id
    assert [event.event_id for event in restored.events] == [event.event_id for event in source_rel.events]
    assert [event.event_hash for event in restored.events] == [event.event_hash for event in source_rel.events]
    assert restored.state == source_rel.state
    assert restored.audit()["chain_valid"] is True


def test_restore_rejects_tampered_bundle_without_writing_events():
    _, bundle = _source_bundle()
    data = copy.deepcopy(bundle.to_dict())
    data["events"][1]["payload"]["scope"] = "tampered"
    store = InMemoryEventStore()

    with pytest.raises(ReplayImportError):
        Tria(store).restore_relationship(data)

    assert store.list(bundle.relationship_id) == []


def test_restore_rejects_nonempty_destination():
    _, bundle = _source_bundle()
    store = InMemoryEventStore()
    tria = Tria(store)
    tria.restore_relationship(bundle)

    with pytest.raises(ReplayImportError, match="empty destination"):
        tria.restore_relationship(bundle)


def test_sqlite_restore_is_complete_and_replayable(tmp_path):
    source_rel, bundle = _source_bundle()
    store = SQLiteEventStore(tmp_path / "restored.sqlite")

    restored = Tria(store).restore_relationship(bundle)
    reloaded = Tria(SQLiteEventStore(tmp_path / "restored.sqlite")).load_relationship(source_rel.relationship_id)

    assert [event.event_hash for event in restored.events] == [event.event_hash for event in source_rel.events]
    assert reloaded.state == source_rel.state
    assert reloaded.audit()["chain_valid"] is True
