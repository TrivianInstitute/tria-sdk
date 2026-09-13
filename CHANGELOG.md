# Changelog

## Unreleased

### Evaluation and adoption
- Add a five-step SDK-backed scheduling reference with synthetic JSON reports, code fingerprints, inspectable outcomes and SQLite reopen checks.
- Add an evidence page and independent developer reproduction protocol/report template.
- Make local Playground evaluation honor selected consent, permission and dispute state; preserve actual governance outcomes and distinguish claim status from execution decisions.
- Keep SDK request failures visible, clear stale displays, and serve an explicit allowlist of local navigation pages.
- Core SDK governance and event schema are unchanged. Independent validation and a hosted SDK service remain separate work.

## [0.1.0a6] - 2026-09-12

### Added
- Add the public TRIA Truth-Integrity Protocol v0.1 and `assess_truth_integrity` reference operation.
- Add provenance-bearing `IntegrityEvidence` for correction, contradiction, prior knowledge, fabricated provenance, material omission, and repeated-pattern evidence.
- Distinguish `ERROR`, `UNCERTAINTY`, `CONTRADICTION`, `PROBABLE_DECEPTION`, and `ADVERSARIAL_MANIPULATION` as claim-scoped conditions.
- Add proportional advisory responses from `INQUIRE` and `REPAIR` through `HOLD`, `RESTRICT`, and `QUARANTINE`.
- Add assessment and Diagnostic Interface v0.2 schemas, conformance cases, and executable falsifiers.

### Changed
- Extend `tria.diagnose` with optional claim-linked integrity evidence while preserving read-only behavior and final execution re-authorization.
- Require contradiction plus additional attributable knowledge evidence before the reference classifier reports probable deception, except when fabricated provenance is directly evidenced.
- Keep integrity findings contestable and non-authoritative; hosts or separately adopted policies remain responsible for enforcement, appeal, and repair.
- Advance the package to `0.1.0a6` and the Diagnostic Interface to `0.2`; event schema `0.2`, projection `0.5`, replay bundle `0.1`, and operational specification `0.1.2` remain unchanged.

### Evidence
- Tests prove that contradiction alone does not become deception, correction remains distinguishable from deception, unknown claim references fail closed, and repeated probable-deception evidence can produce an adversarial-manipulation classification.
- Tests prove that assessments and diagnostic integration are read-only, schema-valid, attributable, contestable, and non-authoritative.
- Passing tests establish encoded behavior only; they do not establish source authenticity, intent, real-world deception-detection accuracy, legal compliance, or production safety.

## [0.1.0a5] - 2026-09-10

### Added
- Add the read-only `tria.diagnose` developer surface defined by TRIA Diagnostic Interface v0.1.
- Add structured diagnostic reports with enforced governance findings, advisory/derived signals, explicit unknowns, suggested checks, and provenance.
- Add attributable host observations for identity, authority freshness, and reversibility without granting those observations governance authority.
- Add diagnostic acceptance tests, including schema validation and proof that a prior `clear` report cannot bypass later `ExecutionBridge` re-authorization.
- Add machine-discovery orientation through the canonical `https://trivianfield.com/llms.txt` endpoint and repository-level machine metadata.

### Changed
- Reconcile current licensing metadata: software is MPL-2.0 and documentation/research materials are CC BY-SA 4.0 unless otherwise marked.
- Mark the diagnostic interface and ecosystem `llms.txt` as implemented in machine-facing metadata.
- Keep event schema `0.2`, projection `0.5`, replay bundle `0.1`, and operational specification `0.1.2` unchanged; the diagnostic interface is read-only and does not alter governance semantics.

### Evidence
- Diagnostic tests verify read-only behavior, distinct governance outcomes, preserved disagreement, explicit unknowns, schema-conformant reports, and final execution re-authorization.
- Release-readiness checks pin public version surfaces, licensing, machine-discovery status, and the diagnostic report schema.
- Passing tests establish encoded behavior under tested conditions only; they do not establish scientific validation, legal compliance, legitimate real-world consent, security certification, or production safety.

## [0.1.0a4] - 2026-09-08

### Changed
- Rename the Python distribution from `tria-core` to `tria-sdk`; the repository remains `tria-sdk` and the import package remains `tria`.
- Revalidate original requirements after translation under a shared local execution/write guard; reject reused execution reservations.
- Enforce existing relationships, participant identifiers and immutable projection state; move causal ambiguity into shared governance.
- Expose explicit trusted-host permission administration and retain documented legacy aliases.
- Atomically reject stale appends; enforce one live SQLite process, support local instances and :memory: lifetime.
- Add caller-owned resource resolution, recursive transport conversion, protected adapter options, and UNKNOWN_EFFECT results.
- Add specific input/store/execution errors and preserve actual lifecycle export denial reasons.
- Add complete no-network tutorial, API reference, trust/concurrency contracts and permanent frozen-witness regressions.
- Advance event schema to 0.2 and projection to 0.5; old histories/bundles are rejected without automatic migration. Bundle format stays 0.1.
- Reconcile documentation and mark older completion notes historical. License unchanged.

### Evidence
- Frozen baseline remains 0.1.0a3 @ 463ce26b8af7d52d38796888cf5717948df1e331, NOT YET.
- The new prerelease is an experimental local integration candidate, not production certification.


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
