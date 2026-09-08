# Persistence and write safety

Use `with SQLiteEventStore('relationship.sqlite') as store:` and `Tria(store)`.
Save `relationship.relationship_id` in your host's application record. Reopen with
`Tria(store).load_relationship(id)`; missing IDs raise RelationshipNotFoundError.
The [complete application](../examples/governed_assistant.py) includes close/reopen.

`:memory:` is supported for one SQLiteEventStore object's lifetime; separate memory
stores are separate databases. `InMemoryEventStore()` is the lighter alternative.
File parents must already exist and be writable. Closed stores raise PersistenceError.

## Supported concurrency

One owning process per canonical database path is enforced using a POSIX advisory
lock held for the lifetime of all open SDK instances. Multiple instances/threads
inside that process share a write/execution lock and connection. Close every store
or use context managers to release ownership. A second process fails clearly;
passing stores across fork is unsupported and rejected. POSIX file locks are
required for file-backed SQLite in this prerelease. Network filesystems, hard-link
aliases and external SQL writers are unsupported; use one canonical local path.

Append runs in a SQLite transaction and checks predecessor, actor sequence, event
identity and hashes before committing. A stale writer raises ConcurrentWriteError;
its event is not appended. Batch append is all-or-nothing, including interruptions.
Reload and reassess whether an operation is still appropriate before constructing
a new proposal. Never blindly retry an old event or a consequence-bearing executor.

File-backed reopen and replay restore are tested, not power-loss recovery, network
filesystem locking or remote database operation. See [compatibility](compatibility.md)
before opening an older alpha database. Do not point a new prerelease at the only
copy of historical data. Direct file modifications are not protected by SDK locks.
