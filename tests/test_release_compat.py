from copy import deepcopy

from tria import (
    CURRENT_BUNDLE_FORMAT_VERSION,
    CURRENT_EVENT_SCHEMA_VERSION,
    CURRENT_PROJECTION_VERSION,
    EpistemicType,
    Tria,
    check_compatibility,
    export_replay_bundle,
    verify_replay_bundle,
)


def _bundle_dict():
    rel = Tria().create_relationship(["human:a", "agent:b"])
    rel.register_claim("human:a", EpistemicType.OBSERVATION, "Observed fact", source_refs=["source:1"])
    return export_replay_bundle(rel).to_dict()


def test_current_compatibility_surface_is_supported():
    report = check_compatibility(
        CURRENT_EVENT_SCHEMA_VERSION,
        projection_version=CURRENT_PROJECTION_VERSION,
        bundle_format_version=CURRENT_BUNDLE_FORMAT_VERSION,
    )
    assert report.supported is True


def test_unknown_bundle_format_fails_closed_before_replay():
    bundle = _bundle_dict()
    bundle["format_version"] = "9.9"
    result = verify_replay_bundle(bundle)
    assert result.valid is False
    assert "bundle format" in result.reason


def test_unknown_projection_version_fails_closed_before_replay():
    bundle = _bundle_dict()
    bundle["projection_version"] = "9.9"
    result = verify_replay_bundle(bundle)
    assert result.valid is False
    assert "projection" in result.reason


def test_event_schema_envelope_must_match_contained_events():
    bundle = _bundle_dict()
    tampered = deepcopy(bundle)
    tampered["event_schema_version"] = "0.1"
    tampered["events"][0]["schema_version"] = "9.9"
    result = verify_replay_bundle(tampered)
    assert result.valid is False


def test_missing_version_envelope_fails_closed():
    bundle = _bundle_dict()
    bundle.pop("format_version")
    result = verify_replay_bundle(bundle)
    assert result.valid is False
