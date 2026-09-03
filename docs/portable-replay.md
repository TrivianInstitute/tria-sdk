# Portable replay bundles

TRIA relationships can be exported as self-contained replay bundles for verification outside the Python runtime.

A bundle contains:
- the relationship identifier;
- event and projection schema versions;
- the immutable event stream in portable JSON form;
- the deterministic materialized projection;
- a SHA-256 digest of that projection.

`export_replay_bundle(relationship)` creates the bundle. `verify_replay_bundle(bundle)` rehydrates the events, verifies every event hash and the hash chain, checks relationship identity consistency, deterministically replays the projection, and confirms that both the projection and its digest match.

The bundle is intended as an interoperability and audit artifact, not as a substitute for governed storage. If a relationship contains sensitive claims, exporting the bundle exports those claims too. Applications remain responsible for governing whether a bundle may be disclosed, copied, or retained.

A conforming non-Python implementation does not need TRIA's Python classes. It needs only to preserve the event schema, canonical hash semantics, deterministic reduction rules, projection shape, and bundle verification contract.
