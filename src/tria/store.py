from __future__ import annotations

from collections import defaultdict
import json
import sqlite3
from pathlib import Path
from typing import Iterable, Protocol

from .events import RelationalEvent


class EventStore(Protocol):
    def append(self, event: RelationalEvent) -> None: ...
    def append_many(self, events: Iterable[RelationalEvent]) -> None: ...
    def list(self, relationship_id: str) -> list[RelationalEvent]: ...


class InMemoryEventStore:
    def __init__(self) -> None:
        self._events: dict[str, list[RelationalEvent]] = defaultdict(list)

    def append(self, event: RelationalEvent) -> None:
        self._events[event.relationship_id].append(event)

    def append_many(self, events: Iterable[RelationalEvent]) -> None:
        events = list(events)
        for event in events:
            self._events[event.relationship_id].append(event)

    def list(self, relationship_id: str) -> list[RelationalEvent]:
        return list(self._events.get(relationship_id, ()))


class SQLiteEventStore:
    """Minimal local-first append-only event store.

    SQLite commit order is used for deterministic replay only. It does not claim
    objective causal order; actor_sequence and causal_parents remain part of each event.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    commit_index INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    relationship_id TEXT NOT NULL,
                    event_json TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_relationship ON events(relationship_id, commit_index)")

    @staticmethod
    def _row(event: RelationalEvent) -> tuple[str, str, str]:
        payload = json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":"))
        return event.event_id, event.relationship_id, payload

    def append(self, event: RelationalEvent) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO events(event_id, relationship_id, event_json) VALUES (?, ?, ?)",
                self._row(event),
            )

    def append_many(self, events: Iterable[RelationalEvent]) -> None:
        rows = [self._row(event) for event in events]
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO events(event_id, relationship_id, event_json) VALUES (?, ?, ?)",
                rows,
            )

    def list(self, relationship_id: str) -> list[RelationalEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT event_json FROM events WHERE relationship_id = ? ORDER BY commit_index ASC",
                (relationship_id,),
            ).fetchall()
        return [RelationalEvent.from_dict(json.loads(row[0])) for row in rows]
