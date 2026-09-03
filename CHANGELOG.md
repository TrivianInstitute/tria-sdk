# Changelog

## [0.1.0a3] - 2026-09-03

### Added
- Portable replay bundle export, deterministic projection hashing, and integrity verification.
- Integrity-gated replay import/restore for in-memory and SQLite stores.
- Replay structural validation requiring a non-empty history with exactly one `RelationshipCreated` root.
- Lifecycle enforcement for resting, dormant, dissolving, and dissolved relationships.
- Explicit lifecycle authority and fail-closed lifecycle transition semantics.
- Consent/capability intersection and minimized execution metadata persistence.
- Purpose-bound, time-bounded, and explicitly conditioned consent and permissions.
- Explicit delegation authority and fail-closed ambiguous permission races.
- Governed policy authority and re-consent semantics.
- Governed cross-boundary disclosure, admission, and derivation.
- Pure governance evaluation with explicit audit recording for consequential operations.
- Runtime use of the relationship's injected governance semantics and distinct `PAUSED` / `BLOCKED` resolution states.
- Deep immutability for event payloads and public runtime/provider/governance values.
- Full replay export governed by explicit aggregate `DISCLOSE` authority.
- Explicit compatibility gates for replay bundle format, event schema, and projection version.

### Changed
- Projection timestamps are derived from immutable event timestamps for deterministic replay.
- Replay bundle envelopes must match the schema versions of contained events.
- Replay export now requires `export_replay_bundle(relationship, actor=...)`; anonymous export is intentionally unsupported.
- Projection version is `0.4` for the current alpha surface.
- CI and public package metadata target `0.1.0a3`.

## [0.1.0a2] - 2026-09-03

### Added
- SQLite persistence, JSON event hydration, replay integrity, and chain verification.
- Governed permissions for STORE, READ, DISCLOSE, DERIVE, ACT, and DELEGATE.
- Policy adoption/revocation records and deterministic policy checks.
- Model-agnostic invocation planning and governed context filtering.
- Thin OpenAI Responses-style and Anthropic Messages-style provider translators.
- Caller-owned execution bridge with blocked-plan protection.
- Provider/runtime/execution conformance fixtures and tests.
- Public package version constant.

### Changed
- Hardened packaging configuration for `src/tria` wheel builds.
- Updated README and package metadata to reflect the current alpha surface.

## [0.1.0a1] - 2026-09-03

### Added
- Initial model-agnostic TRIA Core scaffold.
- Immutable relational events with tamper-evident hashes.
- Actor-local sequence and causal-parent fields.
- Deterministic relational-state projection.
- Scoped consent grant/revocation.
- Epistemic claim admission with provenance requirements.
- Preserved disagreement.
- Deterministic governance decisions.
- In-memory event store and core acceptance tests.
- TRIA Core Specification v0.1.1 pre-implementation baseline.
