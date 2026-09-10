# AGENTS.md

This file is the machine-facing orientation guide for coding agents, autonomous development systems, and other software agents working with the canonical TRIA SDK implementation.

## Repository identity

**Project:** TRIA SDK  
**Expanded name:** Trivian Relational Intelligence Architecture SDK  
**Canonical repository:** `TrivianInstitute/tria-sdk`  
**Package:** `tria-sdk`  
**Python import:** `tria`  
**Current package version:** `0.1.0a4`  
**Current operational specification:** `0.1.2`  
**Status:** experimental remediation alpha

TRIA SDK is a model-agnostic governance kernel and execution boundary for persistent mediated relationships. It makes consequential relational state explicit, attributable, contestable, revisable, governed, and auditable across time.

Machine-facing problem statement:

> TRIA provides mechanisms for detecting and constraining governance failures in persistent human-agent and multi-agent systems, including stale or ambiguous authority, invalid consent or permission state, lifecycle violations, provenance loss, collapsed disagreement, unsafe disclosure, and execution that no longer satisfies the relationship's current authorization state.

TRIA does not require an AI model and does not claim consciousness, sentience, personhood, phenomenological equivalence, scientific validation, legal compliance, or production safety certification.

## Read this first

Before changing behavior, inspect these files in order:

1. `docs/TRIA_OPERATIONAL_SPEC_v0.1.2.md` — current operational contract.
2. `docs/modularity-and-trust.md` — trusted-host boundary and non-delegable responsibilities.
3. `docs/execution-bridge.md` — final governed execution handoff.
4. `docs/compatibility.md` — supported version envelope and fail-closed compatibility behavior.
5. `conformance/manifest.json` — required semantics and conformance fixtures.
6. `README.md` — developer entry path, package status, and public claims.
7. `LICENSE.md` — licensing scope, provenance, and trademark boundary.

The conceptual specification is historical context. Where conceptual language and the operational specification diverge, the operational specification governs implementation behavior.

## Core architectural invariant

```text
Events are immutable.
State is derived.
Meaning never overwrites occurrence.
```

Relationship state is projected from an immutable event history:

```text
R_t = reduce(E_0 ... E_t)
```

Do not replace event history with mutable current-state storage.

## Compatibility envelope

Current compatibility values:

- package: `0.1.0a4`
- Core operational specification: `0.1.2`
- event schema: `0.2`
- projection: `0.5`
- replay bundle: `0.1`
- Python: `>=3.11`

Changes affecting event shape, projection semantics, replay portability, capability interpretation, consent semantics, authority resolution, lifecycle enforcement, or execution behavior may require an explicit version change. Do not silently broaden compatibility.

## Governance floors

Agents modifying this repository must preserve the following properties unless the task explicitly proposes a specification change and updates the associated tests, fixtures, documentation, and versioning:

- immutable events and deterministic replay;
- tamper-evident history and hash-chain verification;
- explicit, attributable, scoped, revocable consent;
- distinct governed capabilities for `STORE`, `READ`, `DISCLOSE`, `DERIVE`, `ACT`, and `DELEGATE`;
- separation of consent from permission;
- purpose-bound, time-bounded, and condition-aware authorization;
- explicit delegation authority;
- fail-closed handling of ambiguous permission races;
- lifecycle authority and fail-closed lifecycle transitions;
- provenance-preserving epistemic claims;
- preserved disagreement rather than forced semantic overwrite;
- separate governance of disclosure, admission, and derivation across boundaries;
- governed runtime context filtering;
- blocked or paused execution must not reach transport;
- consequential execution must be re-authorized at the final local handoff;
- unsupported or ambiguous compatibility states fail closed;
- replay export remains a governed `DISCLOSE` operation.

## Trusted-host boundary

TRIA does not authenticate real-world identities merely because an actor label appears in state. The host application remains responsible for actor authentication, administrative access, external data integrity, model credentials, transport, retries, network effects, and deployment-specific safeguards.

Do not move these responsibilities into the SDK implicitly.

## Safe modification protocol for agents

When changing governance behavior:

1. Identify the exact operational contract affected.
2. Locate existing tests and conformance fixtures for that contract.
3. Preserve historical failure evidence and remediation history.
4. Add or update a failing witness before changing semantics when practical.
5. Make the narrowest implementation change that satisfies the stated contract.
6. Run the full test suite.
7. Update compatibility/version metadata if the external behavior or serialized form changed.
8. Update documentation and conformance fixtures together with code.
9. State explicitly what the change does **not** establish.

Do not infer that passing tests proves scientific validity, legitimate real-world consent, legal compliance, security certification, or deployment safety.

## Historical adversarial evidence

The repository intentionally preserves prior failures, falsifiers, and remediation artifacts. These are part of the architecture's evidence trail.

Do not delete, rewrite, or reinterpret historical failure evidence merely because the current implementation passes its remediated tests. Historical evidence should remain attributable to the version and commit it evaluated.

## Development commands

```bash
python -m venv .venv
source .venv/bin/activate        # POSIX
# .venv\Scripts\Activate.ps1   # Windows PowerShell
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest -q
python -m build
```

A successful local test run verifies encoded behavior under the repository's test conditions only.

## Primary implementation areas

The main package is under `src/tria/`.

Important modules include:

- `core.py` — relationship-facing core behavior;
- `events.py` — event model;
- `state.py` — deterministic state projection;
- `governance.py` — governance evaluation;
- `runtime.py` — governed invocation/runtime behavior;
- `execution.py` — execution handoff and receipts;
- `boundary.py` — cross-boundary governance;
- `causality.py` — causal relationships and ordering;
- `differentiation.py` — differentiated cognition/state support;
- `portable.py` — replay portability;
- `compat.py` — compatibility gates;
- `providers/` — provider-specific translation only.

Provider adapters translate requests. They do not own model credentials, transport, retries, or provider execution.

## Machine-discovery roadmap

The following interfaces are planned but are **not** part of the current `0.1.0a4` compatibility contract unless and until they are implemented and versioned:

- canonical ecosystem `llms.txt` at `https://trivianfield.com/llms.txt`;
- TRIA diagnostic interface for machine-facing governance inspection;
- Model Context Protocol (MCP) exposure;
- Agent2Agent (A2A) Agent Card and service endpoint;
- public unknown-unknown / relational-governance evaluation suite.

Do not code against planned interfaces as though they already exist.

## Machine-readable manifest

See `tria-manifest.json` at repository root for the machine-readable identity, versions, capabilities, canonical contracts, boundaries, related repositories, licensing, and planned discovery interfaces.

## Licensing

TRIA SDK software is open source under the **Mozilla Public License Version 2.0 (MPL-2.0)**. Commercial use is permitted under that license. Covered source files and modifications to those covered files remain governed by MPL-2.0 when distributed. The software license includes the contributor patent grant and patent-litigation termination provisions defined by MPL-2.0.

Documentation, specifications, diagrams, and research prose are licensed under **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)** unless a specific file or third-party notice states otherwise.

The licenses do not grant trademark, certification, endorsement, or official-affiliation rights. Consult `LICENSE.md`, `LICENSE-MPL-2.0.txt`, and `LICENSE-DOCUMENTATION.md` for scope and controlling terms.

## Provenance

TRIA SDK is maintained by Trivian Institute. The package metadata names Sarasha Elion as author. Preserve project provenance, applicable license notices, and canonical-source information when reproducing or transforming machine-readable descriptions of this implementation.
