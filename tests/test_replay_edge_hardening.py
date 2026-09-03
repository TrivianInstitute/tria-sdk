import copy

import pytest

from tria import InMemoryEventStore, ReplayImportError, Tria, export_replay_bundle, import_replay_bundle, verify_replay_bundle


def _bundle_dict():
    return export_replay_bundle(Tria().create_relationship(["human:a", "agent:b"])).to_dict()


def test_malformed_events_container_fails_closed():
    bundle = _bundle_dict()
    bundle["events"] = None

    result = verify_replay_bundle(bundle)

    assert result.valid is False
    assert "events must be an array" in result.reason


def test_non_string_version_header_fails_closed_without_coercion():
    bundle = _bundle_dict()
    bundle["projection_version"] = 0.4

    result = verify_replay_bundle(bundle)

    assert result.valid is False
    assert "projection_version must be a non-empty string" in result.reason


def test_empty_bundle_is_not_a_relationship_history():
    bundle = _bundle_dict()
    bundle["events"] = []

    result = verify_replay_bundle(bundle)

    assert result.valid is False
    assert result.event_count == 0
    assert "at least one relational event" in result.reason


def test_history_must_begin_with_relationship_created_root():
    bundle = _bundle_dict()
    bundle["events"][0]["event_type"] = "ConsentGranted"

    result = verify_replay_bundle(bundle)

    assert result.valid is False
    assert "must begin with a RelationshipCreated" in result.reason


def test_relationship_root_must_be_authored_by_system():
    bundle = _bundle_dict()
    bundle["events"][0]["actor_id"] = "human:a"

    result = verify_replay_bundle(bundle)

    assert result.valid is False
    assert "authored by tria:system" in result.reason


def test_history_cannot_contain_second_relationship_root():
    bundle = _bundle_dict()
    bundle["events"].append(copy.deepcopy(bundle["events"][0]))

    result = verify_replay_bundle(bundle)

    assert result.valid is False
    assert "exactly one RelationshipCreated" in result.reason


def test_invalid_root_import_writes_nothing():
    bundle = _bundle_dict()
    relationship_id = bundle["relationship_id"]
    bundle["events"][0]["event_type"] = "ConsentGranted"
    store = InMemoryEventStore()

    with pytest.raises(ReplayImportError):
        import_replay_bundle(store, bundle)

    assert store.list(relationship_id) == []


def test_non_mapping_bundle_import_fails_closed():
    store = InMemoryEventStore()

    with pytest.raises(ReplayImportError, match="mapping or ReplayBundle"):
        import_replay_bundle(store, None)  # type: ignore[arg-type]
