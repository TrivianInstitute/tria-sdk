from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any
from uuid import uuid4


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


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
