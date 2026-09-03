# Replay edge hardening

Portable replay verification is not only hash-chain verification. A bundle must also represent a structurally valid TRIA relationship history.

## Fail-closed structure

Verification rejects bundles when:

- `events` is missing, null, scalar, text, or empty;
- version headers are not non-empty strings;
- `relationship_id`, `projection`, or `projection_sha256` has the wrong shape;
- contained event schema versions disagree with the bundle envelope;
- event relationship identifiers disagree with the bundle relationship;
- the first event is not `RelationshipCreated` authored by `tria:system`;
- another `RelationshipCreated` event appears later in history;
- event hashes, chain linkage, or deterministic projection verification fail.

Version values are never coerced. A numeric `0.4` is not treated as the projection version string `"0.4"`.

## Root semantics

Every restorable history has exactly one relationship root. The root establishes that the event stream is a TRIA relationship history rather than an arbitrary collection of individually valid relational events.

A valid hash chain is therefore necessary but not sufficient for portable restoration.

## Import behavior

`import_replay_bundle` performs full verification before writing. Structural failures, invalid roots, unsupported versions, tampering, and projection mismatches fail before the destination event store is mutated.

This build does not add federation, signing, or external authenticity. Hashes and replay verification continue to establish internal integrity and deterministic reconstruction, not independent truth or authorship outside the recorded history.
