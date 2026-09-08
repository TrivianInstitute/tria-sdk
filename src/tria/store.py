from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import threading
from typing import Iterable, Protocol

from .events import RelationalEvent, verify_event_chain
from .errors import ConcurrentWriteError, PersistenceError, UnsupportedStoreError


class EventStore(Protocol):
    """Advanced stores must implement all operations and the shared write/execution guard."""
    def append(self, event: RelationalEvent) -> None: ...
    def append_many(self, events: Iterable[RelationalEvent]) -> None: ...
    def list(self, relationship_id: str) -> list[RelationalEvent]: ...
    def execution_guard(self): ...


def _validate_append(prior, events):
    history = list(prior)
    if not verify_event_chain(history):
        raise PersistenceError('Stored chain is invalid; inspect audit and recover from verified history.')
    ids = {e.event_id for e in history}
    for event in events:
        expected = history[-1].event_hash if history else None
        sequence = 1 + max((e.actor_sequence for e in history if e.actor_id == event.actor_id), default=0)
        if event.event_id in ids or event.previous_event_hash != expected or event.actor_sequence != sequence:
            raise ConcurrentWriteError('Stale predecessor, actor sequence, or duplicate event; reload and reconsider the operation before retrying.')
        if not event.verify_hash():
            raise PersistenceError('Refusing an event with an invalid hash.')
        history.append(event)
        ids.add(event.event_id)


class InMemoryEventStore:
    def __init__(self) -> None:
        self._events = defaultdict(list)
        self._lock = threading.RLock()

    def execution_guard(self):
        return self._lock

    def append(self, event):
        self.append_many([event])

    def append_many(self, events):
        events = list(events)
        with self._lock:
            grouped = defaultdict(list)
            for e in events:
                grouped[e.relationship_id].append(e)
            for rid, pending in grouped.items():
                _validate_append(self._events[rid], pending)
            for rid, pending in grouped.items():
                self._events[rid].extend(pending)

    def list(self, relationship_id):
        with self._lock:
            return list(self._events.get(relationship_id, ()))


_registry_lock = threading.RLock()
_sessions = {}


class _Session:
    def __init__(self, path):
        self.lock = threading.RLock()
        self.pid = os.getpid()
        self.refs = 0
        self.owner = None
        try:
            if path != ':memory:':
                try:
                    import fcntl
                except ImportError as exc:
                    raise UnsupportedStoreError('File SQLite currently requires POSIX process locks; use InMemoryEventStore on this platform.') from exc
                self.owner = open(path + '.tria-lock', 'a+b')
                try:
                    fcntl.flock(self.owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise PersistenceError('Database is owned by another process; close its SDK stores before reopening.') from exc
            self.conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
            self.conn.execute('CREATE TABLE IF NOT EXISTS events (commit_index INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE, relationship_id TEXT NOT NULL, event_json TEXT NOT NULL)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_events_relationship ON events(relationship_id, commit_index)')
        except Exception:
            if self.owner is not None:
                self.owner.close()
            raise


class SQLiteEventStore:
    """Atomic compare-and-append; one live process per file, multiple local instances.

    Close every instance to release ownership. ':memory:' persists for this store's
    lifetime. Direct SQL writers do not participate in SDK synchronization.
    """
    def __init__(self, path: str | Path):
        if not isinstance(path, (str, Path)) or not str(path).strip():
            raise PersistenceError('SQLite path must be a file path or :memory:.')
        self.path = ':memory:' if str(path) == ':memory:' else str(Path(path).resolve())
        self._closed = False
        self._key = self.path if self.path != ':memory:' else object()
        try:
            with _registry_lock:
                session = _sessions.get(self._key)
                if session is not None and session.pid != os.getpid():
                    raise PersistenceError('Inherited SQLite stores cannot be used after fork; close stores before starting another process.')
                if session is None:
                    session = _Session(self.path)
                    _sessions[self._key] = session
                session.refs += 1
                self._session = session
        except (OSError, sqlite3.Error) as exc:
            raise PersistenceError('Cannot open SQLite store; use an existing writable parent directory and a valid file path.') from exc

    def _check(self):
        if self._closed or self._session.pid != os.getpid():
            raise PersistenceError('Store is closed or inherited across processes; create a supported store instance.')

    @contextmanager
    def execution_guard(self):
        self._check()
        with self._session.lock:
            self._check()
            yield

    def _list(self, rid):
        rows = self._session.conn.execute('SELECT event_json FROM events WHERE relationship_id=? ORDER BY commit_index', (rid,)).fetchall()
        return [RelationalEvent.from_dict(json.loads(row[0])) for row in rows]

    def list(self, relationship_id):
        with self.execution_guard():
            return self._list(relationship_id)

    def append(self, event):
        self.append_many([event])

    def append_many(self, events):
        events = list(events)
        with self.execution_guard():
            conn = self._session.conn
            conn.execute('BEGIN IMMEDIATE')
            try:
                grouped = defaultdict(list)
                for e in events:
                    grouped[e.relationship_id].append(e)
                for rid, pending in grouped.items():
                    _validate_append(self._list(rid), pending)
                conn.executemany('INSERT INTO events(event_id,relationship_id,event_json) VALUES (?,?,?)',
                    [(e.event_id,e.relationship_id,json.dumps(e.to_dict(),sort_keys=True,separators=(',',':'))) for e in events])
                conn.execute('COMMIT')
            except Exception:
                conn.execute('ROLLBACK')
                raise

    def close(self):
        with _registry_lock:
            if self._closed:
                return
            self._check()
            with self._session.lock:
                self._closed = True
                self._session.refs -= 1
                if not self._session.refs:
                    self._session.conn.close()
                    if self._session.owner is not None:
                        self._session.owner.close()
                    _sessions.pop(self._key, None)

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, *args):
        self.close()
