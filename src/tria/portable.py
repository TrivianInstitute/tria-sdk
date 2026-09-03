from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Any

from .compat import (
    CURRENT_BUNDLE_FORMAT_VERSION,
    CURRENT_EVENT_SCHEMA_VERSION,
    CURRENT_PROJECTION_VERSION,
    SchemaCompatibilityError,
    require_supported_compatibility,
)
from .events import RelationalEvent, verify_event_chain
from .state import RelationalState, reduce_events
from .store import EventStore
from .types import Capability, GovernanceOutcome

BUNDLE_FORMAT_VERSION = CURRENT_BUNDLE_FORMAT_VERSION


class ReplayImportError(ValueError):
    pass


class ReplayExportError(PermissionError):
    pass


def replay_export_resource(relationship_id: str) -> str:
    """Return the aggregate resource governed for full replay-bundle disclosure."""
    return f"relationship:{relationship_id}"


def _portable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _portable(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): _portable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_portable(item) for item in value]
    return value


def state_to_dict(state: RelationalState) -> dict[str, Any]:
    """Return a portable projection representation with no tuple-keyed mappings."""
    return {
        "relationship_id": state.relationship_id,
        "projection_version": state.projection_version,
        "participants": list(state.participants),
        "lifecycle": state.lifecycle.value,
        "consent": [_portable(record) for _, record in sorted(state.consent.items(), key=lambda item: str(item[0]))],
        "permissions": [_portable(record) for _, record in sorted(state.permissions.items(), key=lambda item: str(item[0]))],
        "lifecycle_authorities": [_portable(record) for _, record in sorted(state.lifecycle_authorities.items())],
        "policy_authorities": [_portable(record) for _, record in sorted(state.policy_authorities.items(), key=lambda item: str(item[0]))],
        "policy_definitions": [_portable(record) for _, record in sorted(state.policy_definitions.items(), key=lambda item: str(item[0]))],
        "policy_adoptions": [_portable(record) for _, record in sorted(state.policy_adoptions.items(), key=lambda item: str(item[0]))],
        "reconsent_requirements": [_portable(record) for _, record in sorted(state.reconsent_requirements.items(), key=lambda item: str(item[0]))],
        "claims": [_portable(record) for _, record in sorted(state.claims.items())],
        "disagreements": [
            {"claim_id": claim_id, "alternatives": list(alternatives)}
            for claim_id, alternatives in sorted(state.disagreements.items())
        ],
        "last_event_id": state.last_event_id,
    }


