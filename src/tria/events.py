from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable
from uuid import uuid4

from .compat import CURRENT_EVENT_SCHEMA_VERSION, require_supported_event_schema
from .immutability import deep_freeze, deep_thaw


def _canonical_json(data: Mapping[str, Any]) -> str:
    return json.dumps(deep_thaw(data), sort_keys=True, separators=(",", ":"), default=str)


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


@dataclass(frozen=True, slots=True)
class EventProposal:
    relationship_id: str
    event_type: str
    actor_id: str
    payload: Mapping[str, Any]
    actor_sequence: int
    causal_parents: tuple[str, ...] = ()
    observed_at: datetime | None = None
    schema_version: str = CURRENT_EVENT_SCHEMA_VERSION
    policy_version: str = "0.1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", deep_freeze(self.payload))
        object.__setattr__(self, "causal_parents", tuple(self.causal_parents))


@dataclass(frozen=True, slots=True)
class RelationalEvent:
    event_id: str
    relationship_id: str
    event_type: str
    actor_id: str
    actor_sequence: int
    causal_parents: tuple[str, ...]
    observed_at: datetime | None
    committed_at: datetime
    payload: Mapping[str, Any]
    schema_version: str
    policy_version: str
    previous_event_hash: str | None
    event_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", deep_freeze(self.payload))
        object.__setattr__(self, "causal_parents", tuple(self.causal_parents))

    def _hash_material(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "relationship_id": self.relationship_id,
            "event_type": self.event_type,
            "actor_id": self.actor_id,
            "actor_sequence": self.actor_sequence,
            "causal_parents": self.causal_parents,
            "observed_at": self.observed_at,
            "committed_at": self.committed_at,
            "payload": self.payload,
            "schema_version": self.schema_version,
            "policy_version": self.policy_version,
            "previous_event_hash": self.previous_event_hash,
        }

    @classmethod
    def commit(cls, proposal: EventProposal, previous_event_hash: str | None) -> "RelationalEvent":
        require_supported_event_schema(proposal.schema_version)
        event_id = str(uuid4())
        committed_at = datetime.now(timezone.utc)
        material = {
            "event_id": event_id,
            "relationship_id": proposal.relationship_id,
            "event_type": proposal.event_type,
            "actor_id": proposal.actor_id,
            "actor_sequence": proposal.actor_sequence,
            "causal_parents": proposal.causal_parents,
            "observed_at": proposal.observed_at,
            "committed_at": committed_at,
            "payload": proposal.payload,
            "schema_version": proposal.schema_version,
            "policy_version": proposal.policy_version,
            "previous_event_hash": previous_event_hash,
        }
        digest = hashlib.sha256(_canonical_json(material).encode("utf-8")).hexdigest()
        return cls(event_hash=digest, **material)

    def verify_hash(self) -> bool:
        digest = hashlib.sha256(_canonical_json(self._hash_material()).encode("utf-8")).hexdigest()
        return digest == self.event_hash

    def to_dict(self) -> dict[str, Any]:
        data = deep_thaw(self._hash_material())
        data["observed_at"] = self.observed_at.isoformat() if self.observed_at else None
        data["committed_at"] = self.committed_at.isoformat()
        data["event_hash"] = self.event_hash
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RelationalEvent":
        schema_version = data.get("schema_version", CURRENT_EVENT_SCHEMA_VERSION)
        require_supported_event_schema(schema_version)
        return cls(
            event_id=data["event_id"],
            relationship_id=data["relationship_id"],
            event_type=data["event_type"],
            actor_id=data["actor_id"],
            actor_sequence=int(data["actor_sequence"]),
            causal_parents=tuple(data.get("causal_parents", ())),
            observed_at=_parse_datetime(data.get("observed_at")),
            committed_at=_parse_datetime(data["committed_at"]),
            payload=data.get("payload", {}),
            schema_version=schema_version,
            policy_version=data.get("policy_version", "0.1"),
            previous_event_hash=data.get("previous_event_hash"),
            event_hash=data["event_hash"],
        )


def verify_event_chain(events: Iterable[RelationalEvent]) -> bool:
    previous_hash: str | None = None
    for event in events:
        if not event.verify_hash():
            return False
        if event.previous_event_hash != previous_hash:
            return False
        previous_hash = event.event_hash
    return True
