from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Any

from .compat import CURRENT_EVENT_SCHEMA_VERSION, CURRENT_PROJECTION_VERSION
from .events import RelationalEvent, verify_event_chain
from .state import RelationalState, reduce_events

BUNDLE_FORMAT_VERSION = "0.1"


def _portable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _portable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
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


def export_replay_bundle(relationship) -> ReplayBundle:
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


def verify_replay_bundle(bundle: ReplayBundle | dict[str, Any]) -> BundleVerification:
    data = bundle.to_dict() if isinstance(bundle, ReplayBundle) else dict(bundle)
    try:
        events = [RelationalEvent.from_dict(item) for item in data.get("events", [])]
    except (KeyError, TypeError, ValueError) as exc:
        return BundleVerification(False, False, False, False, 0, f"Invalid event payload: {exc}")

    relationship_id = data.get("relationship_id")
    relationship_valid = bool(relationship_id) and all(event.relationship_id == relationship_id for event in events)
    chain_valid = verify_event_chain(events)
    if not relationship_valid or not chain_valid:
        reason = "Relationship identifiers do not match." if not relationship_valid else "Event hash chain is invalid."
        return BundleVerification(False, chain_valid, relationship_valid, False, len(events), reason)

    state = reduce_events(relationship_id, events)
    expected_projection = state_to_dict(state)
    expected_digest = projection_digest(state)
    projection_valid = (
        data.get("projection") == expected_projection
        and data.get("projection_sha256") == expected_digest
        and data.get("projection_version") == state.projection_version
    )
    return BundleVerification(
        projection_valid,
        chain_valid,
        relationship_valid,
        projection_valid,
        len(events),
        "" if projection_valid else "Projection does not match deterministic replay.",
    )