def _canonical_json(value: Any) -> str:
    return json.dumps(_portable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def projection_digest(state: RelationalState) -> str:
    return hashlib.sha256(_canonical_json(state_to_dict(state)).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ReplayBundle:
    format_version: str
    relationship_id: str
    event_schema_version: str
    projection_version: str
    events: tuple[dict[str, Any], ...]
    projection: dict[str, Any]
    projection_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": self.format_version,
            "relationship_id": self.relationship_id,
            "event_schema_version": self.event_schema_version,
            "projection_version": self.projection_version,
            "events": list(self.events),
            "projection": self.projection,
            "projection_sha256": self.projection_sha256,
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(_portable(self.to_dict()), sort_keys=True, indent=indent, ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class BundleVerification:
    valid: bool
    chain_valid: bool
    relationship_valid: bool
    projection_valid: bool
    event_count: int
    reason: str = ""


def _build_replay_bundle(relationship) -> ReplayBundle:
    events = tuple(event.to_dict() for event in relationship.events)
    state = relationship.state
    projection = state_to_dict(state)
    return ReplayBundle(
        format_version=BUNDLE_FORMAT_VERSION,
        relationship_id=relationship.relationship_id,
        event_schema_version=CURRENT_EVENT_SCHEMA_VERSION,
        projection_version=CURRENT_PROJECTION_VERSION,
        events=events,
        projection=projection,
        projection_sha256=projection_digest(state),
    )


def export_replay_bundle(
    relationship,
    *,
    actor: str,
    purpose: str | None = None,
    satisfied_conditions: tuple[str, ...] = (),
) -> ReplayBundle:
    """Export full relational history only under active aggregate DISCLOSE authority."""
    resource = replay_export_resource(relationship.relationship_id)
    decision = relationship.check_capability(
        actor,
        resource,
        Capability.DISCLOSE,
        purpose=purpose,
        satisfied_conditions=satisfied_conditions,
    )
    relationship.record_governance_decision(
        decision,
        operation="export_replay_bundle",
        actor=actor,
        relationship_id=relationship.relationship_id,
        resource=resource,
        capability=Capability.DISCLOSE.value,
        purpose=purpose,
        satisfied_conditions=list(satisfied_conditions),
    )
    if decision.outcome is not GovernanceOutcome.ALLOW:
        raise ReplayExportError(
            f"{actor!r} cannot export full replay history without active DISCLOSE authority on {resource!r}."
        )
    return _build_replay_bundle(relationship)


def _invalid(reason: str, *, event_count: int = 0, chain_valid: bool = False, relationship_valid: bool = False) -> BundleVerification:
    return BundleVerification(False, chain_valid, relationship_valid, False, event_count, reason)


def _bundle_mapping(bundle: ReplayBundle | Mapping[str, Any]) -> dict[str, Any] | None:
    if isinstance(bundle, ReplayBundle):
        return bundle.to_dict()
    if isinstance(bundle, Mapping):
        return dict(bundle)
    return None


def _valid_version_header(data: Mapping[str, Any], key: str) -> bool:
    value = data.get(key)
    return isinstance(value, str) and bool(value)


def verify_replay_bundle(bundle: ReplayBundle | dict[str, Any]) -> BundleVerification:
    data = _bundle_mapping(bundle)
    if data is None:
        return _invalid("Replay bundle must be a mapping or ReplayBundle.")

    raw_events = data.get("events")
    if not isinstance(raw_events, Sequence) or isinstance(raw_events, (str, bytes, bytearray)):
        return _invalid("Replay bundle events must be an array.")
    event_count = len(raw_events)
    if event_count == 0:
        return _invalid("Replay bundle must contain at least one relational event.")

    for key in ("event_schema_version", "projection_version", "format_version"):
        if not _valid_version_header(data, key):
            return _invalid(f"Replay bundle {key} must be a non-empty string.", event_count=event_count)

    try:
        require_supported_compatibility(
            data["event_schema_version"],
            projection_version=data["projection_version"],
            bundle_format_version=data["format_version"],
        )
    except SchemaCompatibilityError as exc:
        return _invalid(str(exc), event_count=event_count)

    if not isinstance(data.get("relationship_id"), str) or not data["relationship_id"]:
        return _invalid("Replay bundle relationship_id must be a non-empty string.", event_count=event_count)
    if not isinstance(data.get("projection"), Mapping):
        return _invalid("Replay bundle projection must be an object.", event_count=event_count)
    if not isinstance(data.get("projection_sha256"), str) or not data["projection_sha256"]:
        return _invalid("Replay bundle projection_sha256 must be a non-empty string.", event_count=event_count)

    try:
        events = [RelationalEvent.from_dict(item) for item in raw_events]
    except (KeyError, TypeError, ValueError) as exc:
        return _invalid(f"Invalid event payload: {exc}", event_count=event_count)

    envelope_schema = data["event_schema_version"]
    if any(event.schema_version != envelope_schema for event in events):
        return _invalid("Bundle event schema envelope does not match every contained event.", event_count=len(events))

    relationship_id = data["relationship_id"]
    relationship_valid = all(event.relationship_id == relationship_id for event in events)
    if not relationship_valid:
        return _invalid("Relationship identifiers do not match.", event_count=len(events))

    root = events[0]
    if root.event_type != "RelationshipCreated" or root.actor_id != "tria:system":
        return _invalid(
            "Replay history must begin with a RelationshipCreated event authored by tria:system.",
            event_count=len(events),
            relationship_valid=True,
        )
    if any(event.event_type == "RelationshipCreated" for event in events[1:]):
        return _invalid(
            "Replay history must contain exactly one RelationshipCreated root event.",
            event_count=len(events),
            relationship_valid=True,
        )

    chain_valid = verify_event_chain(events)
    if not chain_valid:
        return _invalid("Event hash chain is invalid.", event_count=len(events), relationship_valid=True)

    state = reduce_events(relationship_id, events)
    expected_projection = state_to_dict(state)
    expected_digest = projection_digest(state)
    projection_valid = (
        dict(data["projection"]) == expected_projection
        and data["projection_sha256"] == expected_digest
        and data["projection_version"] == state.projection_version
    )
    return BundleVerification(
        projection_valid,
        chain_valid,
        True,
        projection_valid,
        len(events),
        "" if projection_valid else "Projection does not match deterministic replay.",
    )


def import_replay_bundle(store: EventStore, bundle: ReplayBundle | dict[str, Any]) -> str:
    """Restore a verified portable history into an empty relationship slot."""
    data = _bundle_mapping(bundle)
    if data is None:
        raise ReplayImportError("Replay bundle must be a mapping or ReplayBundle.")

    verification = verify_replay_bundle(data)
    if not verification.valid:
        raise ReplayImportError(verification.reason or "Replay bundle verification failed.")

    relationship_id = data["relationship_id"]
    if store.list(relationship_id):
        raise ReplayImportError(f"Relationship {relationship_id!r} already has persisted events; import requires an empty destination.")

    try:
        events = [RelationalEvent.from_dict(item) for item in data["events"]]
        store.append_many(events)
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        raise ReplayImportError(f"Replay bundle import failed: {exc}") from exc

    restored = store.list(relationship_id)
    if not verify_event_chain(restored) or len(restored) != len(events):
        raise ReplayImportError("Imported event history failed post-write integrity verification.")
    return relationship_id
