# Deep immutability

TRIA treats immutability as a data-structure property, not merely a dataclass attribute setting.

## Rule

A frozen public value object must not expose nested mutable containers that can be altered after construction.

Build 024 therefore deep-freezes the mutable container surfaces carried by:

- relational event proposals and committed relational events;
- runtime invocation requests and results;
- runtime context values and plan sequences;
- provider requests and responses; and
- governance decision metadata.

Nested mappings become read-only mappings, mutable sequences become tuples, and sets become frozensets. Inputs are snapshotted at construction, so later mutation of the caller-owned source object does not alter the TRIA value.

## Event integrity

Event payload immutability is especially important because immutable events are foundational to deterministic replay and audit. A committed event payload cannot be edited in place after its hash has been computed.

This hardening does **not** change canonical event hash semantics, the event schema version, the projection version, or the replay bundle format. Serialization converts frozen containers back to ordinary portable JSON structures.

## Boundary behavior

Applications that need a mutable provider payload or metadata structure for a caller-owned transport may create a copy at the boundary. TRIA itself preserves an immutable snapshot of the authorized request and associated governance values.
