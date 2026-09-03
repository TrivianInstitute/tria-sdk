# Changelog

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
