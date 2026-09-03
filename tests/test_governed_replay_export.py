import pytest

from tria import (
    Capability,
    ReplayExportError,
    Tria,
    export_replay_bundle,
    replay_export_resource,
    verify_replay_bundle,
)


def _relationship():
    return Tria().create_relationship(["human:a", "agent:b"])


def test_replay_export_requires_discose_on_relationship_aggregate():
    rel = _relationship()

    with pytest.raises(ReplayExportError):
        export_replay_bundle(rel, actor="human:a")

    assert rel.events[-1].event_type == "GovernanceEvaluated"
    assert rel.events[-1].payload["operation"] == "export_replay_bundle"
    assert rel.events[-1].payload["outcome"] == "BLOCK"


def test_read_authority_does_not_substitute_for_disclose():
    rel = _relationship()
    resource = replay_export_resource(rel.relationship_id)
    rel.grant_permission("human:a", "human:a", resource, Capability.READ)

    with pytest.raises(ReplayExportError):
        export_replay_bundle(rel, actor="human:a")


def test_authorized_export_includes_its_governance_decision():
    rel = _relationship()
    resource = replay_export_resource(rel.relationship_id)
    rel.grant_permission("human:a", "human:a", resource, Capability.DISCLOSE)

    bundle = export_replay_bundle(rel, actor="human:a")

    assert bundle.events[-1]["event_type"] == "GovernanceEvaluated"
    assert bundle.events[-1]["payload"]["operation"] == "export_replay_bundle"
    assert bundle.events[-1]["payload"]["outcome"] == "ALLOW"
    assert verify_replay_bundle(bundle).valid is True


def test_purpose_bound_disclose_cannot_be_used_without_matching_purpose():
    rel = _relationship()
    resource = replay_export_resource(rel.relationship_id)
    rel.grant_permission("human:a", "human:a", resource, Capability.DISCLOSE, purpose="archive")

    with pytest.raises(ReplayExportError):
        export_replay_bundle(rel, actor="human:a")

    bundle = export_replay_bundle(rel, actor="human:a", purpose="archive")
    assert verify_replay_bundle(bundle).valid is True


def test_export_conditions_must_be_explicitly_satisfied():
    rel = _relationship()
    resource = replay_export_resource(rel.relationship_id)
    rel.grant_permission(
        "human:a",
        "human:a",
        resource,
        Capability.DISCLOSE,
        conditions=("approved_destination",),
    )

    with pytest.raises(ReplayExportError):
        export_replay_bundle(rel, actor="human:a")

    bundle = export_replay_bundle(
        rel,
        actor="human:a",
        satisfied_conditions=("approved_destination",),
    )
    assert verify_replay_bundle(bundle).valid is True
