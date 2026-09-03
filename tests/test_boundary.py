import pytest

from tria import (
    Capability,
    CrossBoundaryGovernanceError,
    Tria,
    admit_disclosure,
    derive_from_disclosure,
    disclose_reference,
)


def _relationships():
    tria = Tria()
    source = tria.create_relationship(["human:a", "agent:source"])
    target = tria.create_relationship(["human:a", "agent:target"])
    return source, target


def _disclosure(source, target):
    source.grant_permission("human:a", "agent:source", "claim:profile", Capability.DISCLOSE)
    return disclose_reference(
        source,
        actor="agent:source",
        resource="claim:profile",
        reference="vault:claim:42",
        target_relationship_id=target.relationship_id,
    )


def test_read_permission_does_not_authorize_disclosure():
    source, target = _relationships()
    source.grant_permission("human:a", "agent:source", "claim:profile", Capability.READ)

    with pytest.raises(CrossBoundaryGovernanceError):
        disclose_reference(
            source,
            actor="agent:source",
            resource="claim:profile",
            reference="vault:claim:42",
            target_relationship_id=target.relationship_id,
        )


def test_destination_store_authority_is_required_for_admission():
    source, target = _relationships()
    disclosure = _disclosure(source, target)

    with pytest.raises(CrossBoundaryGovernanceError):
        admit_disclosure(target, source, disclosure, actor="human:a")


def test_disclosure_requires_explicit_admission_and_preserves_source_provenance():
    source, target = _relationships()
    disclosure = _disclosure(source, target)
    target.grant_permission("human:a", "human:a", disclosure.admitted_resource, Capability.STORE)

    admission = admit_disclosure(target, source, disclosure, actor="human:a")

    assert admission.event_type == "ReferenceAdmitted"
    assert admission.payload["source_relationship_id"] == source.relationship_id
    assert admission.payload["source_event_id"] == disclosure.source_event_id
    assert admission.payload["source_event_hash"] == disclosure.source_event_hash
    assert admission.payload["reference"] == "vault:claim:42"


def test_disclosure_does_not_grant_derivation_authority():
    source, target = _relationships()
    disclosure = _disclosure(source, target)
    target.grant_permission("human:a", "human:a", disclosure.admitted_resource, Capability.STORE)
    admit_disclosure(target, source, disclosure, actor="human:a")

    with pytest.raises(CrossBoundaryGovernanceError):
        derive_from_disclosure(
            target,
            actor="agent:target",
            disclosure_id=disclosure.disclosure_id,
            result_ref="vault:derived:1",
        )

    target.grant_permission(
        "human:a",
        "agent:target",
        disclosure.admitted_resource,
        Capability.DERIVE,
    )
    event = derive_from_disclosure(
        target,
        actor="agent:target",
        disclosure_id=disclosure.disclosure_id,
        result_ref="vault:derived:1",
    )

    assert event.event_type == "ReferenceDerived"
    assert event.payload["result_ref"] == "vault:derived:1"
    assert event.causal_parents == (next(
        item.event_id for item in target.events if item.event_type == "ReferenceAdmitted"
    ),)


def test_disclosure_cannot_be_admitted_into_wrong_relationship():
    source, target = _relationships()
    third = Tria(source._store).create_relationship(["human:a", "agent:third"])
    disclosure = _disclosure(source, target)
    third.grant_permission("human:a", "human:a", disclosure.admitted_resource, Capability.STORE)

    with pytest.raises(CrossBoundaryGovernanceError):
        admit_disclosure(third, source, disclosure, actor="human:a")


def test_tampered_disclosure_handle_fails_closed():
    source, target = _relationships()
    disclosure = _disclosure(source, target)
    target.grant_permission("human:a", "human:a", disclosure.admitted_resource, Capability.STORE)
    tampered = disclosure.__class__(
        disclosure_id=disclosure.disclosure_id,
        source_relationship_id=disclosure.source_relationship_id,
        source_event_id=disclosure.source_event_id,
        source_event_hash=disclosure.source_event_hash,
        target_relationship_id=disclosure.target_relationship_id,
        resource=disclosure.resource,
        reference="vault:claim:tampered",
        disclosed_by=disclosure.disclosed_by,
    )

    with pytest.raises(CrossBoundaryGovernanceError):
        admit_disclosure(target, source, tampered, actor="human:a")
