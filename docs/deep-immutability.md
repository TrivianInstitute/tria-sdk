# Deep immutability

TRIA treats immutability as a data-structure property, not merely a dataclass attribute setting.

## Rule

A frozen public value object must not expose nested mutable containers that can be altered after construction.

The historical Build 024 introduced these protections and the current alpha also freezes RelationalState nested mappings. TRIA therefore deep-freezes the mutable container surfaces carried by:

- relational event proposals and committed relational events;
- runtime invocation requests and results;
- runtime context values and plan sequences;
- provider requests and responses; and
- governance decision metadata.

Nested mappings become read-only mappings, mutable sequences become tuples, and sets become frozensets. Inputs are snapshotted at construction, so later mutation of the caller-owned source object does not alter the TRIA value.

## Event integrity

Event payload immutability is especially important because immutable events are foundational to deterministic replay and audit. A committed event payload cannot be edited in place after its hash has been computed.

The original Build 024 did not change those versions. The current remediation explicitly advances event schema to 0.2 and projection to 0.5; see compatibility.md. Serialization converts frozen containers back to ordinary portable JSON structures.

## Boundary behavior

Applications that need a mutable provider payload must use ProviderRequest.to_transport_payload(), which recursively converts nested frozen containers. A shallow dict copy is insufficient. TRIA itself preserves an immutable snapshot of the authorized request and associated governance values.
