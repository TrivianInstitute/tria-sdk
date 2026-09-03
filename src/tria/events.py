from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable
from uuid import uuid4


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


@dataclass(frozen=True, slots=True)
class EventProposal:
    relationship_id: str
    event_type: str
    actor_id: str
    payload: dict[str, Any]
    actor_sequence: int
    causal_parents: tuple[str, ...] = ()
    observed_at: datetime | None = None
    schema_version: str = "0.1"
    policy_version: str = "0.1"


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
    payload: dict[str, Any]
    schema_version: str
    policy_version: str
    previous_event_hash: str | None
    event_hash: str

    @classmethod
    def commit(cls, proposal: EventProposal, previous_event_hash: str | None) -> "RelationalEvent":
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
        material = asdict(self)
        expected = material.pop("event_hash")
        digest = hashlib.sha256(_canonical_json(material).encode("utf-8")).hexdigest()
        return digest == expected

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["causal_parents"] = list(self.causal_parents)
        data["observed_at"] = self.observed_at.isoformat() if self.observed_at else None
        data["committed_at"] = self.committed_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RelationalEvent":
        return cls(
            event_id=data["event_id"],
            relationship_id=data["relationship_id"],
            event_type=data["event_type"],
            actor_id=data["actor_id"],
            actor_sequence=int(data["actor_sequence"]),
            causal_parents=tuple(data.get("causal_parents", ())),
            observed_at=_parse_datetime(data.get("observed_at")),
            committed_at=_parse_datetime(data["committed_at"]),
            payload=dict(data.get("payload", {})),
            schema_version=data.get("schema_version", "0.1"),
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
