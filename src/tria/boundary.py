from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .types import Capability, GovernanceOutcome


class CrossBoundaryGovernanceError(PermissionError):
    """Raised when a relationship boundary movement is not explicitly authorized."""


@dataclass(frozen=True, slots=True)
class DisclosureHandle:
    disclosure_id: str
    source_relationship_id: str
    source_event_id: str
    source_event_hash: str
    target_relationship_id: str
    resource: str
    reference: str
    disclosed_by: str

    @property
    def admitted_resource(self) -> str:
        return f"disclosure:{self.disclosure_id}"


def disclose_reference(source, *, actor: str, resource: str, reference: str, target_relationship_id: str) -> DisclosureHandle:
    """Authorize a governed reference to cross out of one Relationship boundary.

    Only the reference crosses Core. Raw content remains in caller-owned storage.
    DISCLOSE authority is required independently of READ or DERIVE authority.
    """
    decision = source.check_capability(actor, resource, Capability.DISCLOSE)
    if decision.outcome is not GovernanceOutcome.ALLOW:
        raise CrossBoundaryGovernanceError(decision.reason)

    disclosure_id = str(uuid4())
    event = source._commit(
        "ReferenceDisclosed",
        actor,
        {
            "disclosure_id": disclosure_id,
            "source_relationship_id": source.relationship_id,
            "target_relationship_id": target_relationship_id,
            "resource": resource,
            "reference": reference,
            "disclosed_by": actor,
        },
    )
    return DisclosureHandle(
        disclosure_id=disclosure_id,
        source_relationship_id=source.relationship_id,
        source_event_id=event.event_id,
        source_event_hash=event.event_hash,
        target_relationship_id=target_relationship_id,
        resource=resource,
        reference=reference,
        disclosed_by=actor,
    )


def _verified_source_event(source, disclosure: DisclosureHandle):
    if source.relationship_id != disclosure.source_relationship_id:
        raise CrossBoundaryGovernanceError("Disclosure source relationship does not match the supplied source.")
    event = next((item for item in source.events if item.event_id == disclosure.source_event_id), None)
    if event is None or event.event_type != "ReferenceDisclosed":
        raise CrossBoundaryGovernanceError("Disclosure source event is missing.")
    if event.event_hash != disclosure.source_event_hash or not event.verify_hash():
        raise CrossBoundaryGovernanceError("Disclosure source event failed integrity verification.")
    expected = {
        "disclosure_id": disclosure.disclosure_id,
        "source_relationship_id": disclosure.source_relationship_id,
        "target_relationship_id": disclosure.target_relationship_id,
        "resource": disclosure.resource,
        "reference": disclosure.reference,
        "disclosed_by": disclosure.disclosed_by,
    }
    if any(event.payload.get(key) != value for key, value in expected.items()):
        raise CrossBoundaryGovernanceError("Disclosure handle does not match its immutable source event.")
    return event


def admit_disclosure(target, source, disclosure: DisclosureHandle, *, actor: str):
    """Explicitly admit a verified disclosure into another Relationship boundary.

    Admission records provenance but grants no READ, DERIVE, ACT, or DELEGATE
    capability. Those authorities remain separate governed decisions.
    """
    source_event = _verified_source_event(source, disclosure)
    if target.relationship_id != disclosure.target_relationship_id:
        raise CrossBoundaryGovernanceError("Disclosure target relationship does not match the receiving relationship.")
    if any(
        event.event_type == "ReferenceAdmitted" and event.payload.get("disclosure_id") == disclosure.disclosure_id
        for event in target.events
    ):
        raise CrossBoundaryGovernanceError("Disclosure has already been admitted into this relationship.")

    return target._commit(
        "ReferenceAdmitted",
        actor,
        {
            "disclosure_id": disclosure.disclosure_id,
            "source_relationship_id": disclosure.source_relationship_id,
            "source_event_id": disclosure.source_event_id,
            "source_event_hash": disclosure.source_event_hash,
            "source_resource": disclosure.resource,
            "reference": disclosure.reference,
            "admitted_resource": disclosure.admitted_resource,
            "admitted_by": actor,
        },
        causal_parents=(),
    )


def derive_from_disclosure(target, *, actor: str, disclosure_id: str, result_ref: str):
    """Record an authorized derivation from an admitted cross-boundary reference.

    DERIVE permission is required on ``disclosure:<id>``. Disclosure and admission
    never imply derivation authority. Core records only an external result reference.
    """
    admission = next(
        (
            event
            for event in reversed(target.events)
            if event.event_type == "ReferenceAdmitted" and event.payload.get("disclosure_id") == disclosure_id
        ),
        None,
    )
    if admission is None:
        raise CrossBoundaryGovernanceError("Disclosure must be admitted before derivation.")

    resource = str(admission.payload["admitted_resource"])
    decision = target.check_capability(actor, resource, Capability.DERIVE)
    if decision.outcome is not GovernanceOutcome.ALLOW:
        raise CrossBoundaryGovernanceError(decision.reason)

    return target._commit(
        "ReferenceDerived",
        actor,
        {
            "disclosure_id": disclosure_id,
            "admitted_resource": resource,
            "source_relationship_id": admission.payload["source_relationship_id"],
            "source_event_id": admission.payload["source_event_id"],
            "result_ref": result_ref,
            "derived_by": actor,
        },
        causal_parents=(admission.event_id,),
    )
