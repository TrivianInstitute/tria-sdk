# TRIA v0.1 Alpha Completion Audit

Status: implementation-complete candidate for the current Python alpha surface.

This audit freezes scope for `0.1.0a3`. It is not a claim of scientific validation, production safety, legal compliance, or protocol standardization.

## Canonical boundary

TRIA Core is a model-agnostic governance kernel for persistent mediated relationships. The relationship is the developer-facing aggregate; immutable events are foundational; state is deterministic materialization; provider concepts remain outside Core.

The current implementation covers:

- immutable event history and deterministic replay;
- consent, capabilities, purpose, expiry, and explicit conditions;
- lifecycle state, lifecycle authority, and transition governance;
- policy authority, adoption, revocation, amendment, and re-consent;
- provenance-bearing epistemic claims and preserved disagreement;
- delegation and fail-closed ambiguous permission races;
- governed cross-boundary disclosure, admission, and derivation;
- pure governance evaluation plus explicit decision auditing;
- model-agnostic Runtime and caller-owned execution;
- thin provider translation adapters;
- deep immutability of public value boundaries;
- portable replay verification/import;
- governed full replay export;
- schemas, compatibility gates, conformance fixtures, packaging, and CI.

## Compatibility envelope

- package: `0.1.0a3`
- event schema: `0.1`
- projection: `0.4`
- replay bundle: `0.1`
- Core specification: `0.1.1`
- Python: 3.11 and 3.12

Changes to event hashing, event schema, projection shape, or replay bundle semantics require an explicit compatibility decision rather than an incidental implementation change.

## Completion criteria

The v0.1 alpha implementation is considered technically complete when:

1. CI passes on supported Python versions.
2. package version, README, changelog, compatibility constants, schemas, and conformance manifest agree;
3. every manifest fixture exists and parses;
4. the built wheel imports and exposes the declared version;
5. the public examples exercise current APIs rather than deprecated call shapes;
6. no known Core invariant remains implemented only as documentation;
7. no provider-specific concept is required by Core;
8. no release or version tag is created before the licensing posture is intentionally confirmed.

## Explicitly out of scope

These are not blockers for v0.1 alpha completion:

- federation or remote synchronization;
- participant-sovereign dual ledgers;
- cryptographic attestation infrastructure;
- cross-language canonical JSON/hash standardization;
- global identity or consensus;
- agent orchestration;
- RAG/vector memory;
- application UX;
- provider SDK ownership;
- streaming transport;
- certification infrastructure;
- metaphysical claims about model experience or personhood.

They may become later repositories, protocol work, or higher-version SDK work. They should not be added to v0.1 merely because they are adjacent possibilities.

## Remaining pre-release decision

The principal non-technical blocker is licensing. `pyproject.toml` currently declares `AGPL-3.0-only`. That declaration should be intentionally reviewed before the first public tag or release. This audit does not change it.

## Release posture

After this audit passes CI, further changes to the current alpha should be treated as one of three things:

- a defect fix against an existing invariant;
- an explicitly versioned compatibility change; or
- post-v0.1 scope.

That boundary is intentional. Completion means the kernel has a coherent stopping point.
