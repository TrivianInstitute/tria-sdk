from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from .events import RelationalEvent


class EventStore(Protocol):
    def append(self, event: RelationalEvent) -> None: ...
    def list(self, relationship_id: str) -> list[RelationalEvent]: ...


class InMemoryEventStore:
    def __init__(self) -> None:
        self._events: dict[str, list[RelationalEvent]] = defaultdict(list)

    def append(self, event: RelationalEvent) -> None:
        self._events[event.relationship_id].append(event)

    def list(self, relationship_id: str) -> list[RelationalEvent]:
        return list(self._events.get(relationship_id, ()))
